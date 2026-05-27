# Test Guidelines

Scope: `src/tests/`. These rules refine the root `AGENTS.md` for test code.
Root repository rules still apply: run commands from the repository root, use
`uv run ...`, prefer absolute imports from `flake8_agents...` / `tests...`, and use
`pytest -k "..."` rather than `::` node selectors for focused test runs.

This file describes the desired test-suite direction. Do not preserve old test
organization, task-number file names, or oversized test modules just because
they already exist.

## Verification commands

- For focused test work, run the smallest relevant coverage-enabled pytest
  command first, for example:
  `uv run pytest src/tests -v -k "rule behavior" --cov=src/flake8_agents`.
- For test-only changes, prefer this order:
  `uv run ruff format <files>` -> `uv run ruff check <files>` ->
  `uv run pyrefly check <files>` -> relevant coverage-enabled
  `uv run pytest <files-or-dirs> -v --cov=src/flake8_agents`.
  `uv run flake8 <files-or-dirs>`
  `uv run module-size-file <files-or-dirs>`
- Before reporting broad completion, run from the repository root as applicable:
  `uv run ruff check src`, `uv run ruff format src`, `uv run pyrefly check src`,
  `uv run flake8 src`, `uv run module-size-file src` and the coverage-enabled full suite.
- Use `uv run poe test-cov` as the canonical coverage-enabled full-suite command.
  It runs pytest with coverage enabled and enforces the configured coverage
  threshold. Do not also run a separate full-suite `uv run pytest` unless
  diagnosing a coverage-wrapper failure.
- Do not pipe pytest output, depend on local `.env` state, or require developer
  machine services in tests.

## Test organization

- Default to a direct production-module mapping: tests for
  `src/flake8_agents/<module>.py` belong in `src/tests/test_<module>.py`.
  For example, tests for `src/flake8_agents/plugin.py` belong in
  `src/tests/test_plugin.py`.
- Tests for package `__init__.py` export surfaces belong in `src/tests/test_init.py`.
- When a module's tests are too large or split across distinct behavior areas,
  use a module-named directory with behavior-focused files, such as
  `src/tests/plugin/test_options.py` or `src/tests/plugin/test_errors.py`.
- Organize tests by production module first and behavior area second, not by
  implementation task number or change history.
- Use `Test<Subject>` classes as readability groups when one file covers
  multiple production functions, models, or behavior areas. These classes must
  not add base classes, mutable class or instance state, hidden setup, or
  implicit fixture dependencies.
- Split large modules when separate responsibilities can be tested independently.
  A test file should be understandable without scanning unrelated scenarios, and
  a test directory should make the owning production module obvious.
- Keep shared fixtures in the nearest `conftest.py` only when they are broadly
  useful. Put domain-specific builders, fakes, and assertions in explicit helper
  modules such as `tests/helpers/flake8.py` or `tests/helpers/ast.py`.
- Avoid compatibility wrappers or aliases that only support outdated test
  structure. Prefer updating call sites to the clearer helper name.

## Test shape and naming

- Name tests by behavior and expected result:
  `test_<scenario>_<expected_result>`.
- Keep arrange/act/assert phases obvious. Comments are useful only when they
  identify a non-obvious contract, boundary, or lifecycle guarantee.
- Prefer exact contract assertions over loose existence checks. Assert concrete
  error codes, line and column positions, messages, option values, and traversal
  results when those details are part of the contract.
- Cover invalid input, boundary values, disabled configuration, missing options,
  syntax errors, and empty-result cases explicitly.
- Use `pytest.raises(..., match="...")` when the message is stable and part of
  the behavior being protected.
- Use `pytest.mark.parametrize` with readable IDs for behavior matrices instead
  of imperative loops with hidden expectations.

```python
@pytest.mark.parametrize(
    ("source", "expected_error_codes"),
    [pytest.param("x = 1\n", (), id="no-violations")],
)
def test_checker_reports_expected_errors(
    source: str, expected_error_codes: tuple[str, ...]
) -> None: ...
```

## Flake8 rule testing

- Prefer small source snippets that exercise one behavior at a time.
- Assert the full emitted error contract when it is stable: line, column, error
  code, and message.
- Keep parser setup in helpers when several tests need it, but keep the source
  snippet and expected diagnostics visible in the test itself.
- Test both accepted and rejected examples for each rule so the test suite guards
  against false positives and false negatives.
- Cover nested scopes, decorators, imports, comprehensions, comments, string
  literals, and syntax-error paths when a rule can observe or skip them.
- Do not snapshot broad output when exact diagnostics can be asserted directly.

## Fixtures, fakes, and state

- Make dependencies visible in test signatures. Avoid hidden autouse setup unless
  it is tiny, deterministic, and applies to every test in the scope.
- Builders should create values only. Factories should perform side effects. Keep
  these roles separate so tests show where plugin options, AST nodes, or checker
  instances are created.
- Use descriptive scenario names such as `valid_source`, `invalid_source`,
  `configured_option`, and `expected_diagnostics` instead of ordinal names such
  as `source1` or `result2`.
- Restore every mutation: environment variables, working directories,
  monkeypatch targets, log handlers, process globals, registries, and caches.
- Treat process globals, singletons, registries, caches, and session-scoped
  fixtures as xdist hazards. Prefer per-test construction; if sharing is truly
  needed, make the shared value immutable or explicitly namespaced per worker.
- Namespace shared file-system paths, socket/port choices, cache keys, and other
  external identifiers with `tmp_path` and, when needed, pytest-xdist's
  `worker_id` fixture so parallel workers cannot collide.
- Use deterministic fakes for flake8 options, input files, and plugin call sites.
  Do not call real external services.

## Do not add

- Test files named after OpenSpec task numbers, temporary implementation phases,
  migration history, or combined module/task labels such as
  `test_plugin_tasks_6.py`.
- Tests that only pass in serial execution, depend on test ordering, or rely on
  state accumulated by previous tests.
- Real network calls, external services, or dependencies on developer machine
  state.
- Sleeps for synchronization. Use deterministic helpers, callbacks, or explicit
  state changes.
- Giant autouse fixtures, base test classes, hidden instance state, or global
  setup that makes dependencies invisible.
- Assertions like `len(items) >= 1` when exact error codes, positions, messages,
  or filtered records can be asserted.
- Broad `Any`, `object`, casts, or type suppressions when the test can model the
  value with a concrete fake, typed helper, dataclass, or runtime narrowing
  assertion.