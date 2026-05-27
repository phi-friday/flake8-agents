from __future__ import annotations

import ast
import re
import tokenize
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, TypeAlias

from typing_extensions import Self, override

from flake8_agents._version_ import __version__  # noqa: AGT300

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

    class _TypeAliasNode(ast.AST):
        value: ast.expr

else:
    _TypeAliasNode = ast.AST

__all__ = ["TypeEscapeChecker"]

_TYPE_IGNORE_RE = re.compile(r"#\s*type:\s*ignore(?:\[[^\]]+\])?")
_PYREFLY_IGNORE_RE = re.compile(r"#\s*pyrefly:\s*ignore")
_PYREFLY_RULE_QUALIFIED_IGNORE_RE = re.compile(
    r"#\s*pyrefly:\s*ignore\s*"
    r"\[[A-Za-z0-9_.-]+(?:\s*,\s*[A-Za-z0-9_.-]+)*\](?=$|\s)"
)

_ANY_NAMES = frozenset({"Any", "typing.Any", "typing_extensions.Any"})
_OBJECT_NAMES = frozenset({"object", "builtins.object"})
_SELF_NAMES = frozenset({"Self", "typing.Self", "typing_extensions.Self"})
_TYPE_ALIAS_MARKER_NAMES = frozenset({"TypeAlias", "typing.TypeAlias"})
_CALLABLE_NAMES = frozenset({"Callable", "collections.abc.Callable", "typing.Callable"})
_LITERAL_NAMES = frozenset({"Literal", "typing.Literal", "typing_extensions.Literal"})
_BROAD_CONTAINER_NAMES = frozenset({
    "Dict",
    "Mapping",
    "MutableMapping",
    "Tuple",
    "collections.abc.Mapping",
    "collections.abc.MutableMapping",
    "dict",
    "tuple",
    "typing.Dict",
    "typing.Mapping",
    "typing.MutableMapping",
    "typing.Tuple",
})
_LEGACY_TYPE_PARAMETER_NAMES = frozenset({
    "ParamSpec",
    "TypeVar",
    "TypeVarTuple",
    "typing.ParamSpec",
    "typing.TypeVar",
    "typing.TypeVarTuple",
    "typing_extensions.ParamSpec",
    "typing_extensions.TypeVar",
    "typing_extensions.TypeVarTuple",
})
_ELLIPSIS_NAMES = frozenset({"...", "Ellipsis"})
_ALLOWED_PROTOCOL_METHODS = frozenset({"__contains__", "__eq__", "__ne__"})
_ALLOWED_DESCRIPTOR_METHODS = frozenset({"__delete__", "__get__", "__set__"})
_ALLOWED_DESCRIPTOR_ARGUMENTS = frozenset({"instance", "owner", "value"})
_CALLABLE_SUBSCRIPT_ARITY = 2
_EQ_ARGUMENT_COUNT = 2


_ImportAliases: TypeAlias = dict[str, str]
_ShadowedNames: TypeAlias = set[str]
_DiagnosticKey: TypeAlias = tuple[int, str]
Flake8Result: TypeAlias = tuple[int, int, str, type["TypeEscapeChecker"]]


class DiagnosticCode(Enum):
    TYPE_SUPPRESSION = "AGT100"
    UNSAFE_CAST = "AGT101"
    BROAD_OBJECT = "AGT102"
    BROAD_KNOWN_SHAPE = "AGT103"
    VAGUE_CALLABLE = "AGT104"
    BROAD_ANY = "AGT105"
    LEGACY_TYPE_PARAMETER = "AGT106"
    SELF_RETURN_TYPING = "AGT107"


_MESSAGES: dict[DiagnosticCode, str] = {
    DiagnosticCode.TYPE_SUPPRESSION: "type suppression must use precise checks",
    DiagnosticCode.UNSAFE_CAST: "typing.cast bypasses validation-based narrowing",
    DiagnosticCode.BROAD_OBJECT: "broad object annotation hides value shape",
    DiagnosticCode.BROAD_KNOWN_SHAPE: "known-shape container must not use object",
    DiagnosticCode.VAGUE_CALLABLE: "callable surface must spell out parameters",
    DiagnosticCode.BROAD_ANY: "Any must stay local to validated boundaries",
    DiagnosticCode.LEGACY_TYPE_PARAMETER: "use PEP 695 type parameter syntax",
    DiagnosticCode.SELF_RETURN_TYPING: "classmethod factory should return Self",
}


