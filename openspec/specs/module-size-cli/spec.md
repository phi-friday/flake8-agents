# module-size-cli Specification

## Purpose

Define the package-owned `module-size` CLI for scanning explicit Python files
and directories against configurable physical line-count thresholds.
## Requirements
### Requirement: Module-size CLI accepts explicit scan paths

The system SHALL expose a `module-size` console script that requires one or
more positional paths. Each positional path SHALL be either an existing Python
file or an existing directory.

#### Scenario: Python file path is accepted

- **WHEN** a user runs `module-size path/to/module.py`
- **THEN** the command scans that file for module-size findings.

#### Scenario: Directory path is accepted

- **WHEN** a user runs `module-size path/to/package`
- **THEN** the command scans Python files contained under that directory.

#### Scenario: Missing path is a usage error

- **WHEN** a user runs `module-size` without positional paths
- **THEN** the command exits with a usage error and does not scan a default root.

#### Scenario: Non-Python file path is rejected

- **WHEN** a user supplies an explicit file path that does not end with `.py`
- **THEN** the command exits with an error explaining that the path is not a
  Python file.

### Requirement: Module-size CLI is executable as an installed console script

The system SHALL expose module-size scanning through the installed
`module-size` console script declared in project packaging metadata. The
command SHALL call the package-owned CLI entry function rather than requiring
users to run a module path directly.

#### Scenario: Installed command scans a Python file

- **WHEN** a user runs the installed `module-size` command with an explicit
  Python file path
- **THEN** the command scans that file and reports module-size findings according
  to the configured thresholds.

### Requirement: Directory expansion respects Git ignore state when available

The module-size CLI SHALL expand directory paths to Python files deterministically.
When a directory is inside a Git worktree and Git is available, directory
expansion SHALL include tracked Python files and unignored untracked Python files.
When Git filtering is unavailable for a directory, expansion SHALL fall back to
recursive filesystem discovery of `*.py` files.

#### Scenario: Git worktree directory excludes ignored files

- **WHEN** a user scans a directory inside a Git worktree containing ignored
  Python files
- **THEN** ignored Python files are not scanned through directory expansion.

#### Scenario: Untracked unignored file is included

- **WHEN** a user scans a directory inside a Git worktree containing an untracked
  Python file that is not ignored
- **THEN** that Python file is scanned through directory expansion.

#### Scenario: Non-Git directory falls back to filesystem recursion

- **WHEN** a user scans a directory that Git cannot filter
- **THEN** Python files under that directory are discovered recursively from the
  filesystem.

#### Scenario: Explicit file bypasses directory filtering

- **WHEN** a user supplies an explicit Python file path
- **THEN** the command scans that file directly even if directory-based Git
  filtering would not select it.

### Requirement: Module-size CLI counts physical lines

The module-size CLI SHALL classify files using physical line counts, counting
newline-delimited physical lines and counting a non-empty final line even when the
file does not end with a newline.

#### Scenario: File ending without newline counts final line

- **WHEN** the command scans a non-empty Python file whose last byte is not a
  newline
- **THEN** the final physical line contributes to the file's line count.

#### Scenario: Empty file has zero lines

- **WHEN** the command scans an empty Python file
- **THEN** the file's line count is zero.

### Requirement: Module-size scans use async orchestration and worker-thread file reads

The module-size CLI SHALL expose an async scan API for module-size scans. The
synchronous console-script entry point SHALL adapt to that async implementation.
Blocking filesystem discovery and physical line counting SHALL run in worker
threads so scanning many files does not serialize all blocking file I/O on the
event loop. Concurrent line-count scheduling SHALL remain bounded and compatible
with the repository's supported Python versions.

#### Scenario: Async scan API can be awaited

- **WHEN** repository code calls the module-size scan API from an async context
- **THEN** it can await the scan without invoking the console-script adapter.

#### Scenario: Physical line reads are thread-offloaded

- **WHEN** the async scanner counts physical lines for scanned Python files
- **THEN** blocking line-count reads run through worker-thread offloading rather
  than directly on the event loop.

#### Scenario: Line-count concurrency is bounded

- **WHEN** the async scanner schedules line-count work for scanned Python files
- **THEN** it uses bounded command-scoped concurrency without requiring APIs that
  are unavailable on supported Python versions.

### Requirement: Module-size CLI supports configurable thresholds

The module-size CLI SHALL support `--warn-lines` and `--error-lines` options.
Both threshold values SHALL be positive integers, and `--warn-lines` SHALL be less
than `--error-lines`.

#### Scenario: Valid thresholds are accepted

- **WHEN** a user runs
  `module-size --warn-lines 800 --error-lines 1000 path/to/package`
- **THEN** the command uses 800 as the warning threshold and 1000 as the error
  threshold.

#### Scenario: Warning threshold must be below error threshold

- **WHEN** a user supplies a warning threshold greater than or equal to the error
  threshold
- **THEN** the command exits with a usage error explaining the threshold
  relationship.

#### Scenario: Thresholds must be positive

- **WHEN** a user supplies a zero or negative warning or error threshold
- **THEN** the command exits with a usage error explaining that thresholds must be
  positive integers.

### Requirement: Module-size CLI classifies warning and error findings inclusively

