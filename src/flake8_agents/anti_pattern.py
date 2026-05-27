from __future__ import annotations

import ast
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Self, override

from flake8_agents._version_ import __version__  # noqa: AGT300

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

__all__ = ["AntiPatternChecker"]

_DYNAMIC_BUILTIN_CODES: dict[str, DiagnosticCode]
_MONKEYPATCH_NAME = "monkeypatch"
_IMPORTLIB_MODULE = "importlib"
_IMPORT_MODULE_NAME = "import_module"


class DiagnosticCode(StrEnum):
    GETATTR = "AGT200"
    SETATTR = "AGT201"
    VARS = "AGT202"
    DUNDER_IMPORT = "AGT203"
    IMPORT_MODULE = "AGT204"
    ATTRIBUTE_SETATTR = "AGT205"
    DUNDER_SETATTR = "AGT206"
    DUNDER_NEW = "AGT207"
    NAMESPACE_DICT_DIRECT_INDEX = "AGT208"
    NAMESPACE_DICT_ALIAS_ASSIGNMENT = "AGT209"
    NAMESPACE_DICT_ALIAS_INDEX = "AGT210"
    DOTTED_IMPORT_ALIAS = "AGT211"


_MESSAGES: dict[DiagnosticCode, str] = {
    DiagnosticCode.GETATTR: "avoid dynamic getattr calls",
    DiagnosticCode.SETATTR: "avoid dynamic setattr calls",
    DiagnosticCode.VARS: "avoid dynamic vars calls",
    DiagnosticCode.DUNDER_IMPORT: "avoid dynamic __import__ calls",
    DiagnosticCode.IMPORT_MODULE: "avoid dynamic import_module calls",
    DiagnosticCode.ATTRIBUTE_SETATTR: "avoid setattr-style mutation methods",
    DiagnosticCode.DUNDER_SETATTR: "avoid dynamic __setattr__ calls",
    DiagnosticCode.DUNDER_NEW: "avoid direct __new__ calls",
    DiagnosticCode.NAMESPACE_DICT_DIRECT_INDEX: "avoid indexing raw __dict__",
    DiagnosticCode.NAMESPACE_DICT_ALIAS_ASSIGNMENT: "avoid aliasing raw __dict__",
    DiagnosticCode.NAMESPACE_DICT_ALIAS_INDEX: "avoid indexing raw __dict__ aliases",
    DiagnosticCode.DOTTED_IMPORT_ALIAS: "avoid aliasing dotted module imports",
}