@dataclass(frozen=True)
class Diagnostic:
    line_number: int
    column_number: int
    code: DiagnosticCode

    @property
    def message(self) -> str:
        return f"{self.code.value} {_MESSAGES[self.code]}"


@dataclass(frozen=True)
class SourceContext:
    tree: ast.Module
    aliases: _ImportAliases
    module_shadowed_names: frozenset[str]

    @classmethod
    def build(cls, tree: ast.Module) -> Self:
        aliases = _import_aliases(tree)
        module_shadowed_names = frozenset(_shadowed_names_in_statements(tree.body))
        for shadowed_name in module_shadowed_names:
            aliases.pop(shadowed_name, None)
        return cls(
            tree=tree, aliases=aliases, module_shadowed_names=module_shadowed_names
        )


class TypeEscapeChecker:
    """Flake8 checker for strict typing escape hatches."""

    name = "flake8-agents-type-escape"
    version = __version__

    def __init__(self, tree: ast.Module, filename: str, lines: Sequence[str]) -> None:
        del filename
        self._context = SourceContext.build(tree)
        self._lines = lines

    def run(self) -> Iterator[Flake8Result]:
        """Yield flake8-compatible diagnostics for this file."""
        for diagnostic in _scan_context(self._context, self._lines):
            yield (
                diagnostic.line_number,
                diagnostic.column_number,
                diagnostic.message,
                type(self),
            )


def _scan_context(
    context: SourceContext, lines: Sequence[str]
) -> tuple[Diagnostic, ...]:
    diagnostics: dict[_DiagnosticKey, Diagnostic] = {}
    for diagnostic in _suppression_diagnostics(lines):
        _record(diagnostics, diagnostic)
    _TypeEscapeVisitor(context, diagnostics).visit(context.tree)
    return tuple(diagnostics.values())


def _suppression_diagnostics(lines: Sequence[str]) -> Iterable[Diagnostic]:
    line_index = 0

    def readline() -> str:
        nonlocal line_index
        if line_index >= len(lines):
            return ""
        line = lines[line_index]
        line_index += 1
        return line

    try:
        for token in tokenize.generate_tokens(readline):
            if token.type != tokenize.COMMENT:
                continue
            if _comment_violates_policy(token.string):
                yield Diagnostic(
                    line_number=token.start[0],
                    column_number=token.start[1],
                    code=DiagnosticCode.TYPE_SUPPRESSION,
                )
    except tokenize.TokenError:
        return


def _comment_violates_policy(comment: str) -> bool:
    if _TYPE_IGNORE_RE.search(comment):
        return True
    return any(
        _PYREFLY_RULE_QUALIFIED_IGNORE_RE.match(comment, match.start()) is None
        for match in _PYREFLY_IGNORE_RE.finditer(comment)
    )


def _record(
    diagnostics: dict[_DiagnosticKey, Diagnostic], diagnostic: Diagnostic
) -> None:
    diagnostics[(diagnostic.line_number, diagnostic.code.value)] = diagnostic