The module-size CLI SHALL classify a scanned file as an error finding when its
physical line count is greater than or equal to the configured error threshold. It
SHALL classify a scanned file as a warning finding when its physical line count is
greater than or equal to the configured warning threshold and less than the
configured error threshold. Files below the warning threshold SHALL produce no
finding.

#### Scenario: Error threshold boundary is an error

- **WHEN** a scanned file has exactly the configured error threshold number of
  physical lines
- **THEN** the file is reported as an error finding.

#### Scenario: Warning threshold boundary is a warning

- **WHEN** a scanned file has exactly the configured warning threshold number of
  physical lines and fewer than the configured error threshold number of physical
  lines
- **THEN** the file is reported as a warning finding.

#### Scenario: Below warning threshold is clean

- **WHEN** a scanned file has fewer physical lines than the configured warning
  threshold
- **THEN** the file produces no module-size finding.

### Requirement: Module-size CLI renders deterministic human-readable output

The module-size CLI SHALL render findings in deterministic path order as
human-readable output that includes each finding's path, physical line count,
level, and threshold. Finding output SHALL be written to stdout. Usage errors and
scan failures SHALL be written to stderr.

#### Scenario: Findings are sorted by path

- **WHEN** multiple files produce module-size findings
- **THEN** the command reports those findings in deterministic path order.

#### Scenario: Warning-only findings are reported on stdout

- **WHEN** a scan produces warning findings and no error findings
- **THEN** stdout contains the warning finding details and stderr does not contain
  routine finding output.

#### Scenario: Error findings are reported on stdout

- **WHEN** a scan produces error findings
- **THEN** stdout contains the error finding details and stderr does not contain
  routine finding output.

### Requirement: Module-size CLI exit codes distinguish findings from failures

The module-size CLI SHALL exit successfully when a scan completes without error
findings, including scans that produce only warning findings. It SHALL exit with
failure when any error finding is present. It SHALL use usage-error behavior for
invalid options or invalid paths.

#### Scenario: Clean scan succeeds

- **WHEN** all scanned files are below the warning threshold
- **THEN** the command exits successfully.

#### Scenario: Warning-only scan succeeds

- **WHEN** scanned files produce warning findings but no error findings
- **THEN** the command exits successfully.

#### Scenario: Error finding fails command

- **WHEN** at least one scanned file produces an error finding
- **THEN** the command exits with failure.

### Requirement: Module-size CLI remains separate from flake8 diagnostics

The module-size CLI SHALL NOT add, remove, or modify flake8 extension diagnostics
or the existing `AGT` flake8 entry point.

#### Scenario: Flake8 entry point is unchanged

- **WHEN** the module-size CLI is added
- **THEN** the existing `AGT` flake8 extension entry point remains available with
  its existing checker target.

### Requirement: Module-size CLI supports regex exclusions

The module-size CLI SHALL support a repeatable `--exclude` option. Each `--exclude` value SHALL be compiled as a Python regular expression and SHALL match against the normalized resolved path string for each candidate Python file. A file SHALL be skipped when any exclude expression matches its normalized resolved path string. Exclusions SHALL apply to files selected from explicit Python file paths and directory expansion. Exclusions SHALL be applied before physical line counting. Invalid exclude expressions SHALL be reported as usage errors.

#### Scenario: Directory-expanded file matching exclude is skipped

- **WHEN** a user scans a directory containing Python files and supplies `--exclude` with a regular expression matching one candidate file path
- **THEN** the matching file is not scanned and non-matching candidate Python files are scanned normally.

#### Scenario: Repeated excludes skip any matching file

- **WHEN** a user supplies multiple `--exclude` options while scanning files
- **THEN** any candidate Python file matching at least one exclude expression is skipped.

#### Scenario: Explicit Python file matching exclude is skipped

- **WHEN** a user supplies an explicit Python file path and an `--exclude` expression matching that file path
- **THEN** the file is not scanned and does not produce a module-size finding.

#### Scenario: Invalid exclude regex is a usage error

- **WHEN** a user supplies an `--exclude` value that is not a valid Python regular expression
- **THEN** the command exits with a usage error and does not scan files.

#### Scenario: Excluded files are not line counted

- **WHEN** a user supplies an `--exclude` expression matching a candidate Python file path
- **THEN** the scanner skips that file before physical line-count reads are scheduled.

### Requirement: Module-size CLI can suppress warning output
The module-size CLI SHALL support a `--suppress-warnings` option that omits warning findings from final human-readable stdout output. The option SHALL NOT omit error findings, change physical line counting, change finding classification, change `scan_paths` results, or change exit-code behavior.

#### Scenario: Warning-only findings are suppressed from stdout
- **WHEN** a scan produces warning findings and no error findings
- **AND** the user supplies `--suppress-warnings`
- **THEN** stdout is empty
- **AND** stderr is empty
- **AND** the command exits successfully.

#### Scenario: Error findings remain visible when warnings are suppressed
- **WHEN** a scan produces error findings
- **AND** the user supplies `--suppress-warnings`
- **THEN** stdout contains the error finding details
- **AND** stderr does not contain routine finding output
- **AND** the command exits with failure.

#### Scenario: Mixed findings suppress only warnings
- **WHEN** a scan produces both warning and error findings
- **AND** the user supplies `--suppress-warnings`
- **THEN** stdout contains the error finding details
- **AND** stdout does not contain the warning finding details
- **AND** the command exits with failure.

