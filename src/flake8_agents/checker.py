from __future__ import annotations

import re
import tokenize
from dataclasses import dataclass
from itertools import chain
from typing import TYPE_CHECKING, TypeAlias

from flake8_agents._version_ import __version__  # noqa: AGT300
from flake8_agents.anti_pattern import AntiPatternChecker
from flake8_agents.import_boundary import ImportBoundaryChecker
from flake8_agents.type_escape import TypeEscapeChecker

if TYPE_CHECKING:
    import ast
    from collections.abc import Iterator, Sequence


__all__ = ["FlakeAgentsChecker"]


_OwnedCheckerType: TypeAlias = type[
    AntiPatternChecker | ImportBoundaryChecker | TypeEscapeChecker
]
Flake8Result: TypeAlias = tuple[
    int, int, str, _OwnedCheckerType | type["FlakeAgentsChecker"]
]

_NOQA_INLINE_RE = re.compile(
    r"# noqa(?::[\s]?(?P<codes>([A-Z]+[0-9]*(?:[,\s]+)?)+))?", re.IGNORECASE
)
_AUDITED_AGT_NOQA_CODE_RE = re.compile(r"AGT[1-9][0-9]*\Z")
_AGT_UNUSED_NOQA_CODE = "AGT001"
_AGT_UNUSED_NOQA_MESSAGE = "unused AGT noqa suppression"


@dataclass(frozen=True)
class _RawDiagnostic:
    line_number: int
    column_number: int
    message: str
    checker_type: _OwnedCheckerType

    @property
    def code(self) -> str:
        return self.message.split(maxsplit=1)[0]

    def to_result(self) -> Flake8Result:
        return (self.line_number, self.column_number, self.message, self.checker_type)


@dataclass(frozen=True)
class _NoqaSuppression:
    line_number: int
    column_number: int
    codes: tuple[str, ...]
    logical_line_numbers: frozenset[int]


class FlakeAgentsChecker:
    """Aggregate flake8 checker for repository AGT diagnostics."""

    name = "flake8-agents"
    version = __version__

    def __init__(self, tree: ast.Module, filename: str, lines: Sequence[str]) -> None:
        self._type_escape_checker = TypeEscapeChecker(
            tree=tree, filename=filename, lines=lines
        )
        self._anti_pattern_checker = AntiPatternChecker(
            tree=tree, filename=filename, lines=lines
        )
        self._import_boundary_checker = ImportBoundaryChecker(
            tree=tree, filename=filename, lines=lines
        )
        self._lines = lines

    def run(self) -> Iterator[Flake8Result]:
        """Yield all flake8-compatible AGT diagnostics for this file."""
        diagnostics = tuple(self._raw_diagnostics())
        for diagnostic in diagnostics:
            yield diagnostic.to_result()
        yield from _unused_noqa_results(diagnostics, self._lines, type(self))

    def _raw_diagnostics(self) -> Iterator[_RawDiagnostic]:
        for line_number, column_number, message, checker_type in chain(
            self._type_escape_checker.run(),
            self._anti_pattern_checker.run(),
            self._import_boundary_checker.run(),
        ):
            yield _RawDiagnostic(
                line_number=line_number,
                column_number=column_number,
                message=message,
                checker_type=checker_type,
            )


def _unused_noqa_results(
    diagnostics: tuple[_RawDiagnostic, ...],
    lines: Sequence[str],
    checker_type: type[FlakeAgentsChecker],
) -> Iterator[Flake8Result]:
    diagnostic_codes_by_line = _diagnostic_codes_by_line(diagnostics)
    for suppression in _explicit_agt_noqa_suppressions(lines):
        unused_codes = tuple(
            code
            for code in suppression.codes
            if not _suppression_matches_any_diagnostic(
                code, suppression.logical_line_numbers, diagnostic_codes_by_line
            )
        )
        if unused_codes:
            yield (
                suppression.line_number,
                suppression.column_number,
                _unused_noqa_message(unused_codes),
                checker_type,
            )


def _diagnostic_codes_by_line(
    diagnostics: tuple[_RawDiagnostic, ...],
) -> dict[int, tuple[str, ...]]:
    codes_by_line: dict[int, list[str]] = {}
    for diagnostic in diagnostics:
        codes_by_line.setdefault(diagnostic.line_number, []).append(diagnostic.code)
    return {line_number: tuple(codes) for line_number, codes in codes_by_line.items()}


def _explicit_agt_noqa_suppressions(
    lines: Sequence[str],
) -> tuple[_NoqaSuppression, ...]:
    logical_lines_by_line = _logical_lines_by_line(lines)
    return tuple(
        suppression
        for token in _tokens_from_lines(lines)
        if token.type == tokenize.COMMENT
        for suppression in _suppression_from_comment(
            token, lines, logical_lines_by_line
        )
    )


def _tokens_from_lines(lines: Sequence[str]) -> tuple[tokenize.TokenInfo, ...]:
    line_index = 0

    def readline() -> str:
        nonlocal line_index
        if line_index >= len(lines):
            return ""
        line = lines[line_index]
        line_index += 1
        return line

    try:
        return tuple(tokenize.generate_tokens(readline))
    except tokenize.TokenError:
        return ()


def _logical_lines_by_line(lines: Sequence[str]) -> dict[int, frozenset[int]]:
    logical_lines: dict[int, frozenset[int]] = {}
    min_line = len(lines) + 2
    max_line = -1
    for token in _tokens_from_lines(lines):
        if token.type in {tokenize.ENDMARKER, tokenize.DEDENT}:
            continue
        min_line = min(min_line, token.start[0])
        max_line = max(max_line, token.end[0])
        if token.type in {tokenize.NL, tokenize.NEWLINE}:
            current_lines = frozenset(range(min_line, max_line + 1))
            for line_number in current_lines:
                logical_lines[line_number] = current_lines
            min_line = len(lines) + 2
            max_line = -1
    return logical_lines


def _suppression_from_comment(
    token: tokenize.TokenInfo,
    lines: Sequence[str],
    logical_lines_by_line: dict[int, frozenset[int]],
) -> tuple[_NoqaSuppression, ...]:
    line_number, column_number = token.start
    if line_number > len(lines):
        return ()
    if not lines[line_number - 1][:column_number].strip():
        return ()
    match = _NOQA_INLINE_RE.search(token.string)
    if match is None:
        return ()
    codes_text = match.groupdict()["codes"]
    if codes_text is None:
        return ()
    codes = tuple(
        code
        for code in re.split(r"[,\s]+", codes_text.upper())
        if _AUDITED_AGT_NOQA_CODE_RE.fullmatch(code) is not None
    )
    if not codes:
        return ()
    return (
        _NoqaSuppression(
            line_number=line_number,
            column_number=column_number + match.start(),
            codes=codes,
            logical_line_numbers=logical_lines_by_line.get(
                line_number, frozenset({line_number})
            ),
        ),
    )


def _suppression_matches_any_diagnostic(
    suppression_code: str,
    logical_line_numbers: frozenset[int],
    diagnostic_codes_by_line: dict[int, tuple[str, ...]],
) -> bool:
    return any(
        diagnostic_code == suppression_code
        or diagnostic_code.startswith(suppression_code)
        for line_number in logical_line_numbers
        for diagnostic_code in diagnostic_codes_by_line.get(line_number, ())
    )


def _unused_noqa_message(unused_codes: tuple[str, ...]) -> str:
    return (
        f"{_AGT_UNUSED_NOQA_CODE} {_AGT_UNUSED_NOQA_MESSAGE}: {', '.join(unused_codes)}"
    )