class _TypeEscapeVisitor(ast.NodeVisitor):
    def __init__(
        self, context: SourceContext, diagnostics: dict[_DiagnosticKey, Diagnostic]
    ) -> None:
        self._context = context
        self._diagnostics = diagnostics
        self._class_stack: deque[str] = deque()
        self._shadowed_name_counts: dict[str, int] = {}
        self._shadowed_scope_stack: deque[tuple[str, ...]] = deque()
        self._push_shadowed_names(context.module_shadowed_names)

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._class_stack.append(node.name)
        self.generic_visit(node)
        self._class_stack.pop()

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._check_function(node)
        self._push_shadowed_names(_shadowed_names_in_function(node))
        self.generic_visit(node)
        self._pop_shadowed_names()

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._check_function(node)
        self._push_shadowed_names(_shadowed_names_in_function(node))
        self.generic_visit(node)
        self._pop_shadowed_names()

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self._add_legacy_type_parameter_violation(
            node, self._legacy_type_parameter_target(node.target, node.value)
        )
        if _is_identity_sentinel_assignment(node):
            self.generic_visit(node)
            return
        if _is_type_alias_marker(node.annotation, self._context.aliases):
            if node.value is not None:
                self._check_annotation(node.value)
        else:
            self._check_annotation(node.annotation)
        self.generic_visit(node)

    @override
    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            self._add_legacy_type_parameter_violation(
                node, self._legacy_type_parameter_target(target, node.value)
            )
        self.generic_visit(node)

    def visit_TypeAlias(self, node: _TypeAliasNode) -> None:  # pragma: no cover
        self._check_annotation(node.value)
        self.generic_visit(node)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        if _is_cast_call(node, self._context.aliases, self._shadowed_name_counts):
            self._add_diagnostic(node, DiagnosticCode.UNSAFE_CAST)
        self.generic_visit(node)

    def _check_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
        for arg in _iter_function_args(node.args):
            if arg.annotation is None:
                continue
            if _is_allowed_object_argument(node, arg, self._class_stack):
                continue
            category = _annotation_violation_category(
                arg.annotation,
                self._context.aliases,
                vague_callable_context=arg is node.args.vararg
                or arg is node.args.kwarg,
            )
            if category is not None:
                self._add_diagnostic(arg.annotation, category)
        if node.returns is not None:
            if _needs_self_return_annotation(
                node, self._class_stack, self._context.aliases
            ):
                self._add_diagnostic(node.returns, DiagnosticCode.SELF_RETURN_TYPING)
            category = _annotation_violation_category(
                node.returns, self._context.aliases
            )
            if category is not None:
                self._add_diagnostic(node.returns, category)

    def _check_annotation(self, annotation: ast.expr) -> None:
        category = _annotation_violation_category(annotation, self._context.aliases)
        if category is not None:
            self._add_diagnostic(annotation, category)

    def _legacy_type_parameter_target(
        self, target: ast.expr, value: ast.expr | None
    ) -> str | None:
        if self._class_stack or not isinstance(target, ast.Name):
            return None
        if value is None or not _is_legacy_type_parameter_call(
            value, self._context.aliases, self._shadowed_name_counts
        ):
            return None
        return target.id

    def _add_legacy_type_parameter_violation(
        self, node: ast.AST, target_name: str | None
    ) -> None:
        if target_name is not None:
            self._add_diagnostic(node, DiagnosticCode.LEGACY_TYPE_PARAMETER)

    def _push_shadowed_names(self, names: Iterable[str]) -> None:
        pushed_names = tuple(names)
        for name in pushed_names:
            self._shadowed_name_counts[name] = (
                self._shadowed_name_counts.get(name, 0) + 1
            )
        self._shadowed_scope_stack.append(pushed_names)

    def _pop_shadowed_names(self) -> None:
        for name in self._shadowed_scope_stack.pop():
            next_count = self._shadowed_name_counts[name] - 1
            if next_count:
                self._shadowed_name_counts[name] = next_count
            else:
                del self._shadowed_name_counts[name]

    def _add_diagnostic(self, node: ast.AST, code: DiagnosticCode) -> None:
        line_number = node.lineno if hasattr(node, "lineno") else 1
        column_number = node.col_offset if hasattr(node, "col_offset") else 0
        _record(
            self._diagnostics,
            Diagnostic(line_number=line_number, column_number=column_number, code=code),
        )


def _import_aliases(tree: ast.Module) -> _ImportAliases:
    aliases: _ImportAliases = {}
    _collect_import_aliases(tree.body, aliases)
    return aliases


