# Repository Guidelines

## Project Overview

`flake8-agents` is a Python 3.10+ Flake8 plugin for agent-oriented Python
quality guardrails. It ships AGT diagnostics for typing escapes, dynamic
anti-patterns, import-boundary hygiene, and unused AGT `noqa` suppressions, plus
a `module-size` CLI for line-count thresholds.

Treat `pyproject.toml`, `ruff.toml`, and `pyrefly.toml` as the final authority
for local tooling behavior. Follow any closer `AGENTS.md` file for subdirectory
work, especially `src/tests/AGENTS.md` for tests.

## Architecture & Data Flow

- Flake8 entry point: `AGT = "flake8_agents.checker:FlakeAgentsChecker"`.
- `FlakeAgentsChecker` (`src/flake8_agents/checker.py`) receives Flake8's AST,
  filename, and source lines, runs owned checkers, then yields Flake8 tuples:
  `(line, column, message, checker_type)`.
- Owned checker families:
  - `TypeEscapeChecker` (`type_escape.py`) for typing escape diagnostics.
  - `AntiPatternChecker` (`anti_pattern.py`) for dynamic/runtime anti-patterns.
  - `ImportBoundaryChecker` (`import_boundary.py`) for import/export boundaries.
- The aggregate checker also tokenizes comments to report unused explicit
  `AGT...` suppressions as `AGT001`.
- `module-size` (`src/flake8_agents/cli/module_size.py`) is separate from Flake8:
  parse args -> resolve Python files, preferring git-aware discovery -> async line
  counting -> sorted warning/error findings -> tabular stdout/stderr + exit code.
- Production code favors small focused modules, frozen dataclasses for diagnostic
  records, enums for severity/code families, immutable tuple returns, and
  deterministic sorting before output.

## Key Directories

- `src/flake8_agents/`: package source, Flake8 checker orchestration, rule
  implementations, package metadata facade, and `py.typed` marker.
- `src/flake8_agents/cli/`: console-command implementation for `module-size`.
- `src/tests/`: pytest suite for checker behavior, Flake8 integration, package
  exports, and CLI contracts. Read `src/tests/AGENTS.md` before editing tests.
- `src/tests/cli/`: CLI-specific tests for `module-size`.
- `openspec/specs/`: persistent behavior specs. Use them when a task references
  OpenSpec or changes a specified capability.
- `samples/`: reference/legacy guard-script examples. Some scripts have 3.14t
  uv-script shebangs; do not copy those as the project compatibility baseline.

## Development Commands

Use `uv` for environment and tool execution. Prefer Poe tasks through
`uv run poe <task>` when a task exists; do not call `poe` directly.

```sh
uv sync
uv run ruff format src
uv run ruff check src
uv run pyrefly check src
uv run flake8 src
uv run poe module-size
uv run pytest
uv run poe test-cov
```

Useful focused examples:

```sh
uv run pytest src/tests -k "type escape" --cov=src/flake8_agents
uv run flake8 --isolated --select AGT path/to/file.py
uv run module-size src --warn-lines 800 --error-lines 1000
```

`uv run poe lint` runs the configured sequence: format, Ruff, Pyrefly, Flake8,
and module-size. Formatting is a required check, not optional cleanup.

## Code Conventions & Common Patterns

- Runtime support is Python `>=3.10`; Ruff and Pyrefly target `py310`. Do not
  introduce unguarded 3.11+ or 3.12+ syntax/APIs. In particular, do not use
  PEP 695 generic syntax or `type` statements in production code while 3.10 is
  supported.
- Use absolute imports from `flake8_agents...`; avoid relative imports for
  package code.
- Keep imports and exports explicit. Public/package-internal modules that expose
  symbols should define a sorted literal `__all__` after imports and before other
  declarations.
- Keep module tops ordered: future imports, runtime imports, type-only imports or
  `if TYPE_CHECKING:`, `__all__`, constants, classes, functions.
- Prefer static imports. Use dynamic import machinery only for a real runtime
  boundary, and document the narrow reason nearby.
