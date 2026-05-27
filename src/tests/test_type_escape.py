from __future__ import annotations

import ast
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest
import tomlkit
from typing_extensions import TypeVar

from flake8_agents.type_escape import TypeEscapeChecker

_T = TypeVar("_T", infer_variance=True)


@dataclass(frozen=True)
class DiagnosticView:
    line_number: int
    code: str


def assert_diagnostics_match(actual: tuple[_T, ...], expected: tuple[_T, ...]) -> None:
    assert Counter(actual) == Counter(expected)


def collect_diagnostics(source: str) -> tuple[DiagnosticView, ...]:
    tree = ast.parse(source)
    checker = TypeEscapeChecker(
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
            "value = 1  # type: ignore[assignment]\n",
            (DiagnosticView(1, "AGT100"),),
            id="type-ignore",
        ),
        pytest.param(
            "value = 1  # pyrefly: ignore\n",
            (DiagnosticView(1, "AGT100"),),
            id="bare-pyrefly-ignore",
        ),
        pytest.param(
            "from typing import cast\nresult = cast(int, value)\n",
            (DiagnosticView(2, "AGT101"),),
            id="unsafe-cast",
        ),
        pytest.param(
            "def handle(value: object) -> None:\n    return None\n",
            (DiagnosticView(1, "AGT102"),),
            id="broad-object",
        ),
        pytest.param(
            "payload: dict[str, object]\n",
            (DiagnosticView(1, "AGT103"),),
            id="broad-known-shape-container",
        ),
        pytest.param(
            "from typing import Callable\ncallback: Callable[..., int]\n",
            (DiagnosticView(2, "AGT104"),),
            id="callable-ellipsis",
        ),
        pytest.param(
            (
                "from typing import Any\n"
                "def handle(value: Any) -> None:\n"
                "    return None\n"
            ),
            (DiagnosticView(2, "AGT105"),),
            id="broad-any",
        ),
        pytest.param(
            'from typing import TypeVar\nT = TypeVar("T")\n',
            (DiagnosticView(2, "AGT106"),),
            id="legacy-type-var",
        ),
        pytest.param(
            (
                "class Box:\n"
                "    @classmethod\n"
                '    def build(cls) -> "Box":\n'
                "        return cls()\n"
            ),
            (DiagnosticView(3, "AGT107"),),
            id="self-return-typing",
        ),
    ],
)
def test_checker_reports_rejected_type_escape_patterns(
    source: str, expected: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected)


def test_checker_resolves_aliases_and_ignores_shadowed_names() -> None:
    source = (
        "import typing as t\n"
        "from collections.abc import Callable as AbcCallable\n"
        "from typing import cast\n"
        "def bad(payload: t.Mapping[str, object]) -> AbcCallable[..., int]:\n"
        "    return cast(AbcCallable[..., int], lambda value: 1)\n"
        "def safe(cast: str, object: str, Any: str) -> None:\n"
        "    cast.upper()\n"
        "    object.upper()\n"
        "    Any.upper()\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(4, "AGT104"),
            DiagnosticView(4, "AGT103"),
            DiagnosticView(5, "AGT101"),
        ),
    )


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param(
            (
                "from typing import Literal\n"
                'mode: Literal["array", "object"]\n'
                'dynamic_name: Literal["Any"]\n'
                'qualified_dynamic_name: Literal["typing.Any"]\n'
                'container_name: Literal["list[object]"]\n'
            ),
            (),
            id="imported-literal-value-members",
        ),
        pytest.param(
            (
                "import typing as t\n"
                "import typing_extensions as te\n"
                "from typing import Literal as L\n"
                "from typing_extensions import Literal as ExtLiteral\n"
                'direct_alias: L["object"]\n'
                'qualified_typing: t.Literal["Any"]\n'
                'qualified_extensions: te.Literal["typing.Any"]\n'
                'extensions_alias: ExtLiteral["list[object]"]\n'
            ),
            (),
            id="qualified-and-aliased-literal-value-members",
        ),
        pytest.param(
            (
                "from typing import Literal\n"
                'def quoted(value: "object") -> None:\n'
                "    return None\n"
                'value: Literal["object"] | object\n'
            ),
            (DiagnosticView(2, "AGT102"), DiagnosticView(4, "AGT102")),
            id="broad-annotations-outside-literal-value-position",
        ),
    ],
)
def test_checker_treats_literal_members_as_values(
    source: str, expected: tuple[DiagnosticView, ...]
) -> None:
    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, expected)