def _collect_import_aliases(
    statements: Sequence[ast.stmt], aliases: _ImportAliases
) -> None:
    for statement in statements:
        if isinstance(statement, ast.Import):
            for alias in statement.names:
                if alias.name in {"builtins", "typing", "typing_extensions"}:
                    aliases[alias.asname or alias.name] = alias.name
                if alias.name == "collections.abc":
                    aliases[alias.asname or alias.name] = alias.name
            continue
        if isinstance(statement, ast.ImportFrom) and statement.module in {
            "collections.abc",
            "typing",
            "typing_extensions",
        }:
            for alias in statement.names:
                aliases[alias.asname or alias.name] = f"{statement.module}.{alias.name}"
            continue
        if isinstance(statement, ast.If) and _is_type_checking_guard(
            statement.test, aliases
        ):
            _collect_import_aliases(statement.body, aliases)


def _is_type_checking_guard(test: ast.expr, aliases: _ImportAliases) -> bool:
    return _resolved_annotation_name(test, aliases) in {
        "TYPE_CHECKING",
        "typing.TYPE_CHECKING",
    }


def _annotation_violation_category(
    annotation: ast.expr,
    aliases: _ImportAliases,
    *,
    vague_callable_context: bool = False,
) -> DiagnosticCode | None:
    if vague_callable_context and _contains_broad_dynamic(annotation, aliases):
        return DiagnosticCode.VAGUE_CALLABLE
    if _is_vague_callable(annotation, aliases):
        return DiagnosticCode.VAGUE_CALLABLE
    if _is_broad_known_shape_container(annotation, aliases):
        return DiagnosticCode.BROAD_KNOWN_SHAPE
    if _contains_name(annotation, _ANY_NAMES, aliases):
        return DiagnosticCode.BROAD_ANY
    if _contains_name(annotation, _OBJECT_NAMES, aliases):
        return DiagnosticCode.BROAD_OBJECT
    return None


def _is_vague_callable(annotation: ast.expr, aliases: _ImportAliases) -> bool:
    if not isinstance(annotation, ast.Subscript):
        return False
    if _resolved_annotation_name(annotation.value, aliases) not in _CALLABLE_NAMES:
        return False
    elements = _subscript_elements(annotation.slice)
    if len(elements) != _CALLABLE_SUBSCRIPT_ARITY:
        return False
    return _annotation_name(elements[0]) in _ELLIPSIS_NAMES


def _is_broad_known_shape_container(
    annotation: ast.expr, aliases: _ImportAliases
) -> bool:
    if isinstance(annotation, ast.Subscript):
        base_name = _resolved_annotation_name(annotation.value, aliases)
        if base_name in _BROAD_CONTAINER_NAMES and _contains_name(
            annotation.slice, _OBJECT_NAMES, aliases
        ):
            return True
        return any(
            _is_broad_known_shape_container(element, aliases)
            for element in _subscript_elements(annotation.slice)
        )
    if isinstance(annotation, ast.BinOp) and isinstance(annotation.op, ast.BitOr):
        return _is_broad_known_shape_container(
            annotation.left, aliases
        ) or _is_broad_known_shape_container(annotation.right, aliases)
    return False


def _contains_broad_dynamic(annotation: ast.expr, aliases: _ImportAliases) -> bool:
    return _contains_name(annotation, _ANY_NAMES, aliases) or _contains_name(
        annotation, _OBJECT_NAMES, aliases
    )


def _contains_name(
    annotation: ast.AST | None, names: frozenset[str], aliases: _ImportAliases
) -> bool:
    if annotation is None:
        return False
    if _resolved_annotation_name(annotation, aliases) in names:
        return True
    if _is_literal_annotation(annotation, aliases):
        return False
    parsed_string = _parse_string_annotation(annotation)
    if parsed_string is not None:
        return _contains_name(parsed_string, names, aliases)
    return any(
        _contains_name(child, names, aliases)
        for child in ast.iter_child_nodes(annotation)
    )


def _is_literal_annotation(annotation: ast.AST, aliases: _ImportAliases) -> bool:
    return (
        isinstance(annotation, ast.Subscript)
        and _resolved_annotation_name(annotation.value, aliases) in _LITERAL_NAMES
    )


def _is_type_alias_marker(annotation: ast.expr, aliases: _ImportAliases) -> bool:
    return _resolved_annotation_name(annotation, aliases) in _TYPE_ALIAS_MARKER_NAMES