- Use `typing_extensions` for compatibility helpers unavailable in Python 3.10
  stdlib, such as `override`.
- Keep Flake8 checkers side-effect-light: derive diagnostics from AST and source
  lines, preserve stable line/column/message contracts, and avoid global mutable
  state.
- The AGT rules themselves enforce many typing, import-boundary, dynamic-dispatch,
  and suppression-hygiene policies. Do not duplicate those rule catalogs here;
  run `uv run flake8 src` and fix the source instead of weakening or bypassing
  diagnostics.
- Ruff controls formatting: 88 columns, double quotes, space indentation,
  Google-style docstrings when docstrings are needed.
- Prefer descriptive names like `error_code`, `rule_name`, `node`, `line_number`,
  and `expected_diagnostics` over vague names.
- Keep refactors clean-cut: retire stale imports, update tests and public facades,
  and avoid compatibility shims unless they are a deliberate supported API.

## Important Files

- `pyproject.toml`: package metadata, Python requirement, dependencies, Flake8
  plugin entry point, console script, pytest/coverage config, uv groups, Poe tasks.
- `ruff.toml`: lint/format policy, Python target, import sorting, AGT external
  integration, and per-test ignores.
- `pyrefly.toml`: type-checking baseline and test-specific relaxations.
- `uv.lock`: resolved dependency graph for the configured non-Windows uv
  environment.
- `src/flake8_agents/checker.py`: aggregate Flake8 plugin and unused AGT noqa
  detection.
- `src/flake8_agents/type_escape.py`: AGT100-family typing escape rules.
- `src/flake8_agents/anti_pattern.py`: AGT200-family dynamic anti-pattern rules.
- `src/flake8_agents/import_boundary.py`: AGT300-family import/export rules.
- `src/flake8_agents/cli/module_size.py`: `module-size` CLI implementation.
- `src/flake8_agents/_version_.py` and generated `_version.py`: version facade
  and hatch-vcs generated metadata.
- `src/tests/AGENTS.md`: test-specific workflow and quality rules.
- `README.md`: currently empty; rely on configs/specs/source for repository facts.

## Runtime/Tooling Preferences

- Supported Python range is 3.10 through current classifiers; keep compatibility
  paths explicit when newer APIs are useful.
- Runtime dependencies are intentionally small: `flake8` and
  `typing-extensions`. Avoid adding dependencies without a clear package-level
  reason.
- Build backend is `hatchling` with `hatch-vcs`; `_version.py` is generated and
  excluded from normal lint/type scope.
- `uv` default groups include flake, dev, and test tooling. The configured uv
  environment excludes Windows (`sys_platform != 'win32'`).
- For OpenSpec-driven work, read the relevant files under `openspec/specs/` or
  `openspec/changes/`, implement against documented requirements, update tests,
  and validate changed specs when the command is available.
- Preserve user changes. Do not overwrite unrelated work, stash, or revert files
  you did not intentionally modify.

## Testing & QA

- Test framework: pytest with coverage via `pytest-cov`; async tests use AnyIO.
- Canonical full coverage command: `uv run poe test-cov` with a configured 99%
  coverage threshold.
- Focused tests should use `-k "..."` rather than `::` node selectors.
- Checker tests usually build small source snippets, parse with `ast.parse`, run
  the checker directly, and assert exact diagnostics. Integration tests also run
  real `uv run flake8 --isolated --select AGT` subprocesses.
- CLI tests exercise both `module_size.main(...)` with captured output and the
  installed `module-size` console script.
- Assert behavior contracts: error code, line, column, message, exit code,
  stdout/stderr, sorted output, false positives, and false negatives where they
  matter.
- Use deterministic temp files, monkeypatching, and explicit fixtures. Avoid
  real network calls, sleeps, order-dependent tests, broad autouse fixtures, and
  developer-machine state.
- Before reporting completion on code changes, run the smallest relevant check
  first, then the applicable format, lint, type, Flake8, module-size, and pytest
  commands for the touched area.
