from __future__ import annotations

import argparse
import asyncio
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, NoReturn

from typing_extensions import override

if TYPE_CHECKING:
    from collections.abc import Coroutine, Sequence

__all__ = ["FindingLevel", "ModuleSizeFinding", "main", "scan_paths"]

_DEFAULT_ERROR_LINES = 1_000
_DEFAULT_WARN_LINES = 800
_LINE_COUNT_CHUNK_SIZE = 1024 * 1024
_LINE_COUNT_WORKERS = 10
_NEWLINE_BYTE = 10
_SUCCESS_EXIT_CODE = 0
_FINDING_FAILURE_EXIT_CODE = 1
_EMPTY_EXCLUDE_PATTERNS: tuple[str, ...] = ()
_EMPTY_EXCLUDE_REGEXES: tuple[re.Pattern[str], ...] = ()


class FindingLevel(Enum):
    """Severity levels for module-size findings."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class ModuleSizeFinding:
    """Single module-size CLI finding."""

    path: Path
    line_count: int
    level: FindingLevel
    threshold: int


@dataclass(frozen=True)
class _Thresholds:
    warn_lines: int
    error_lines: int


class _ParsedArguments(argparse.Namespace):
    paths: list[Path]
    warn_lines: int
    error_lines: int
    exclude_patterns: Sequence[str]
    suppress_warnings: bool


class _ModuleSizeCliError(ValueError):
    """Invalid user input or unrecoverable scan failure."""


class _ModuleSizeParser(argparse.ArgumentParser):
    @override
    def error(self, message: str) -> NoReturn:
        super().error(message)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the module-size CLI."""
    parser = _build_parser()
    arguments = parser.parse_args(argv, namespace=_ParsedArguments())
    thresholds = _validate_thresholds(
        arguments.warn_lines, arguments.error_lines, parser
    )
    try:
        exclude_regexes = _compile_exclude_patterns(arguments.exclude_patterns)
        findings = asyncio.run(
            _scan_cli_paths(tuple(arguments.paths), thresholds, exclude_regexes)
        )
    except _ModuleSizeCliError as error:
        parser.error(str(error))

    rendered_findings = findings
    if arguments.suppress_warnings:
        rendered_findings = tuple(
            finding for finding in findings if finding.level is not FindingLevel.WARNING
        )
    if rendered_findings:
        sys.stdout.write(_render_findings(rendered_findings))
    if any(finding.level is FindingLevel.ERROR for finding in findings):
        return _FINDING_FAILURE_EXIT_CODE
    return _SUCCESS_EXIT_CODE


async def scan_paths(
    paths: Sequence[Path],
    *,
    warn_lines: int = _DEFAULT_WARN_LINES,
    error_lines: int = _DEFAULT_ERROR_LINES,
    exclude_patterns: Sequence[str] = _EMPTY_EXCLUDE_PATTERNS,
) -> tuple[ModuleSizeFinding, ...]:
    """Scan explicit paths asynchronously and return module-size findings."""
    thresholds = _Thresholds(warn_lines=warn_lines, error_lines=error_lines)
    exclude_regexes = _compile_exclude_patterns(exclude_patterns)
    return await _scan_cli_paths(paths, thresholds, exclude_regexes)


async def _scan_cli_paths(
    paths: Sequence[Path],
    thresholds: _Thresholds,
    exclude_regexes: Sequence[re.Pattern[str]] = _EMPTY_EXCLUDE_REGEXES,
) -> tuple[ModuleSizeFinding, ...]:
    scanned_paths = await _resolve_scannable_python_files(paths)
    included_paths = _filter_excluded_paths(scanned_paths, exclude_regexes)
    line_counts = await _line_counts_for_files(included_paths)
    findings = tuple(
        finding
        for path in included_paths
        if (finding := _finding_for_line_count(path, line_counts[path], thresholds))
        is not None
    )
    return tuple(sorted(findings, key=lambda finding: finding.path))