def _is_identity_sentinel_assignment(node: ast.AnnAssign) -> bool:
    return (
        isinstance(node.value, ast.Call)
        and _resolved_annotation_name(node.annotation, {}) == "object"
        and _resolved_annotation_name(node.value.func, {}) == "object"
    )


def _is_allowed_object_argument(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    arg: ast.arg,
    class_stack: Sequence[str],
) -> bool:
    if _is_standard_eq_other_argument(node, arg, class_stack):
        return True
    if class_stack and node.name in _ALLOWED_DESCRIPTOR_METHODS:
        return arg.arg in _ALLOWED_DESCRIPTOR_ARGUMENTS
    if class_stack and node.name in _ALLOWED_PROTOCOL_METHODS:
        return arg.arg in {"key", "other"}
    if node.name.startswith("is_"):
        return _argument_has_only_opaque_uses(node, arg.arg)
    return False


def _is_standard_eq_other_argument(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    arg: ast.arg,
    class_stack: Sequence[str],
) -> bool:
    if not class_stack or node.name != "__eq__" or arg.arg != "other":
        return False
    if len(node.args.args) < _EQ_ARGUMENT_COUNT or node.args.args[1] is not arg:
        return False
    return (
        _annotation_name(arg.annotation) == "object"
        and _annotation_name(node.returns) == "bool"
    )


def _argument_has_only_opaque_uses(
    function: ast.FunctionDef | ast.AsyncFunctionDef, arg_name: str
) -> bool:
    for node in _walk_without_nested_scopes(function.body):
        if isinstance(node, ast.Attribute) and _is_name(node.value, arg_name):
            return False
        if isinstance(node, ast.Subscript) and _is_name(node.value, arg_name):
            return False
    return True


def _needs_self_return_annotation(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    class_stack: Sequence[str],
    aliases: _ImportAliases,
) -> bool:
    if not class_stack or node.returns is None:
        return False
    if not _is_classmethod(node):
        return False
    if _contains_name(node.returns, _SELF_NAMES, aliases):
        return False
    cls_name = _classmethod_receiver_name(node)
    if cls_name is None:
        return False
    return _returns_classmethod_receiver_instance(node, cls_name)