_DYNAMIC_BUILTIN_CODES = {
    "getattr": DiagnosticCode.GETATTR,
    "setattr": DiagnosticCode.SETATTR,
    "vars": DiagnosticCode.VARS,
    "__import__": DiagnosticCode.DUNDER_IMPORT,
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
    tree: ast.AST

    @classmethod
    def build(cls, tree: ast.AST) -> Self:
        return cls(tree=tree)


class AntiPatternChecker:
    """Flake8 checker for dynamic Python anti-patterns."""

    name = "flake8-agents-anti-pattern"
    version = __version__

    def __init__(self, tree: ast.AST, filename: str, lines: Sequence[str]) -> None:
        del filename, lines
        self._context = SourceContext.build(tree)

    def run(self) -> Iterator[tuple[int, int, str, type[AntiPatternChecker]]]:
        """Yield flake8-compatible anti-pattern diagnostics for this file."""
        diagnostics = _scan_context(self._context)
        for diagnostic in diagnostics:
            yield (
                diagnostic.line_number,
                diagnostic.column_number,
                diagnostic.message,
                type(self),
            )


def _scan_context(context: SourceContext) -> tuple[Diagnostic, ...]:
    visitor = _AntiPatternVisitor(context)
    visitor.visit(context.tree)
    return tuple(visitor.diagnostics)


class _AntiPatternVisitor(ast.NodeVisitor):
    def __init__(self, context: SourceContext) -> None:
        self._context = context
        self._call_shadow_scopes: deque[set[str]] = deque([set()])
        self._import_module_scopes: deque[set[str]] = deque([
            {f"{_IMPORTLIB_MODULE}.{_IMPORT_MODULE_NAME}"}
        ])
        self._namespace_scopes: deque[dict[str, bool]] = deque([{}])
        self.diagnostics: list[Diagnostic] = []

    @override
    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name.partition(".")[0]
            if alias.name == _IMPORTLIB_MODULE:
                self._unshadow_call(bound_name)
                self._bind_import_module_name(f"{bound_name}.{_IMPORT_MODULE_NAME}")
                self._bind_namespace_name(bound_name, is_alias=False)
            else:
                self._bind_name(bound_name, is_namespace_alias=False)
            if alias.asname is not None and "." in alias.name:
                self._record(node, DiagnosticCode.DOTTED_IMPORT_ALIAS)

    @override
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            bound_name = alias.asname or alias.name
            if node.module == _IMPORTLIB_MODULE and alias.name == _IMPORT_MODULE_NAME:
                self._unshadow_call(bound_name)
                self._bind_import_module_name(bound_name)
                self._bind_namespace_name(bound_name, is_alias=False)
            else:
                self._bind_name(bound_name, is_namespace_alias=False)

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._bind_name(node.name, is_namespace_alias=False)
        self._visit_function_scope(node)

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._bind_name(node.name, is_namespace_alias=False)
        self._visit_function_scope(node)

    @override
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._bind_name(node.name, is_namespace_alias=False)
        self._call_shadow_scopes.append(set())
        self._import_module_scopes.append(set())
        self._namespace_scopes.append({})
        self.generic_visit(node)
        self._namespace_scopes.pop()
        self._import_module_scopes.pop()
        self._call_shadow_scopes.pop()

    @override
    def visit_Assign(self, node: ast.Assign) -> None:
        self.visit(node.value)
        is_namespace_alias = _is_namespace_dictionary(node.value)
        for target in node.targets:
            self.visit(target)
            self._bind_assignment_target(target, is_namespace_alias=is_namespace_alias)
        if is_namespace_alias:
            self._record(node, DiagnosticCode.NAMESPACE_DICT_ALIAS_ASSIGNMENT)

    @override
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        self.visit(node.annotation)
        if node.value is not None:
            self.visit(node.value)
        is_namespace_alias = node.value is not None and _is_namespace_dictionary(
            node.value
        )
        self.visit(node.target)
        self._bind_assignment_target(node.target, is_namespace_alias=is_namespace_alias)
        if is_namespace_alias and isinstance(node.target, ast.Name):
            self._record(node, DiagnosticCode.NAMESPACE_DICT_ALIAS_ASSIGNMENT)

    @override
    def visit_AugAssign(self, node: ast.AugAssign) -> None:
        self.visit(node.value)
        self.visit(node.target)
        self._bind_assignment_target(node.target, is_namespace_alias=False)

    @override
    def visit_For(self, node: ast.For) -> None:
        self.visit(node.iter)
        self._bind_assignment_target(node.target, is_namespace_alias=False)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    @override
    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.visit(node.iter)
        self._bind_assignment_target(node.target, is_namespace_alias=False)
        for statement in node.body:
            self.visit(statement)
        for statement in node.orelse:
            self.visit(statement)

    @override
    def visit_With(self, node: ast.With) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._bind_assignment_target(
                    item.optional_vars, is_namespace_alias=False
                )
        for statement in node.body:
            self.visit(statement)

    @override
    def visit_AsyncWith(self, node: ast.AsyncWith) -> None:
        for item in node.items:
            self.visit(item.context_expr)
            if item.optional_vars is not None:
                self._bind_assignment_target(
                    item.optional_vars, is_namespace_alias=False
                )
        for statement in node.body:
            self.visit(statement)

    @override
    def visit_Call(self, node: ast.Call) -> None:
        category = self._call_category(node)
        if category is not None:
            self._record(node, category)
        self.generic_visit(node)

    @override
    def visit_Subscript(self, node: ast.Subscript) -> None:
        if _is_namespace_dictionary(node.value):
            self._record(node, DiagnosticCode.NAMESPACE_DICT_DIRECT_INDEX)
        elif isinstance(node.value, ast.Name) and self._is_active_namespace_alias(
            node.value.id
        ):
            self._record(node, DiagnosticCode.NAMESPACE_DICT_ALIAS_INDEX)
        self.generic_visit(node)

    def _visit_function_scope(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> None:
        argument_names = set(_iter_argument_names(node.args))
        self._call_shadow_scopes.append(argument_names)
        self._import_module_scopes.append(set())
        self._namespace_scopes.append(dict.fromkeys(argument_names, False))
        for statement in node.body:
            self.visit(statement)
        self._namespace_scopes.pop()
        self._import_module_scopes.pop()
        self._call_shadow_scopes.pop()

    def _call_category(self, node: ast.Call) -> DiagnosticCode | None:
        function = node.func
        if isinstance(function, ast.Name):
            return self._name_call_category(function.id)
        if isinstance(function, ast.Attribute):
            return self._attribute_call_category(function, node)
        return None

    def _name_call_category(self, name: str) -> DiagnosticCode | None:
        if self._is_call_shadowed(name):
            return None
        if self._is_import_module_name(name):
            return DiagnosticCode.IMPORT_MODULE
        return _DYNAMIC_BUILTIN_CODES.get(name)

    def _attribute_call_category(
        self, function: ast.Attribute, node: ast.Call
    ) -> DiagnosticCode | None:
        if _is_shadowed_qualified_name(function, self._call_shadow_scopes):
            return None
        if self._is_import_module_name(_qualified_name(function)):
            return DiagnosticCode.IMPORT_MODULE
        if function.attr == "setattr" and not _is_monkeypatch_setattr(function):
            return DiagnosticCode.ATTRIBUTE_SETATTR
        if function.attr == "__setattr__":
            return DiagnosticCode.DUNDER_SETATTR
        if function.attr == "__new__" and not _is_object_new_call(node):
            return DiagnosticCode.DUNDER_NEW
        return None

    def _bind_assignment_target(
        self, target: ast.expr, *, is_namespace_alias: bool
    ) -> None:
        for name in _stored_names(target):
            self._bind_name(name, is_namespace_alias=is_namespace_alias)

    def _bind_name(self, name: str, *, is_namespace_alias: bool) -> None:
        self._call_shadow_scopes[-1].add(name)
        self._bind_namespace_name(name, is_alias=is_namespace_alias)

    def _unshadow_call(self, name: str) -> None:
        self._call_shadow_scopes[-1].discard(name)

    def _bind_import_module_name(self, name: str) -> None:
        self._import_module_scopes[-1].add(name)

    def _bind_namespace_name(self, name: str, *, is_alias: bool) -> None:
        self._namespace_scopes[-1][name] = is_alias

    def _is_call_shadowed(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self._call_shadow_scopes))

    def _is_import_module_name(self, name: str) -> bool:
        return any(name in scope for scope in reversed(self._import_module_scopes))

    def _is_active_namespace_alias(self, name: str) -> bool:
        for scope in reversed(self._namespace_scopes):
            if name in scope:
                return scope[name]
        return False

    def _record(self, node: ast.expr | ast.stmt, code: DiagnosticCode) -> None:
        self.diagnostics.append(
            Diagnostic(
                line_number=node.lineno, column_number=node.col_offset, code=code
            )
        )


def _is_namespace_dictionary(node: ast.AST) -> bool:
    return isinstance(node, ast.Attribute) and node.attr == "__dict__"


def _is_monkeypatch_setattr(function: ast.Attribute) -> bool:
    return (
        function.attr == "setattr"
        and isinstance(function.value, ast.Name)
        and function.value.id == _MONKEYPATCH_NAME
    )


def _is_object_new_call(node: ast.Call) -> bool:
    return (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "__new__"
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "object"
    )


def _qualified_name(node: ast.Attribute) -> str:
    value = node.value
    if isinstance(value, ast.Name):
        return f"{value.id}.{node.attr}"
    if isinstance(value, ast.Attribute):
        return f"{_qualified_name(value)}.{node.attr}"
    return node.attr


def _is_shadowed_qualified_name(
    node: ast.Attribute, shadow_scopes: Sequence[set[str]]
) -> bool:
    value = node.value
    while isinstance(value, ast.Attribute):
        value = value.value
    if not isinstance(value, ast.Name):
        return False
    return any(value.id in scope for scope in reversed(shadow_scopes))


def _iter_argument_names(arguments: ast.arguments) -> Iterator[str]:
    yield from (arg.arg for arg in arguments.posonlyargs)
    yield from (arg.arg for arg in arguments.args)
    yield from (arg.arg for arg in arguments.kwonlyargs)
    if arguments.vararg is not None:
        yield arguments.vararg.arg
    if arguments.kwarg is not None:
        yield arguments.kwarg.arg


def _stored_names(target: ast.expr) -> frozenset[str]:
    if isinstance(target, ast.Name):
        return frozenset({target.id})
    if isinstance(target, (ast.Tuple, ast.List)):
        names: set[str] = set()
        for element in target.elts:
            names.update(_stored_names(element))
        return frozenset(names)
    return frozenset()
