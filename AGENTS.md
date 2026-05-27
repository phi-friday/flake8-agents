# Repository Guidelines

## Scope and Precedence

`flake8-agents` is a Python repository for flake8 extension development.

- Follow the closest applicable `AGENTS.md` first if subdirectory-specific files
  are added later, then this root file.
- Do not carry over stack-specific rules from related repositories unless they
  match this repository and the user explicitly asks for them.
- Treat `pyproject.toml`, `ruff.toml`, and `pyrefly.toml` as the final authority
  for local tooling behavior.

## Repository Layout

- `src/flake8_agents/`: package and flake8 extension code.
- `src/tests/`: pytest tests.
- `openspec/`: optional proposal, design, task, and spec artifacts when a change
  is being managed through OpenSpec.

## Local Developer Decisions

Developers may create a root-level `DECISIONS.md` file for personal preferences
and repeated decisions that should not be shared across the repository.

- `DECISIONS.md` is local-only and must stay ignored by git.
- If `DECISIONS.md` exists, read it before asking preference or decision
  questions, and apply the documented answers when they fit the current task.
- If `DECISIONS.md` is absent or does not cover the current decision, ask the
  developer using the normal workflow.
- Explicit user instructions, closer `AGENTS.md` files, and this repository's
  tracked configuration take precedence over `DECISIONS.md` if they conflict.

## OpenSpec Workflow

When a task names an OpenSpec change or modifies OpenSpec artifacts:

1. Read the relevant proposal, design, tasks, and spec files under
   `openspec/changes/`.
2. Implement against documented requirements, not assumptions.
3. Add or update tests for each changed requirement.
4. Update the corresponding `tasks.md` when implementation tasks are completed.
5. If public behavior changes beyond the current spec, update or create OpenSpec
   artifacts before implementation.

Run strict OpenSpec validation for changed specs when the validation command is
available.

## Structural Refactors

When splitting, moving, or retiring repository-owned modules or packages:

- Define the canonical owning module for each responsibility before editing.
- Preserve supported public façades with sorted literal `__all__` declarations
  when an old import path was a public boundary.
- Keep implementation-focused modules importable through their owning package,
  not through broad compatibility shims or retired root modules.
- Remove stale repository-owned imports and add guard coverage when a retired
  module path must stay unavailable.
- Align tests with the new ownership topology: public façade, owner modules,
  stale import rejection, and affected integration consumers.
- Run the relevant lint, format, type, and test commands before marking the
  refactor complete.

## Commands

Use `uv` for environment and tool execution.

- Sync dependencies: `uv sync`
- Lint: `uv run ruff check src`, `uv run flake8` and `uv run poe module-size`
- Format, required with the same priority as linting: `uv run ruff format src`
- Type check: `uv run pyrefly check src`
- Test: `uv run pytest`
- Coverage-enabled test suite: `uv run poe test-cov`

If Poe tasks are configured and valid for the files being touched, invoke them as
`uv run poe <task>`. Do not call `poe` directly.

## Python Style and Naming

- Use absolute imports from the package root; avoid relative imports such as
  `from ..module import name`.
- Prefer ordinary static imports over `import_module`. Use dynamic imports only
  when they are genuinely required, and document the narrow reason nearby. Do
  not bypass this rule by adding thin helper wrappers, indirect callable loaders,
  or other dynamic dispatch that exists only to hide module loading.
- Public and package-internal modules that intentionally export symbols must
  declare a sorted literal `__all__` as the first module declaration after the
  complete import section: future imports when present, runtime imports, then
  type-only imports or `if TYPE_CHECKING:` blocks. Package `__init__.py` files
  must include explicit `__all__` entries for re-exported modules, symbols, and
  lazy attributes. Modules with no intentional exports should use an empty
  `__all__` using the same placement rule or be explicitly excluded by
  repository validation as implementation-private.
- Cross-module imports from `flake8_agents` must target names declared by the
  imported module's export surface. Do not import leading-underscore symbols or
  private modules across module boundaries unless there is a narrow documented
  exception.
- Keep Python modules organized in this top-of-module order: future imports when
  present, runtime imports, type-only imports or `if TYPE_CHECKING:` blocks,
  `__all__`, global constants and variables, classes, then functions. Place all
  real runtime imports before any `if TYPE_CHECKING:` block or type-only imports,
  never interleave imports with declarations, and place `__all__` before other
  module-level constants, sentinels, variables, classes, or functions.
- Use `PascalCase` for classes and type aliases.
- Use `snake_case` for modules, functions, methods, variables, and fields.
- Use `UPPER_SNAKE_CASE` for constants.
- Prefix private/internal symbols with `_` when the boundary matters.
- Prefer descriptive names such as `error_code`, `rule_name`, `node`, or
  `line_number` over vague names such as `id`, `data`, or `value`.
- Write Google-style docstrings when docstrings are needed.
- Keep modules focused and avoid unrelated refactors.

## Strict Typing

This repository intentionally uses strict typing.

- Every new Python function and method must have explicit parameter and return
  type annotations.
- Annotate attributes and module-level constants when inference is not obvious.
- Prefer built-in generic types such as `list[str]` and `dict[str, int]`.
- Prefer Python 3.14 PEP 695 type parameter syntax for new generic functions,
  methods, classes, and type aliases, such as `def f[T](...)`, `class Box[T]:`,
  `type Alias[T] = ...`, and `def decorator[**P, R](...)`. Do not introduce
  module-level `TypeVar`, `ParamSpec`, or `TypeVarTuple` declarations unless a
  narrow documented exception is required by runtime behavior, a confirmed
  type-checker limitation, a third-party API constraint, or a test that
  intentionally covers legacy typing syntax.