def test_checker_ignores_nested_scope_shadowing_for_outer_cast_calls() -> None:
    source = (
        "from typing import Any, cast\n"
        "def outer(value: int) -> None:\n"
        "    def function_shadow() -> None:\n"
        "        cast = str\n"
        "    class ClassShadow:\n"
        "        cast = str\n"
        "    lambda_shadow = lambda: (cast := str)\n"
        "    cast(Any, value)\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(8, "AGT101"),))


def test_checker_preserves_outer_shadowing_after_nested_scope_exit() -> None:
    source = (
        "from typing import Any, cast\n"
        "def outer(cast: str, value: Any) -> None:\n"
        "    def inner(cast: int) -> None:\n"
        "        cast.bit_length()\n"
        "    cast.upper()\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(2, "AGT105"),))


def test_checker_accepts_standard_exceptions() -> None:
    source = (
        "from typing import Self\n"
        "sentinel: object = object()\n"
        "class Comparable:\n"
        "    def __eq__(self, other: object) -> bool:\n"
        "        return self is other\n"
        "class Descriptor:\n"
        '    def __get__(self, instance: object, owner: object) -> "Descriptor":\n'
        "        return self\n"
        "def is_present(value: object) -> bool:\n"
        "    return value is not None\n"
        "class Box:\n"
        "    @classmethod\n"
        "    def build(cls) -> Self:\n"
        "        return cls()\n"
        "value = 1  # pyrefly: ignore[missing-import]\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, ())


@pytest.mark.skipif(
    sys.version_info < (3, 12),
    reason="PEP 695 type statements are available only on Python 3.12 and newer",
)
def test_checker_inspects_type_aliases_and_variadic_surfaces() -> None:
    source = (
        "from typing import Any, TypeAlias\n"
        "type Payload = dict[str, object]\n"
        "LegacyPayload: TypeAlias = Any\n"
        "def collect(*args: object, **kwargs: Any) -> None:\n"
        "    return None\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(2, "AGT103"),
            DiagnosticView(3, "AGT105"),
            DiagnosticView(4, "AGT104"),
        ),
    )


def test_checker_covers_alias_and_shadowing_edges() -> None:
    source = (
        "import builtins\n"
        "import collections.abc as cabc\n"
        "import typing_extensions as te\n"
        "from typing import TYPE_CHECKING, TypeVar\n"
        "if TYPE_CHECKING:\n"
        "    from typing import Any as HiddenAny\n"
        "async def async_bad(value: te.Any) -> cabc.Callable[..., int]:\n"
        "    return lambda item: 1\n"
        "def union_payload(value: list[dict[str, builtins.object] | int]) -> None:\n"
        "    return None\n"
        "TypeVar = str\n"
        'T = TypeVar("T")\n'
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(7, "AGT104"),
            DiagnosticView(7, "AGT105"),
            DiagnosticView(9, "AGT103"),
        ),
    )


def test_checker_covers_protocol_rejections_and_stored_factory_returns() -> None:
    source = (
        "class Bag:\n"
        "    def __contains__(self, key: object) -> bool:\n"
        "        return False\n"
        "def is_indexed(value: object) -> bool:\n"
        '    return value["key"] is not None\n'
        "class Box:\n"
        "    @classmethod\n"
        '    def assigned(cls) -> "Box":\n'
        "        result = cls()\n"
        "        return result\n"
        "    @classmethod\n"
        '    def annotated(cls) -> "Box":\n'
        '        result: "Box" = cls()\n'
        "        return result\n"
        "    @classmethod\n"
        '    def no_receiver() -> "Box":\n'
        "        return Box()\n"
        'value: "[" = None\n'
        "items = (1, 2)\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(4, "AGT102"),
            DiagnosticView(8, "AGT107"),
            DiagnosticView(12, "AGT107"),
        ),
    )