def _build_parser() -> _ModuleSizeParser:
    parser = _ModuleSizeParser(
        prog="module-size", description="Check Python module physical line counts."
    )
    parser.add_argument(
        "paths", nargs="+", type=Path, help="Python files or directories to scan."
    )
    parser.add_argument(
        "--warn-lines",
        type=_positive_int,
        default=_DEFAULT_WARN_LINES,
        help="Report a warning at this physical line count or above.",
    )
    parser.add_argument(
        "--error-lines",
        type=_positive_int,
        default=_DEFAULT_ERROR_LINES,
        help="Report an error at this physical line count or above.",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        default=[],
        dest="exclude_patterns",
        metavar="REGEX",
        help="Skip files whose resolved path matches this regular expression.",
    )
    parser.add_argument(
        "--suppress-warnings",
        action="store_true",
        help="Omit warning findings from stdout output.",
    )
    return parser


def _positive_int(value: str) -> int:
    try:
        parsed_value = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed_value <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed_value


def _validate_thresholds(
    warn_lines: int, error_lines: int, parser: argparse.ArgumentParser
) -> _Thresholds:
    if warn_lines >= error_lines:
        parser.error("--warn-lines must be less than --error-lines")
    return _Thresholds(warn_lines=warn_lines, error_lines=error_lines)


def _compile_exclude_patterns(patterns: Sequence[str]) -> tuple[re.Pattern[str], ...]:
    if not patterns:
        return _EMPTY_EXCLUDE_REGEXES
    compiled_patterns: list[re.Pattern[str]] = []
    for pattern in patterns:
        try:
            compiled_patterns.append(re.compile(pattern))
        except re.error as error:  # noqa: PERF203
            message = f"invalid exclude regex: {pattern}: {error}"
            raise _ModuleSizeCliError(message) from error
    return tuple(compiled_patterns)


def _filter_excluded_paths(
    paths: Sequence[Path], exclude_regexes: Sequence[re.Pattern[str]]
) -> Sequence[Path]:
    if not exclude_regexes:
        return paths
    return tuple(
        path for path in paths if not _path_matches_any_exclude(path, exclude_regexes)
    )


def _path_matches_any_exclude(
    path: Path, exclude_regexes: Sequence[re.Pattern[str]]
) -> bool:
    path_text = path.as_posix()
    return any(exclude_regex.search(path_text) for exclude_regex in exclude_regexes)


async def _resolve_scannable_python_files(paths: Sequence[Path]) -> tuple[Path, ...]:
    resolved_paths: set[Path] = set()
    for path in paths:
        resolved_path = await asyncio.to_thread(path.resolve, strict=False)
        if not await asyncio.to_thread(resolved_path.exists):
            message = f"path does not exist: {path}"
            raise _ModuleSizeCliError(message)
        if await asyncio.to_thread(resolved_path.is_file):
            resolved_paths.add(_resolve_python_file(resolved_path, path))
            continue
        if await asyncio.to_thread(resolved_path.is_dir):
            resolved_paths.update(await _expand_directory(resolved_path))
            continue
        message = f"path is not a file or directory: {path}"
        raise _ModuleSizeCliError(message)
    return tuple(sorted(resolved_paths))


def _resolve_python_file(resolved_path: Path, original_path: Path) -> Path:
    if resolved_path.suffix != ".py":
        message = f"path is not a Python file: {original_path}"
        raise _ModuleSizeCliError(message)
    return resolved_path


async def _expand_directory(directory: Path) -> tuple[Path, ...]:
    git_paths = await _expand_git_directory(directory)
    if git_paths is not None:
        return git_paths
    return await asyncio.to_thread(_expand_filesystem_directory, directory)


def _expand_filesystem_directory(directory: Path) -> tuple[Path, ...]:
    return tuple(
        sorted(path.resolve() for path in directory.rglob("*.py") if path.is_file())
    )


