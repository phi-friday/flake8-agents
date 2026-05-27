from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import sys
import sysconfig
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from typing_extensions import Self

from flake8_agents.cli import module_size

if TYPE_CHECKING:
    from collections.abc import Coroutine, Sequence
    from types import TracebackType

PROJECT_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class CliResult:
    returncode: int
    stdout: str
    stderr: str


def run_module_size(capsys: pytest.CaptureFixture[str], *arguments: str) -> CliResult:
    try:
        returncode = module_size.main(arguments)
    except SystemExit as error:
        returncode = system_exit_code(error)
    captured = capsys.readouterr()
    return CliResult(returncode=returncode, stdout=captured.out, stderr=captured.err)


def system_exit_code(error: SystemExit) -> int:
    code = error.code
    if code is None:
        return 0
    if isinstance(code, int):
        return code
    message = f"unexpected SystemExit code: {code}"
    raise AssertionError(message)


def run_console_script(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        (console_script_path("module-size"), *arguments),
        cwd=PROJECT_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def console_script_path(script_name: str) -> str:
    scripts_path = sysconfig.get_path("scripts")
    script_path = Path(scripts_path) / script_name
    if sys.platform == "win32":
        script_path = script_path.with_suffix(".exe")
    resolved_path = shutil.which(script_path.name, path=scripts_path)
    if resolved_path is None:
        message = f"console script is not installed: {script_path}"
        raise AssertionError(message)
    return resolved_path


def run_git(repository: Path, *arguments: str) -> None:
    subprocess.run(
        ("git", *arguments), cwd=repository, check=True, capture_output=True, text=True
    )


def write_python_lines(path: Path, line_count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(f"line_{index} = {index}\n" for index in range(line_count)),
        encoding="utf-8",
    )


def output_lines(result: CliResult) -> list[str]:
    return result.stdout.splitlines()


class TestPathInputs:
    def test_missing_path_exits_with_usage_error(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        result = run_module_size(capsys)

        assert result.returncode != 0
        assert result.stdout == ""
        assert "paths" in result.stderr

    def test_missing_path_exits_with_usage_error_from_console_script(self) -> None:
        result = run_console_script()

        assert result.returncode != 0
        assert result.stdout == ""
        assert "paths" in result.stderr

    def test_console_script_scans_python_file(self, tmp_path: Path) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)

        result = run_console_script(
            "--warn-lines", "2", "--error-lines", "5", str(module_path)
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert "warning" in result.stdout
        assert result.stderr == ""

    def test_nonexistent_path_is_rejected(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        missing_path = tmp_path / "missing.py"

        result = run_module_size(capsys, str(missing_path))

        assert result.returncode != 0
        assert result.stdout == ""
        assert "does not exist" in result.stderr

    def test_non_python_file_path_is_rejected(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        text_path = tmp_path / "notes.txt"
        text_path.write_text("not python\n", encoding="utf-8")

        result = run_module_size(capsys, str(text_path))

        assert result.returncode != 0
        assert result.stdout == ""
        assert "Python file" in result.stderr

    def test_non_file_and_non_directory_path_is_rejected(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        fifo_path = tmp_path / "stream.py"
        os.mkfifo(fifo_path)

        result = run_module_size(capsys, str(fifo_path))

        assert result.returncode != 0
        assert result.stdout == ""
        assert "not a file or directory" in result.stderr

    def test_explicit_python_file_is_scanned(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(module_path)
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert "warning" in result.stdout
        assert "2" in result.stdout
        assert result.stderr == ""

    def test_directory_path_scans_python_files_only(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        package_path = tmp_path / "package"
        module_path = package_path / "module.py"
        ignored_text_path = package_path / "notes.txt"
        write_python_lines(module_path, 2)
        ignored_text_path.write_text("not python\n", encoding="utf-8")

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(package_path)
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert str(ignored_text_path) not in result.stdout
        assert result.stderr == ""


class TestDirectoryExpansion:
    @pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
    def test_git_directory_scan_excludes_ignored_and_includes_untracked_files(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        repository = tmp_path / "repository"
        package_path = repository / "package"
        tracked_path = package_path / "tracked.py"
        untracked_path = package_path / "untracked.py"
        ignored_path = package_path / "ignored.py"
        repository.mkdir()
        run_git(repository, "init")
        write_python_lines(tracked_path, 2)
        write_python_lines(untracked_path, 2)
        write_python_lines(ignored_path, 2)
        (repository / ".gitignore").write_text("package/ignored.py\n", encoding="utf-8")
        run_git(
            repository, "add", ".gitignore", str(tracked_path.relative_to(repository))
        )

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(package_path)
        )

        assert result.returncode == 0
        assert str(tracked_path) in result.stdout
        assert str(untracked_path) in result.stdout
        assert str(ignored_path) not in result.stdout
        assert result.stderr == ""

    @pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
    def test_git_repository_root_directory_scan_uses_root_pathspec(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        repository = tmp_path / "repository"
        tracked_path = repository / "tracked.py"
        repository.mkdir()
        run_git(repository, "init")
        write_python_lines(tracked_path, 2)
        run_git(repository, "add", str(tracked_path.relative_to(repository)))

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(repository)
        )

        assert result.returncode == 0
        assert str(tracked_path) in result.stdout
        assert result.stderr == ""

    @pytest.mark.skipif(shutil.which("git") is None, reason="git is required")
    def test_explicit_python_file_bypasses_git_directory_filtering(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        repository = tmp_path / "repository"
        ignored_path = repository / "ignored.py"
        repository.mkdir()
        run_git(repository, "init")
        write_python_lines(ignored_path, 2)
        (repository / ".gitignore").write_text("ignored.py\n", encoding="utf-8")

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(ignored_path)
        )

        assert result.returncode == 0
        assert str(ignored_path) in result.stdout
        assert result.stderr == ""

    def test_non_git_directory_scan_falls_back_to_filesystem_recursion(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "not-a-repo" / "nested" / "module.py"
        write_python_lines(module_path, 2)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            str(module_path.parents[1]),
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert result.stderr == ""

    def test_directory_scan_falls_back_when_git_is_unavailable(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        module_path = tmp_path / "package" / "module.py"
        write_python_lines(module_path, 2)
        monkeypatch.setattr(module_size.shutil, "which", lambda _name: None)

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(module_path.parent)
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert result.stderr == ""

    def test_directory_scan_falls_back_when_git_listing_fails(
        self,
        capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        module_path = tmp_path / "package" / "module.py"
        write_python_lines(module_path, 2)

        async def fail_git_listing(
            git_executable: str, cwd: Path, arguments: Sequence[str]
        ) -> subprocess.CompletedProcess[bytes]:
            assert git_executable
            assert cwd
            if "rev-parse" in arguments:
                return subprocess.CompletedProcess(
                    args=arguments,
                    returncode=0,
                    stdout=f"{tmp_path}\n".encode(),
                    stderr=b"",
                )
            return subprocess.CompletedProcess(
                args=arguments, returncode=1, stdout=b"", stderr=b"failed"
            )

        monkeypatch.setattr(module_size, "_run_git", fail_git_listing)

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(module_path.parent)
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert result.stderr == ""


class TestRegexExclusions:
    def test_directory_scan_excludes_matching_python_file(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        package_path = tmp_path / "package"
        scanned_path = package_path / "scanned.py"
        generated_path = package_path / "generated.py"
        write_python_lines(scanned_path, 2)
        write_python_lines(generated_path, 2)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            "--exclude",
            r"(^|/)generated\.py$",
            str(package_path),
        )

        assert result.returncode == 0
        assert str(scanned_path) in result.stdout
        assert str(generated_path) not in result.stdout
        assert result.stderr == ""

    def test_repeated_excludes_skip_any_matching_file(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        package_path = tmp_path / "package"
        first_excluded_path = package_path / "generated.py"
        second_excluded_path = package_path / "vendored.py"
        scanned_path = package_path / "scanned.py"
        write_python_lines(first_excluded_path, 2)
        write_python_lines(second_excluded_path, 2)
        write_python_lines(scanned_path, 2)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            "--exclude",
            r"(^|/)generated\.py$",
            "--exclude",
            r"(^|/)vendored\.py$",
            str(package_path),
        )

        assert result.returncode == 0
        assert str(first_excluded_path) not in result.stdout
        assert str(second_excluded_path) not in result.stdout
        assert str(scanned_path) in result.stdout
        assert result.stderr == ""

    def test_explicit_matching_python_file_is_excluded(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "generated.py"
        write_python_lines(module_path, 2)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            "--exclude",
            r"(^|/)generated\.py$",
            str(module_path),
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_invalid_exclude_regex_is_usage_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)

        result = run_module_size(capsys, "--exclude", "[", str(module_path))

        assert result.returncode != 0
        assert result.stdout == ""
        assert "invalid exclude regex" in result.stderr

    async def test_excluded_files_are_not_line_counted(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        scanned_path = tmp_path / "scanned.py"
        excluded_path = tmp_path / "generated.py"
        write_python_lines(scanned_path, 2)
        write_python_lines(excluded_path, 2)
        counted_paths: list[Path] = []

        def record_line_count(path: Path) -> int:
            counted_paths.append(path)
            if path == excluded_path.resolve():
                raise AssertionError("excluded file should not be line counted")
            return path.read_bytes().count(b"\n")

        monkeypatch.setattr(module_size, "_line_count_for_file", record_line_count)

        findings = await module_size.scan_paths(
            (tmp_path,),
            warn_lines=2,
            error_lines=5,
            exclude_patterns=(r"(^|/)generated\.py$",),
        )

        assert [finding.path for finding in findings] == [scanned_path.resolve()]
        assert counted_paths == [scanned_path.resolve()]


class TestLineCountingAndThresholds:
    def test_empty_python_file_is_clean(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "empty.py"
        module_path.write_text("", encoding="utf-8")

        result = run_module_size(
            capsys, "--warn-lines", "1", "--error-lines", "2", str(module_path)
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_file_without_trailing_newline_counts_final_line(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        module_path.write_text("value = 1", encoding="utf-8")

        result = run_module_size(
            capsys, "--warn-lines", "1", "--error-lines", "2", str(module_path)
        )

        assert result.returncode == 0
        assert str(module_path) in result.stdout
        assert "warning" in result.stdout
        assert result.stderr == ""

    def test_error_threshold_boundary_fails(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 3)

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "3", str(module_path)
        )

        assert result.returncode == 1
        assert str(module_path) in result.stdout
        assert "error" in result.stdout
        assert result.stderr == ""

    def test_invalid_threshold_relationship_is_usage_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 1)

        result = run_module_size(
            capsys, "--warn-lines", "3", "--error-lines", "3", str(module_path)
        )

        assert result.returncode != 0
        assert result.stdout == ""
        assert "warn-lines" in result.stderr
        assert "error-lines" in result.stderr

    def test_non_positive_threshold_is_usage_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 1)

        result = run_module_size(
            capsys, "--warn-lines", "0", "--error-lines", "3", str(module_path)
        )

        assert result.returncode != 0
        assert result.stdout == ""
        assert "positive" in result.stderr

    def test_non_integer_threshold_is_usage_error(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 1)

        result = run_module_size(
            capsys, "--warn-lines", "many", "--error-lines", "3", str(module_path)
        )

        assert result.returncode != 0
        assert result.stdout == ""
        assert "positive" in result.stderr


class TestAsyncScanning:
    async def test_scan_paths_can_be_awaited(self, tmp_path: Path) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)

        findings = await module_size.scan_paths(
            (module_path,), warn_lines=2, error_lines=5
        )

        assert findings == (
            module_size.ModuleSizeFinding(
                path=module_path.resolve(),
                line_count=2,
                level=module_size.FindingLevel.WARNING,
                threshold=2,
            ),
        )

    async def test_scan_paths_offloads_line_counts_to_worker_threads(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        first_path = tmp_path / "first.py"
        second_path = tmp_path / "second.py"
        write_python_lines(first_path, 2)
        write_python_lines(second_path, 2)
        loop_thread_id = threading.get_ident()
        worker_thread_ids: list[int] = []

        def record_line_count(path: Path) -> int:
            worker_thread_ids.append(threading.get_ident())
            return path.read_bytes().count(b"\n")

        monkeypatch.setattr(module_size, "_line_count_for_file", record_line_count)

        findings = await module_size.scan_paths(
            (first_path, second_path), warn_lines=2, error_lines=5
        )

        assert [finding.path for finding in findings] == [
            first_path.resolve(),
            second_path.resolve(),
        ]
        assert worker_thread_ids
        assert all(thread_id != loop_thread_id for thread_id in worker_thread_ids)

    @pytest.mark.skipif(
        sys.version_info < (3, 11),
        reason="asyncio.TaskGroup is available only on Python 3.11 and newer",
    )
    async def test_scan_paths_uses_task_group_for_line_counts(
        self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)
        task_group_entries: list[bool] = []
        tasks: list[asyncio.Task[None]] = []

        class RecordingTaskGroup:
            async def __aenter__(self) -> Self:
                task_group_entries.append(True)
                return self

            async def __aexit__(
                self,
                exception_type: type[BaseException] | None,
                exception: BaseException | None,
                traceback: TracebackType | None,
            ) -> None:
                for task in tasks:
                    await task

            def create_task(
                self, coroutine: Coroutine[None, None, None]
            ) -> asyncio.Task[None]:
                task = asyncio.create_task(coroutine)
                tasks.append(task)
                return task

        monkeypatch.setattr(module_size.asyncio, "TaskGroup", RecordingTaskGroup)

        findings = await module_size.scan_paths(
            (module_path,), warn_lines=2, error_lines=5
        )

        assert findings
        assert task_group_entries == [True]


class TestOutputAndExitCodes:
    def test_findings_are_sorted_by_path(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        later_path = tmp_path / "z_later.py"
        earlier_path = tmp_path / "a_earlier.py"
        write_python_lines(later_path, 1)
        write_python_lines(earlier_path, 1)

        result = run_module_size(
            capsys, "--warn-lines", "1", "--error-lines", "3", str(tmp_path)
        )

        assert result.returncode == 0
        lines = output_lines(result)
        assert str(earlier_path) in lines[1]
        assert str(later_path) in lines[2]
        assert result.stderr == ""

    def test_warning_only_findings_succeed(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(module_path)
        )

        assert result.returncode == 0
        assert "warning" in result.stdout
        assert "error" not in result.stdout
        assert result.stderr == ""

    def test_error_findings_fail_with_findings_on_stdout(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 5)

        result = run_module_size(
            capsys, "--warn-lines", "2", "--error-lines", "5", str(module_path)
        )

        assert result.returncode == 1
        assert "error" in result.stdout
        assert str(module_path) in result.stdout
        assert result.stderr == ""

    def test_suppress_warnings_omits_warning_only_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 2)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            "--suppress-warnings",
            str(module_path),
        )

        assert result.returncode == 0
        assert result.stdout == ""
        assert result.stderr == ""

    def test_suppress_warnings_keeps_error_output(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        module_path = tmp_path / "module.py"
        write_python_lines(module_path, 5)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            "--suppress-warnings",
            str(module_path),
        )

        assert result.returncode == 1
        assert str(module_path) in result.stdout
        assert "error" in result.stdout
        assert result.stderr == ""

    def test_suppress_warnings_omits_only_warning_rows(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        warning_path = tmp_path / "warning.py"
        error_path = tmp_path / "error.py"
        write_python_lines(warning_path, 2)
        write_python_lines(error_path, 5)

        result = run_module_size(
            capsys,
            "--warn-lines",
            "2",
            "--error-lines",
            "5",
            "--suppress-warnings",
            str(tmp_path),
        )

        assert result.returncode == 1
        assert str(error_path) in result.stdout
        assert "error" in result.stdout
        assert str(warning_path) not in result.stdout
        assert result.stderr == ""
