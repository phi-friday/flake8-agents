from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass

import pytest
from typing_extensions import TypeVar

from flake8_agents.anti_pattern import AntiPatternChecker

_T = TypeVar("_T", infer_variance=True)


@dataclass(frozen=True)
class DiagnosticView:
    line_number: int
    code: str


def assert_diagnostics_match(actual: tuple[_T, ...], expected: tuple[_T, ...]) -> None:
    assert Counter(actual) == Counter(expected)


def collect_diagnostics(source: str) -> tuple[DiagnosticView, ...]:
    tree = ast.parse(source)
    checker = AntiPatternChecker(
        tree=tree, filename="sample.py", lines=source.splitlines(keepends=True)
    )
    return tuple(
        DiagnosticView(line_number=line_number, code=message.split(maxsplit=1)[0])
        for line_number, _column, message, _checker_type in checker.run()
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "value = getattr(target, 'name')\n",
            (DiagnosticView(1, "AGT200"),),
            id="getattr",
        ),
        pytest.param(
            "setattr(target, 'name', value)\n",
            (DiagnosticView(1, "AGT201"),),
            id="setattr",
        ),
        pytest.param(
            "namespace = vars(target)\n", (DiagnosticView(1, "AGT202"),), id="vars"
        ),
        pytest.param(
            "module = __import__('package')\n",
            (DiagnosticView(1, "AGT203"),),
            id="dunder-import",
        ),
        pytest.param(
            "import importlib\nmodule = importlib.import_module('package')\n",
            (DiagnosticView(2, "AGT204"),),
            id="importlib-import-module",
        ),
        pytest.param(
            "target.setattr('name', value)\n",
            (DiagnosticView(1, "AGT205"),),
            id="attribute-setattr",
        ),
        pytest.param(
            "target.__setattr__('name', value)\n",
            (DiagnosticView(1, "AGT206"),),
            id="dunder-setattr",
        ),
        pytest.param(
            "instance = Target.__new__(Target)\n",
            (DiagnosticView(1, "AGT207"),),
            id="dunder-new",
        ),
        pytest.param(
            "value = target.__dict__['name']\n",
            (DiagnosticView(1, "AGT208"),),
            id="direct-namespace-index",
        ),
        pytest.param(
            "target.__dict__['name'] = value\n",
            (DiagnosticView(1, "AGT208"),),
            id="direct-namespace-index-store",
        ),
        pytest.param(
            "namespace = target.__dict__\n",
            (DiagnosticView(1, "AGT209"),),
            id="namespace-alias-assignment",
        ),
        pytest.param(
            "namespace: dict[str, int] = target.__dict__\n",
            (DiagnosticView(1, "AGT209"),),
            id="annotated-namespace-alias-assignment",
        ),
        pytest.param(
            "namespace = target.__dict__\nvalue = namespace['name']\n",
            (DiagnosticView(1, "AGT209"), DiagnosticView(2, "AGT210")),
            id="namespace-alias-index",
        ),
        pytest.param(
            "namespace = target.__dict__\nnamespace['name'] = value\n",
            (DiagnosticView(1, "AGT209"), DiagnosticView(2, "AGT210")),
            id="namespace-alias-index-store",
        ),
        pytest.param(
            "import package.module as alias\n",
            (DiagnosticView(1, "AGT211"),),
            id="dotted-import-alias",
        ),
    ],
)
def test_checker_reports_rejected_anti_pattern_patterns(
    source: str, expected: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected)


def test_checker_reports_import_module_aliases() -> None:
    source = (
        "import importlib as il\n"
        "from importlib import import_module as load\n"
        "first = importlib.import_module('first')\n"
        "second = il.import_module('second')\n"
        "third = load('third')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(3, "AGT204"),
            DiagnosticView(4, "AGT204"),
            DiagnosticView(5, "AGT204"),
        ),
    )


def test_checker_uses_import_module_aliases_after_they_are_bound() -> None:
    source = (
        "before = load('before')\n"
        "from importlib import import_module as load\n"
        "after = load('after')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(3, "AGT204"),))


def test_checker_accepts_import_module_alias_calls_after_shadowing() -> None:
    source = (
        "from importlib import import_module as load\n"
        "first = load('first')\n"
        "load = factory\n"
        "second = load('second')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(2, "AGT204"),))


def test_checker_accepts_documented_exceptions_and_shadowed_names() -> None:
    source = (
        "import sqlalchemy as sa\n"
        "import sqlalchemy.orm\n"
        "from sqlalchemy import orm as test\n"
        "def getattr(value: str) -> str:\n"
        "    return value\n"
        "def setattr(value: str) -> str:\n"
        "    return value\n"
        "def vars(value: str) -> dict[str, str]:\n"
        "    return {}\n"
        "def __import__(value: str) -> str:\n"
        "    return value\n"
        "def import_module(value: str) -> str:\n"
        "    return value\n"
        "getattr('name')\n"
        "setattr('name')\n"
        "vars('name')\n"
        "__import__('name')\n"
        "import_module('name')\n"
        "monkeypatch.setattr(module, 'NAME', value)\n"
        "instance = object.__new__(Target)\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


def test_checker_tracks_namespace_aliases_across_active_scopes() -> None:
    source = (
        "namespace = target.__dict__\n"
        "def inner() -> object:\n"
        "    return namespace['name']\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics, (DiagnosticView(1, "AGT209"), DiagnosticView(3, "AGT210"))
    )


def test_checker_accepts_shadowing_in_async_and_class_scopes() -> None:
    source = (
        "async def async_safe(getattr: object) -> None:\n"
        "    getattr('name')\n"
        "class Safe:\n"
        "    def vars(self, value: str) -> dict[str, str]:\n"
        "        return {}\n"
        "    value = vars('name')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


def test_checker_treats_rebound_namespace_names_as_non_aliases() -> None:
    source = (
        "namespace = target.__dict__\n"
        "namespace += other\n"
        "namespace['name']\n"
        "for namespace in items:\n"
        "    namespace['name']\n"
        "else:\n"
        "    getattr(target, 'name')\n"
        "with manager as namespace:\n"
        "    namespace['name']\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics, (DiagnosticView(1, "AGT209"), DiagnosticView(7, "AGT200"))
    )


def test_checker_treats_async_rebound_namespace_names_as_non_aliases() -> None:
    source = (
        "namespace = target.__dict__\n"
        "async def inner() -> None:\n"
        "    async for namespace in items:\n"
        "        namespace['name']\n"
        "    else:\n"
        "        getattr(target, 'name')\n"
        "    async with manager as namespace:\n"
        "        namespace['name']\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics, (DiagnosticView(1, "AGT209"), DiagnosticView(6, "AGT200"))
    )


def test_checker_accepts_shadowed_qualified_import_module_calls() -> None:
    source = (
        "import importlib\n"
        "def safe(importlib: object) -> None:\n"
        "    importlib.import_module('package')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


def test_checker_accepts_unknown_dynamic_call_shapes() -> None:
    source = (
        "(factory())()\n"
        "package.importlib.import_module('package')\n"
        "(factory()).import_module('package')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


def test_checker_accepts_variadic_shadowed_builtin_names() -> None:
    source = (
        "def safe(*getattr: object, **vars: object) -> None:\n"
        "    getattr('name')\n"
        "    vars('name')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


def test_checker_accepts_destructuring_shadowed_builtin_names() -> None:
    source = (
        "(getattr, other) = pair\n"
        "[vars, another] = other_pair\n"
        "getattr('name')\n"
        "vars('name')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())