async def _expand_git_directory(directory: Path) -> tuple[Path, ...] | None:
    git_executable = shutil.which("git")
    if git_executable is None:
        return None

    root_result = await _run_git(
        git_executable, directory, ("rev-parse", "--show-toplevel")
    )
    if root_result.returncode != 0:
        return None

    repository_root = await asyncio.to_thread(
        _resolve_decoded_path,
        root_result.stdout.decode("utf-8", errors="replace").strip(),
    )
    pathspec = str(directory.relative_to(repository_root))
    if pathspec == ".":
        pathspec = ":/"

    listed_result = await _run_git(
        git_executable,
        repository_root,
        (
            "ls-files",
            "-z",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            pathspec,
        ),
    )
    if listed_result.returncode != 0:
        return None

    return tuple(
        sorted(
            repository_root / Path(value.decode("utf-8"))
            for value in listed_result.stdout.split(b"\0")
            if value and Path(value.decode("utf-8")).suffix == ".py"
        )
    )


def _resolve_decoded_path(path: str) -> Path:
    return Path(path).resolve()


async def _run_git(
    git_executable: str, cwd: Path, arguments: Sequence[str]
) -> subprocess.CompletedProcess[bytes]:
    # Git executable comes from PATH and shell=False keeps arguments separate.
    # Directory scan filtering requires invoking Git's index-aware path selector.
    process = await asyncio.create_subprocess_exec(
        git_executable,
        "-C",
        str(cwd),
        *arguments,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    returncode = process.returncode
    if returncode is None:  # pragma: no cover
        returncode = _FINDING_FAILURE_EXIT_CODE
    return subprocess.CompletedProcess(
        args=(git_executable, "-C", str(cwd), *arguments),
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


async def _gather(
    futures: Sequence[asyncio.Future[Any] | Coroutine[Any, Any, Any]],  # noqa: AGT105
) -> None:
    if sys.version_info >= (3, 11):  # pragma: no cover
        async with asyncio.TaskGroup() as task_group:
            for future in futures:
                task_group.create_task(future)
        return
    await asyncio.gather(*futures)


async def _line_counts_for_files(paths: Sequence[Path]) -> dict[Path, int]:
    if not paths:
        return {}
    line_counts: dict[Path, int] = {}
    semaphore = asyncio.Semaphore(_LINE_COUNT_WORKERS)

    async def count_lines(path: Path) -> None:
        async with semaphore:
            line_counts[path] = await asyncio.to_thread(_line_count_for_file, path)

    await _gather([count_lines(path) for path in paths])
    return line_counts


def _finding_for_line_count(
    path: Path, line_count: int, thresholds: _Thresholds
) -> ModuleSizeFinding | None:
    if line_count >= thresholds.error_lines:
        return ModuleSizeFinding(
            path=path,
            line_count=line_count,
            level=FindingLevel.ERROR,
            threshold=thresholds.error_lines,
        )
    if line_count >= thresholds.warn_lines:
        return ModuleSizeFinding(
            path=path,
            line_count=line_count,
            level=FindingLevel.WARNING,
            threshold=thresholds.warn_lines,
        )
    return None


def _line_count_for_file(path: Path) -> int:
    line_count = 0
    saw_bytes = False
    previous_byte: int | None = None
    with path.open("rb") as file:
        while chunk := file.read(_LINE_COUNT_CHUNK_SIZE):
            saw_bytes = True
            line_count += chunk.count(b"\n")
            previous_byte = chunk[-1]
    if saw_bytes and previous_byte != _NEWLINE_BYTE:
        line_count += 1
    return line_count


def _render_findings(findings: Sequence[ModuleSizeFinding]) -> str:
    rows = [
        ("PATH", "LINES", "LEVEL", "THRESHOLD"),
        *(
            (
                str(finding.path),
                str(finding.line_count),
                finding.level.value,
                str(finding.threshold),
            )
            for finding in findings
        ),
    ]
    widths = tuple(max(len(row[column]) for row in rows) for column in range(4))
    rendered_lines = [
        "  ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
        for row in rows
    ]
    return "\n".join(rendered_lines) + "\n"


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
