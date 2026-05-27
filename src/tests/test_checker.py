from __future__ import annotations

import ast
import subprocess
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest
from typing_extensions import TypeVar

from flake8_agents.checker import FlakeAgentsChecker

_T = TypeVar("_T", infer_variance=True)


@dataclass(frozen=True)
class DiagnosticView:
    line_number: int
    code: str


@dataclass(frozen=True)
class FullDiagnosticView:
    line_number: int
    column_number: int
    code: str
    message: str
    checker_name: str


def assert_diagnostics_match(actual: tuple[_T, ...], expected: tuple[_T, ...]) -> None:
    assert Counter(actual) == Counter(expected)


def collect_diagnostics(source: str) -> tuple[DiagnosticView, ...]:
    tree = ast.parse(source)
    checker = FlakeAgentsChecker(
        tree=tree, filename="sample.py", lines=source.splitlines(keepends=True)
    )
    return tuple(
        DiagnosticView(line_number=line_number, code=message.split(maxsplit=1)[0])
        for line_number, _column, message, _checker_type in checker.run()
    )


def collect_full_diagnostics(source: str) -> tuple[FullDiagnosticView, ...]:
    tree = ast.parse(source)
    checker = FlakeAgentsChecker(
        tree=tree, filename="sample.py", lines=source.splitlines(keepends=True)
    )
    return tuple(
        FullDiagnosticView(
            line_number=line_number,
            column_number=column_number,
            code=message.split(maxsplit=1)[0],
            message=message,
            checker_name=checker_type.__name__,
        )
        for line_number, column_number, message, checker_type in checker.run()
    )


def run_flake8(
    tmp_path: Path, source: str, *arguments: str
) -> subprocess.CompletedProcess[str]:
    source_path = tmp_path / "sample.py"
    source_path.write_text(source, encoding="utf-8")
    command = (
        "uv",
        "run",
        "flake8",
        "--isolated",
        "--select",
        "AGT",
        *arguments,
        str(source_path),
    )
    return subprocess.run(
        command,
        cwd=Path(__file__).resolve().parents[2],
        check=False,
        capture_output=True,
        text=True,
    )


def test_checker_reports_all_rule_family_diagnostics() -> None:
    source = (
        "from typing import Any\n"
        "from flake8_agents._version import __version__\n"
        "value: Any = None\n"
        "name = getattr(target, 'name')\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(2, "AGT300"),
            DiagnosticView(3, "AGT105"),
            DiagnosticView(4, "AGT200"),
        ),
    )


def test_flake8_reports_all_rule_family_diagnostics(tmp_path: Path) -> None:
    source = (
        "from typing import Any\n"
        "from flake8_agents._version import __version__\n"
        "value: Any = None\n"
        "name = getattr(target, 'name')\n"
    )

    result = run_flake8(tmp_path, source)

    assert result.returncode == 1
    assert "sample.py:2:1: AGT300" in result.stdout
    assert "sample.py:3:8: AGT105" in result.stdout
    assert "sample.py:4:8: AGT200" in result.stdout


def test_flake8_reports_mixed_diagnostics_by_source_location(tmp_path: Path) -> None:
    source = (
        "from typing import Any\n"
        "first = getattr(target, 'first')\n"
        "value: Any = None\n"
        "namespace = target.__dict__\n"
        "second = namespace['second']\n"
    )

    result = run_flake8(tmp_path, source)

    assert result.returncode == 1
    assert [
        line.split("sample.py:", maxsplit=1)[1] for line in result.stdout.splitlines()
    ] == [
        "2:9: AGT200 avoid dynamic getattr calls",
        "3:8: AGT105 Any must stay local to validated boundaries",
        "4:1: AGT209 avoid aliasing raw __dict__",
        "5:10: AGT210 avoid indexing raw __dict__ aliases",
    ]


def test_flake8_suppresses_anti_pattern_with_noqa(tmp_path: Path) -> None:
    result = run_flake8(tmp_path, "name = getattr(target, 'name')  # noqa: AGT200\n")

    assert result.returncode == 0
    assert result.stdout == ""


def test_flake8_suppresses_anti_pattern_with_configuration(tmp_path: Path) -> None:
    result = run_flake8(
        tmp_path, "name = getattr(target, 'name')\n", "--ignore", "AGT200"
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_checker_reports_mixed_diagnostics() -> None:
    source = (
        "from typing import Any\n"
        "first = getattr(target, 'first')\n"
        "value: Any = None\n"
        "namespace = target.__dict__\n"
        "second = namespace['second']\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(2, "AGT200"),
            DiagnosticView(3, "AGT105"),
            DiagnosticView(4, "AGT209"),
            DiagnosticView(5, "AGT210"),
        ),
    )