def _is_classmethod(node: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    return any(
        _annotation_name(decorator) == "classmethod"
        for decorator in node.decorator_list
    )


def _classmethod_receiver_name(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> str | None:
    if not node.args.args:
        return None
    return node.args.args[0].arg


def _returns_classmethod_receiver_instance(
    node: ast.FunctionDef | ast.AsyncFunctionDef, cls_name: str
) -> bool:
    factory_names = _factory_result_names(node.body, cls_name)
    return any(
        _is_receiver_factory_return(return_node.value, cls_name, factory_names)
        for return_node in _return_nodes(node.body)
    )


def _factory_result_names(
    statements: Sequence[ast.stmt], cls_name: str
) -> frozenset[str]:
    names: set[str] = set()
    for statement in _walk_without_nested_scopes(statements):
        if isinstance(statement, ast.Assign) and _is_receiver_call(
            statement.value, cls_name
        ):
            for target in statement.targets:
                names.update(_stored_names(target))
        if isinstance(statement, ast.AnnAssign) and _is_receiver_call(
            statement.value, cls_name
        ):
            names.update(_stored_names(statement.target))
    return frozenset(names)


def _return_nodes(statements: Sequence[ast.stmt]) -> Iterable[ast.Return]:
    for statement in _walk_without_nested_scopes(statements):
        if isinstance(statement, ast.Return):
            yield statement


def _is_receiver_factory_return(
    value: ast.expr | None, cls_name: str, factory_names: frozenset[str]
) -> bool:
    if _is_receiver_call(value, cls_name):
        return True
    return isinstance(value, ast.Name) and value.id in factory_names


def _is_receiver_call(value: ast.expr | None, cls_name: str) -> bool:
    return (
        isinstance(value, ast.Call)
        and isinstance(value.func, ast.Name)
        and value.func.id == cls_name
    )


def _is_cast_call(
    node: ast.Call, aliases: _ImportAliases, shadowed_names: dict[str, int]
) -> bool:
    if isinstance(node.func, ast.Name) and node.func.id in shadowed_names:
        return False
    return _resolved_annotation_name(node.func, aliases) in {
        "typing.cast",
        "typing_extensions.cast",
    }


def _is_legacy_type_parameter_call(
    node: ast.expr, aliases: _ImportAliases, shadowed_names: dict[str, int]
) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Name) and node.func.id in shadowed_names:
        return False
    return _resolved_annotation_name(node.func, aliases) in _LEGACY_TYPE_PARAMETER_NAMES


def _iter_function_args(arguments: ast.arguments) -> Iterable[ast.arg]:
    yield from arguments.posonlyargs
    yield from arguments.args
    if arguments.vararg is not None:
        yield arguments.vararg
    yield from arguments.kwonlyargs
    if arguments.kwarg is not None:
        yield arguments.kwarg


def _shadowed_names_in_statements(statements: Sequence[ast.stmt]) -> _ShadowedNames:
    shadowed_names: _ShadowedNames = set()
    for statement in statements:
        if isinstance(statement, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            shadowed_names.add(statement.name)
            continue
        if isinstance(statement, ast.Assign):
            for target in statement.targets:
                shadowed_names.update(_stored_names(target))
            continue
        if isinstance(statement, ast.AnnAssign):
            shadowed_names.update(_stored_names(statement.target))
    return shadowed_names


def _shadowed_names_in_function(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
) -> _ShadowedNames:
    shadowed_names = {arg.arg for arg in _iter_function_args(node.args)}
    pending: list[ast.AST] = list(node.body)
    while pending:
        descendant = pending.pop()
        if isinstance(
            descendant, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef
        ):
            shadowed_names.add(descendant.name)
            continue
        if isinstance(descendant, ast.Lambda):
            continue
        if isinstance(descendant, ast.Name) and isinstance(descendant.ctx, ast.Store):
            shadowed_names.add(descendant.id)
        pending.extend(ast.iter_child_nodes(descendant))
    return shadowed_names


def _stored_names(target: ast.expr) -> Iterable[str]:
    if isinstance(target, ast.Name):
        yield target.id
        return
    if isinstance(target, ast.Tuple | ast.List):
        for element in target.elts:
            yield from _stored_names(element)


def _walk_without_nested_scopes(statements: Sequence[ast.stmt]) -> Iterable[ast.AST]:
    pending: list[ast.AST] = list(reversed(statements))
    while pending:
        node = pending.pop()
        yield node
        if isinstance(
            node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Lambda
        ):
            continue
        pending.extend(ast.iter_child_nodes(node))


def _parse_string_annotation(annotation: ast.AST) -> ast.expr | None:
    if not isinstance(annotation, ast.Constant) or not isinstance(
        annotation.value, str
    ):
        return None
    try:
        return ast.parse(annotation.value, mode="eval").body
    except SyntaxError:
        return None


def _annotation_name(annotation: ast.expr | ast.AST | None) -> str:
    if isinstance(annotation, ast.Name):
        return annotation.id
    if isinstance(annotation, ast.Attribute):
        parent_name = _annotation_name(annotation.value)
        return f"{parent_name}.{annotation.attr}" if parent_name else annotation.attr
    if isinstance(annotation, ast.Constant) and annotation.value is Ellipsis:
        return "..."
    if (
        isinstance(annotation, ast.Constant)
        and isinstance(annotation.value, str)
        and annotation.value in _ANY_NAMES | _OBJECT_NAMES | _SELF_NAMES
    ):
        return annotation.value
    return ""


def _resolved_annotation_name(
    annotation: ast.expr | ast.AST | None, aliases: _ImportAliases
) -> str:
    return _resolve_name(_annotation_name(annotation), aliases)


def _resolve_name(name: str, aliases: _ImportAliases) -> str:
    if not name:
        return ""
    if name in aliases:
        return aliases[name]
    root, separator, suffix = name.partition(".")
    if not separator or root not in aliases:
        return name
    return f"{aliases[root]}.{suffix}"


def _subscript_elements(annotation: ast.expr) -> tuple[ast.expr, ...]:
    if isinstance(annotation, ast.Tuple):
        return tuple(annotation.elts)
    return (annotation,)


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name
