from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from flake8_agents._version_ import __version__  # noqa: AGT300

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator, Sequence

__all__ = ["ImportBoundaryChecker"]

_PACKAGE_PREFIX = "flake8_agents"
_RETIRED_IMPORTS: frozenset[str] = frozenset()


type Flake8Result = tuple[int, int, str, type[ImportBoundaryChecker]]


class DiagnosticCode(StrEnum):
    PRIVATE_PROJECT_IMPORT = "AGT300"
    RETIRED_PROJECT_IMPORT = "AGT301"
    IMPORT_SECTION_ORDER = "AGT302"


_MESSAGES: dict[DiagnosticCode, str] = {
    DiagnosticCode.PRIVATE_PROJECT_IMPORT: "private project import crosses boundary",
    DiagnosticCode.RETIRED_PROJECT_IMPORT: "retired project import path is unavailable",
    DiagnosticCode.IMPORT_SECTION_ORDER: (
        "module import section must precede declarations"
    ),
}


@dataclass(frozen=True)
class Diagnostic:
    line_number: int
    column_number: int
    code: DiagnosticCode

    @property
    def message(self) -> str:
        return f"{self.code.value} {_MESSAGES[self.code]}"


class ImportBoundaryChecker:
    """Flake8 checker for project import-boundary diagnostics."""

    name = "flake8-agents-import-boundary"
    version = __version__

    def __init__(
        self,
        tree: ast.Module,
        filename: str,
        lines: Sequence[str],
        *,
        retired_imports: Sequence[str] = (),
    ) -> None:
        del filename, lines
        self._tree = tree
        if retired_imports:
            self._retired_imports = frozenset((*_RETIRED_IMPORTS, *retired_imports))
        else:
            self._retired_imports = _RETIRED_IMPORTS

    def run(self) -> Iterator[Flake8Result]:
        """Yield flake8-compatible diagnostics for this file."""
        for diagnostic in _scan_tree(self._tree, self._retired_imports):
            yield (
                diagnostic.line_number,
                diagnostic.column_number,
                diagnostic.message,
                type(self),
            )


def _scan_tree(
    tree: ast.Module, retired_imports: frozenset[str]
) -> tuple[Diagnostic, ...]:
    diagnostics: dict[tuple[int, DiagnosticCode], Diagnostic] = {}
    for diagnostic in _import_boundary_diagnostics(tree, retired_imports):
        _record(diagnostics, diagnostic)
    for diagnostic in _import_section_order_diagnostics(tree):
        _record(diagnostics, diagnostic)
    return tuple(diagnostics.values())


def _record(
    diagnostics: dict[tuple[int, DiagnosticCode], Diagnostic], diagnostic: Diagnostic
) -> None:
    diagnostics[(diagnostic.line_number, diagnostic.code)] = diagnostic


def _import_boundary_diagnostics(
    tree: ast.Module, retired_imports: frozenset[str]
) -> Iterable[Diagnostic]:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            yield from _import_diagnostics(node, retired_imports)
        elif isinstance(node, ast.ImportFrom):
            yield from _from_import_diagnostics(node, retired_imports)


def _import_diagnostics(
    node: ast.Import, retired_imports: frozenset[str]
) -> Iterable[Diagnostic]:
    for alias in node.names:
        module_name = alias.name
        if _is_retired_import(module_name, retired_imports):
            yield Diagnostic(
                line_number=node.lineno,
                column_number=node.col_offset,
                code=DiagnosticCode.RETIRED_PROJECT_IMPORT,
            )
        if _is_project_module(module_name) and _has_private_module_part(module_name):
            yield Diagnostic(
                line_number=node.lineno,
                column_number=node.col_offset,
                code=DiagnosticCode.PRIVATE_PROJECT_IMPORT,
            )


def _from_import_diagnostics(
    node: ast.ImportFrom, retired_imports: frozenset[str]
) -> Iterable[Diagnostic]:
    module_name = node.module
    if module_name is None:
        return
    if _is_retired_import(module_name, retired_imports):
        yield Diagnostic(
            line_number=node.lineno,
            column_number=node.col_offset,
            code=DiagnosticCode.RETIRED_PROJECT_IMPORT,
        )
    if not _is_project_module(module_name):
        return
    if _has_private_module_part(module_name) or any(
        _is_private_name(alias.name) for alias in node.names if alias.name != "*"
    ):
        yield Diagnostic(
            line_number=node.lineno,
            column_number=node.col_offset,
            code=DiagnosticCode.PRIVATE_PROJECT_IMPORT,
        )


def _import_section_order_diagnostics(tree: ast.Module) -> Iterable[Diagnostic]:
    seen_runtime_import = False
    seen_type_checking_block = False
    seen_declaration = False

    for statement in _module_order_statements(tree):
        if _is_future_import(statement):
            if seen_runtime_import or seen_type_checking_block or seen_declaration:
                yield _import_section_order_diagnostic(statement)
            continue
        if _is_runtime_import(statement):
            if seen_type_checking_block or seen_declaration:
                yield _import_section_order_diagnostic(statement)
            seen_runtime_import = True
            continue
        if _is_type_checking_block(statement):
            if seen_declaration:
                yield _import_section_order_diagnostic(statement)
            seen_type_checking_block = True
            continue
        seen_declaration = True


def _import_section_order_diagnostic(statement: ast.stmt) -> Diagnostic:
    return Diagnostic(
        line_number=statement.lineno,
        column_number=statement.col_offset,
        code=DiagnosticCode.IMPORT_SECTION_ORDER,
    )


def _module_order_statements(tree: ast.Module) -> Iterable[ast.stmt]:
    start_index = 1 if ast.get_docstring(tree, clean=False) is not None else 0
    for index, statement in enumerate(tree.body):
        if index >= start_index:
            yield statement


def _is_future_import(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.ImportFrom) and statement.module == "__future__"


def _is_runtime_import(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.Import | ast.ImportFrom) and not _is_future_import(
        statement
    )


def _is_type_checking_block(statement: ast.stmt) -> bool:
    return isinstance(statement, ast.If) and _annotation_name(statement.test) in {
        "TYPE_CHECKING",
        "typing.TYPE_CHECKING",
    }


def _annotation_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        value_name = _annotation_name(node.value)
        if not value_name:
            return node.attr
        return f"{value_name}.{node.attr}"
    return ""


def _is_retired_import(module_name: str, retired_imports: frozenset[str]) -> bool:
    return any(
        module_name == retired_import or module_name.startswith(f"{retired_import}.")
        for retired_import in retired_imports
    )


def _is_project_module(module_name: str) -> bool:
    return module_name == _PACKAGE_PREFIX or module_name.startswith(
        f"{_PACKAGE_PREFIX}."
    )


def _has_private_module_part(module_name: str) -> bool:
    return any(_is_private_name(part) for part in module_name.split("."))


def _is_private_name(name: str) -> bool:
    return name.startswith("_") and not (name.startswith("__") and name.endswith("__"))
