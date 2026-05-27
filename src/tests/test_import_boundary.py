from __future__ import annotations

import ast
from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest
from typing_extensions import TypeVar

from flake8_agents.import_boundary import ImportBoundaryChecker

if TYPE_CHECKING:
    from collections.abc import Sequence

_T = TypeVar("_T", infer_variance=True)


@dataclass(frozen=True)
class DiagnosticView:
    line_number: int
    code: str


def assert_diagnostics_match(actual: tuple[_T, ...], expected: tuple[_T, ...]) -> None:
    assert Counter(actual) == Counter(expected)


def collect_diagnostics(
    source: str, retired_imports: Sequence[str] = ()
) -> tuple[DiagnosticView, ...]:
    tree = ast.parse(source)
    checker = ImportBoundaryChecker(
        tree=tree,
        filename="sample.py",
        lines=source.splitlines(keepends=True),
        retired_imports=retired_imports,
    )
    return tuple(
        DiagnosticView(line_number=line_number, code=message.split(maxsplit=1)[0])
        for line_number, _column, message, _checker_type in checker.run()
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "import flake8_agents._version\n",
            (DiagnosticView(1, "AGT300"),),
            id="private-module-import",
        ),
        pytest.param(
            "from flake8_agents._version import __version__\n",
            (DiagnosticView(1, "AGT300"),),
            id="private-module-from-import",
        ),
        pytest.param(
            "from flake8_agents.type_escape import _private_helper\n",
            (DiagnosticView(1, "AGT300"),),
            id="private-symbol-from-import",
        ),
    ],
)
def test_checker_reports_private_project_imports(
    source: str, expected: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected)


def test_checker_accepts_dunder_symbols_and_external_private_imports() -> None:
    source = (
        "from flake8_agents.metadata import __version__\n"
        "import external._private\n"
        "from external.module import _private_symbol\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("import flake8_agents.legacy\n", id="exact-import"),
        pytest.param("import flake8_agents.legacy.child\n", id="submodule-import"),
        pytest.param(
            "from flake8_agents.legacy import Thing\n", id="exact-from-import"
        ),
        pytest.param(
            "from flake8_agents.legacy.child import Thing\n", id="submodule-from-import"
        ),
    ],
)
def test_checker_reports_retired_project_imports(source: str) -> None:
    diagnostics = collect_diagnostics(source, retired_imports=("flake8_agents.legacy",))

    assert_diagnostics_match(diagnostics, (DiagnosticView(1, "AGT301"),))


def test_checker_accepts_project_imports_outside_configured_retired_paths() -> None:
    source = (
        "import flake8_agents.current\nfrom flake8_agents.legacy_extra import Thing\n"
    )

    diagnostics = collect_diagnostics(source, retired_imports=("flake8_agents.legacy",))

    assert_diagnostics_match(diagnostics, ())


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            "VALUE = 1\nfrom __future__ import annotations\n",
            (DiagnosticView(2, "AGT302"),),
            id="future-after-declaration",
        ),
        pytest.param(
            "from typing import TYPE_CHECKING\n"
            "if TYPE_CHECKING:\n"
            "    from collections.abc import Sequence\n"
            "import ast\n",
            (DiagnosticView(4, "AGT302"),),
            id="runtime-after-type-checking",
        ),
        pytest.param(
            "__all__ = []\nimport ast\n",
            (DiagnosticView(2, "AGT302"),),
            id="runtime-after-all",
        ),
        pytest.param(
            "VALUE = 1\nif TYPE_CHECKING:\n    from collections.abc import Sequence\n",
            (DiagnosticView(2, "AGT302"),),
            id="type-checking-after-declaration",
        ),
    ],
)
def test_checker_reports_import_section_lifecycle_violations(
    source: str, expected: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected)


def test_checker_accepts_ruff_owned_import_sorting_and_grouping_concerns() -> None:
    source = (
        "import sys\n"
        "import os\n"
        "\n"
        "from flake8_agents.type_escape import TypeEscapeChecker\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


def test_checker_accepts_post_import_declaration_ordering() -> None:
    source = (
        "from __future__ import annotations\n"
        "\n"
        "import ast\n"
        "from typing import TYPE_CHECKING\n"
        "\n"
        "if TYPE_CHECKING:\n"
        "    from collections.abc import Sequence\n"
        "\n"
        '__all__ = ["Example"]\n'
        "\n"
        "class Example:\n"
        "    pass\n"
        "\n"
        "VALUE = 1\n"
        "\n"
        "def build() -> Example:\n"
        "    return Example()\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())