def test_checker_preserves_full_diagnostic_contract_after_optimization() -> None:
    source = (
        "def use() -> None:\n"
        "    before = load('before')\n"
        "    from importlib import import_module as load\n"
        "    after = load('after')\n"
    )

    diagnostics = collect_full_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            FullDiagnosticView(
                line_number=4,
                column_number=12,
                code="AGT204",
                message="AGT204 avoid dynamic import_module calls",
                checker_name="AntiPatternChecker",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected_diagnostics"),
    [
        pytest.param(
            "from typing import Any\nvalue: Any = None  # noqa: AGT105\n",
            (DiagnosticView(2, "AGT105"),),
            id="used-exact-code",
        ),
        pytest.param(
            "value: int = 1  # noqa: AGT105\n",
            (DiagnosticView(1, "AGT001"),),
            id="unused-exact-code",
        ),
    ],
)
def test_checker_audits_exact_agt_noqa_suppressions(
    source: str, expected_diagnostics: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected_diagnostics)


def test_checker_reports_only_unused_agt_codes_in_mixed_noqa_list() -> None:
    source = (
        "from typing import Any\nvalue: Any = None  # noqa: PLC0415,AGT105,AGT200\n"
    )

    diagnostics = collect_full_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            FullDiagnosticView(
                line_number=2,
                column_number=19,
                code="AGT001",
                message="AGT001 unused AGT noqa suppression: AGT200",
                checker_name="FlakeAgentsChecker",
            ),
            FullDiagnosticView(
                line_number=2,
                column_number=7,
                code="AGT105",
                message="AGT105 Any must stay local to validated boundaries",
                checker_name="TypeEscapeChecker",
            ),
        ),
    )


@pytest.mark.parametrize(
    ("noqa_code", "expected_diagnostics"),
    [
        pytest.param(
            "AGT1", (DiagnosticView(2, "AGT105"),), id="numeric-family-prefix"
        ),
        pytest.param("AGT10", (DiagnosticView(2, "AGT105"),), id="subfamily-prefix"),
        pytest.param(
            "AGT20",
            (DiagnosticView(2, "AGT001"), DiagnosticView(2, "AGT105")),
            id="unmatched-prefix",
        ),
    ],
)
def test_checker_matches_agt_noqa_codes_using_flake8_prefix_semantics(
    noqa_code: str, expected_diagnostics: tuple[DiagnosticView, ...]
) -> None:
    source = f"from typing import Any\nvalue: Any = None  # noqa: {noqa_code}\n"

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected_diagnostics)


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("value: int = 1  # noqa: AGT1\n", id="numeric-family-prefix"),
        pytest.param(
            "value: int = 1  # noqa: PLC0415,AGT,AGT200\n",
            id="mixed-list-starting-with-ignored-family-prefix",
        ),
    ],
)
def test_checker_reports_unused_numeric_agt_prefix_noqa(source: str) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(1, "AGT001"),))


@pytest.mark.parametrize(
    "source",
    [
        pytest.param("value: int = 1  # noqa: PLC0415\n", id="non-agt-code"),
        pytest.param("value: int = 1  # noqa\n", id="bare-inline-noqa"),
        pytest.param("# flake8: noqa\nvalue: int = 1\n", id="file-level-noqa"),
        pytest.param(
            "value: int = 1  # ordinary comment\n", id="non-noqa-inline-comment"
        ),
        pytest.param("value: int = 1  # noqa: AGT\n", id="full-agt-prefix"),
    ],
)
def test_checker_ignores_noqa_comments_outside_explicit_agt_scope(source: str) -> None:
    diagnostics = collect_diagnostics(source)

    assert diagnostics == ()


def test_checker_ignores_unparseable_noqa_token_stream() -> None:
    checker = FlakeAgentsChecker(
        tree=ast.parse(""), filename="sample.py", lines=["value = (  # noqa: AGT105\n"]
    )

    assert tuple(checker.run()) == ()


def test_flake8_reports_unused_explicit_agt_noqa(tmp_path: Path) -> None:
    result = run_flake8(tmp_path, "value: int = 1  # noqa: AGT105\n")

    assert result.returncode == 1
    assert "sample.py:1:17: AGT001 unused AGT noqa suppression: AGT105" in result.stdout


def test_flake8_keeps_used_explicit_agt_noqa_suppressed(tmp_path: Path) -> None:
    result = run_flake8(
        tmp_path, "from typing import Any\nvalue: Any = None  # noqa: AGT105\n"
    )

    assert result.returncode == 0
    assert result.stdout == ""


@pytest.mark.parametrize(
    ("source", "expected_diagnostics"),
    [
        pytest.param(
            "from typing import Any\nvalue: Any = (  # noqa: AGT105\n    None\n)\n",
            (DiagnosticView(2, "AGT105"),),
            id="used-on-diagnostic-physical-line",
        ),
        pytest.param(
            "value: int = (  # noqa: AGT105\n    1\n)\n",
            (DiagnosticView(1, "AGT001"),),
            id="unused-on-logical-line",
        ),
    ],
)
def test_checker_matches_agt_noqa_against_logical_lines(
    source: str, expected_diagnostics: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected_diagnostics)