- Do not use `object` as a generic "unknown value" annotation. Reserve `object`
  for values that are actually opaque identity-only objects, such as an
  `object()` sentinel, or for APIs that truly accept any object without
  inspecting it.
- Use `Any` only at real dynamic boundaries, such as untyped third-party APIs,
  externally decoded payloads before validation, or deliberately opaque test
  doubles. Keep the `Any` scope local, validate or narrow it immediately, and do
  not let it leak into domain models or public APIs.
- Never replace an inferable or known precise type with `Any`. If the shape is
  known, model it with a concrete class, dataclass, `TypedDict`, `Protocol`,
  precise union, or typed alias instead.
- Avoid `dict[str, object]` and `Mapping[str, object]` for structured payloads
  whose keys and value types are known. Use explicit payload models or narrowly
  typed mappings; keep broad mappings only at parse boundaries and convert them
  to domain types quickly.
- Avoid implicit `Any`, untyped decorators, unannotated callables, and vague
  variadic signatures. Prefer explicit `Callable[[ArgType], ReturnType]`,
  `Callable[[ArgType, OtherArgType], ReturnType]`, `Protocol`, or concrete
  test-double signatures over `Callable[..., ReturnType]` and broad
  `*args: object` / `**kwargs: object` unless the call surface is an intentionally
  opaque decorator or pass-through boundary.
- Do not weaken types just to silence Pyrefly. Prefer precise domain models,
  protocols, typed mappings, assertions, and runtime validation.
- Do not use `typing.cast` as a shortcut. A cast is acceptable only when a value
  has already been validated or narrowed and the type checker cannot express the
  invariant. Keep casts as close as possible to the validation and add a clear
  reason when it is not obvious.
- In tests, narrow types with `assert isinstance(...)`, membership checks, or
  helper validators before accessing typed fields. Do not use casts to construct
  impossible invalid states; feed raw invalid data through validation/parsing
  code instead.
- Avoid no-op type checks such as `isinstance(value, object)` and avoid type
  suppressions in Python code. For this repository:
  - `# type: ignore` is forbidden.
  - Bare `# pyrefly: ignore` is forbidden.
  - Only explicit, localized `# pyrefly: ignore[<rule>]` comments are allowed,
    and only for unavoidable Pyrefly limitations.
  - Suppressions must remain rare and narrowly scoped.
- Public APIs, flake8 plugin entry points, emitted error structures, and rule
  configuration models must use explicit, stable types.
- Test files may have limited typing relaxations according to `pyrefly.toml`, but
  production code must satisfy the strict baseline.

## Ruff Rules

Use `ruff.toml` as the final authority for linting and formatting. Ruff
validation has two required parts: linting and formatting. Neither command is
optional, and one is not a substitute for the other.

- Target Python version: Python 3.14.
- Line length: 88.
- Formatter: double quotes, spaces, docstring code formatting enabled.
- Linting: `select = ["ALL"]` with repository-specific ignores.
- Docstrings: Google-style convention.
- Fix Ruff violations directly by default. `noqa` suppressions must be rare,
  localized to the smallest practical scope, name the specific rule, and include
  an adjacent rationale when the justification is not obvious. Do not add
  suppressions for avoidable import placement, exception typing, typing, fixture,
  or module-boundary issues.

## Testing Conventions

- Put tests under `src/tests/`.
- Run pytest from the repository root with `uv run pytest ...`.
- Use `-k "..."` for focused pytest selection instead of node selectors with
  `::`.
- Name tests as `test_<scenario>_<outcome>`.
- Keep arrange/act/assert phases clear.
- Prefer explicit fixtures in test signatures over hidden global setup.
- Avoid giant opaque `autouse` fixtures.
- Use `Test<Subject>` classes as readability groups when a module covers
  multiple production functions, models, or behavior areas; do not add base test
  classes, mutable shared class/instance state, or hidden setup.
- Use `pytest.mark.parametrize` with readable IDs for behavior matrices.
- Avoid sleeps, real network calls, and order-dependent tests unless explicitly
  required and isolated.
- Keep successful pytest runs quiet under the existing pytest arguments: do not
  leave incidental stdout, stderr, or INFO-and-above log records in passing tests.
- Expected-error tests should assert the meaningful exception, error translation,
  captured output, or log contract directly; suppress or drain incidental
  framework tracebacks that are not part of the contract.
- Restore global mutations and environment changes in teardown.
- Prefer focused unit tests for flake8 rule behavior, option parsing, error
  formatting, AST traversal, and edge cases in invalid Python syntax handling.

## Agent Behavior

- Preserve user changes and do not overwrite unrelated work.
- Read local configuration before inventing commands or conventions.
- Keep implementation aligned with OpenSpec tasks and requirements when a task is
  explicitly driven by OpenSpec.
- Prefer `uv run ...` for project tools.
- When you need to ask the user a question, request a decision, or confirm a
  preference, do not end the response with a plain-text question. Use the
  `question` tool so the user can answer inline and the workflow can continue.
- Run the smallest relevant check first, then lint, format, Pyrefly, and pytest
  as appropriate before reporting completion. Treat formatting as required
  validation, not optional cleanup.
- If verification cannot be run, report exactly what was skipped and why.