def test_checker_covers_remaining_branch_behaviors() -> None:
    source = (
        "from typing import Callable\n"
        "callback: Callable[[int]]\n"
        'def quoted(value: "object") -> None:\n'
        "    return None\n"
        "class OddComparable:\n"
        "    def __eq__(self, first: object, other: object) -> bool:\n"
        "        return False\n"
        "def is_attr(value: object) -> bool:\n"
        "    return value.ready\n"
        "def is_nested(value: object) -> bool:\n"
        "    def inner() -> bool:\n"
        "        return value.ready\n"
        "    return True\n"
        "(left, right) = (1, 2)\n"
        "def unannotated(value):\n"
        "    return None\n"
        "target[0] = 1\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(
        diagnostics,
        (
            DiagnosticView(3, "AGT102"),
            DiagnosticView(6, "AGT102"),
            DiagnosticView(8, "AGT102"),
        ),
    )


def test_checker_reports_type_alias_marker_values() -> None:
    source = "from typing import Any, TypeAlias\nLegacyPayload: TypeAlias = Any\n"

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(2, "AGT105"),))


def test_checker_reports_variadic_dynamic_types_as_vague_callable() -> None:
    source = (
        "from typing import Any\n"
        "def collect(*args: object, **kwargs: Any) -> None:\n"
        "    return None\n"
    )

    diagnostics = collect_diagnostics(source)

    assert_diagnostics_match(diagnostics, (DiagnosticView(2, "AGT104"),))


def test_pyproject_registers_agt_entry_point() -> None:
    project = tomlkit.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    entry_points = project["project"]["entry-points"]["flake8.extension"]

    assert entry_points == {"AGT": "flake8_agents.checker:FlakeAgentsChecker"}


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


def test_flake8_reports_agt_diagnostics_through_installed_plugin(
    tmp_path: Path,
) -> None:
    result = run_flake8(tmp_path, "from typing import Any\nvalue: Any = None\n")

    assert result.returncode == 1
    assert "sample.py:2:8: AGT105" in result.stdout


@pytest.mark.parametrize(
    "arguments",
    [
        pytest.param(("--ignore", "AGT105"), id="configured-ignore"),
        pytest.param(("--per-file-ignores", "sample.py:AGT105"), id="per-file-ignore"),
    ],
)
def test_flake8_standard_configuration_suppresses_diagnostics(
    tmp_path: Path, arguments: tuple[str, ...]
) -> None:
    result = run_flake8(
        tmp_path, "from typing import Any\nvalue: Any = None\n", *arguments
    )

    assert result.returncode == 0
    assert result.stdout == ""


def test_flake8_noqa_suppresses_without_reason_comment(tmp_path: Path) -> None:
    source = "from typing import Any\nvalue: Any = None  # noqa: AGT105\n"

    result = run_flake8(tmp_path, source)

    assert result.returncode == 0
    assert result.stdout == ""


def test_flake8_does_not_require_agt_guard_allow_comments(tmp_path: Path) -> None:
    source = (
        "from typing import Any\n"
        "value: Any = None  # noqa: AGT105\n"
        "other: Any = None  # guard: allow type-escape/broad-any\n"
    )

    result = run_flake8(tmp_path, source)

    assert result.returncode == 1
    assert "sample.py:3:8: AGT105" in result.stdout
    assert "because" not in result.stdout
