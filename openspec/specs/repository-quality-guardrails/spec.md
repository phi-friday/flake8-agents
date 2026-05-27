# repository-quality-guardrails Specification

## Purpose

Define repository-wide Python quality guardrails for strict typing, clean code,
async boundaries, testing conventions, validation commands, Ruff/Pyrefly
suppression policy, and alignment between OpenSpec requirements and agent
guidance.
## Requirements
### Requirement: Strict typing rules are normative

The system SHALL treat strict typing rules documented in applicable `AGENTS.md`,
`pyproject.toml`, `pyrefly.toml`, and OpenSpec requirements as mandatory
implementation requirements for production code and public/tested boundaries.

#### Scenario: Production code follows strict typing guidance

- **WHEN** production Python code is added or modified
- **THEN** every new function and method has explicit parameter and return type
  annotations
- **AND** attributes or module-level constants are annotated when inference is
  not obvious.

#### Scenario: Modern generic syntax is preferred

- **WHEN** repository-owned Python code declares generic functions, methods,
  classes, or type aliases
- **THEN** it uses Python 3.14 type parameter syntax such as `def f[T](...)`,
  `class Box[T]:`, `type Alias[T] = ...`, or `def decorator[**P, R](...)`
  instead of module-level `TypeVar`, `ParamSpec`, or `TypeVarTuple`
  declarations unless a documented runtime, checker, or third-party constraint
  requires legacy syntax.

#### Scenario: Broad dynamic types stay at true boundaries

- **WHEN** a value's shape is known or can be validated
- **THEN** production code models it with precise classes, dataclasses,
  `TypedDict`, `Protocol`, precise unions, or typed aliases instead of `Any`,
  `object`, `dict[str, object]`, or broad mappings.

#### Scenario: Any remains local

- **WHEN** untyped third-party APIs, externally decoded payloads, or deliberately
  opaque test doubles require `Any`
- **THEN** the `Any` scope remains local to that boundary, is validated or
  narrowed immediately, and does not leak into public APIs, plugin result
  models, option models, diagnostics, or error structures.

#### Scenario: Casts follow validation

- **WHEN** `typing.cast` is needed because a checker cannot express an already
  validated invariant
- **THEN** the cast stays as close as possible to the validation and includes a
  clear reason when the invariant is not obvious.

#### Scenario: Type suppressions are exceptional

- **WHEN** type checking or linting appears inconvenient
- **THEN** the implementation does not use `# type: ignore`, does not use bare
  `# pyrefly: ignore`, avoids no-op checks such as `isinstance(value, object)`,
  and uses localized `# pyrefly: ignore[<rule>]` comments only for unavoidable
  Pyrefly limitations.

### Requirement: Callable ellipsis usage is explicitly justified

The system SHALL treat `Callable[..., ReturnType]`, broad `*args`, and broad
`**kwargs` annotations as intentionally opaque call surfaces, not general-purpose
shortcuts.

#### Scenario: Known callable parameters are precise

- **WHEN** production code, test helpers, fixtures, or type aliases describe a
  callable whose accepted parameters are known
- **THEN** the annotation uses a precise `Callable[[...], ReturnType]`, a named
  `Protocol`, PEP 695/ParamSpec forwarding where justified, or a concrete helper
  type instead of `Callable[..., ReturnType]`.

#### Scenario: Decorator forwarding remains possible

- **WHEN** decorator, wrapper, or pass-through adapter code preserves an
  arbitrary callable signature that cannot be expressed as a fixed parameter list
- **THEN** broad callable syntax is localized to that forwarding boundary and
  the surrounding type structure makes the intentional opacity clear.

### Requirement: Repository Python style rules are normative

The system SHALL follow repository Python style and naming rules when adding or
modifying code, including import ordering, type-only imports, export declaration
placement, and module organization.

#### Scenario: Imports use repository style

- **WHEN** Python modules import project code or type-only dependencies
- **THEN** they use absolute imports from the package root, avoid relative
  imports, keep runtime imports before any `if TYPE_CHECKING:` block, and do not
  interleave declarations between import groups.

#### Scenario: Public exports are explicit

- **WHEN** a public or package-internal module intentionally exports symbols
- **THEN** it declares a sorted literal `__all__` after imports and before other
  module declarations.

#### Scenario: Dynamic imports are exceptional

- **WHEN** repository-owned code can name an import target at development time
- **THEN** it uses ordinary static imports rather than `import_module`,
  `__import__`, or helper indirection that hides static dependencies.

#### Scenario: Direct attribute access is preferred

- **WHEN** code reads or writes known attributes
- **THEN** it uses direct attribute access or assignment instead of `getattr`,
  non-monkeypatch `setattr`, `__dict__` indexing, or namespace dictionary helper
  extraction.

### Requirement: Async boundaries are explicit

The system SHALL expose asynchronous implementations as the primary surface when
async behavior exists and SHALL make synchronous adapters explicit.

#### Scenario: Async implementation owns the primary name

- **WHEN** both asynchronous and synchronous forms of the same operation exist
- **THEN** the async implementation uses the primary unsuffixed operation name
  and the synchronous wrapper uses an explicit suffix such as `_sync` or an
  equally clear adapter name.

#### Scenario: Direct asyncio is justified

- **WHEN** project-owned async concurrency is added
- **THEN** it uses anyio task groups and anyio synchronization primitives by
  default, reserving direct asyncio for documented boundary cases.

### Requirement: Testing conventions are normative

The system SHALL follow repository testing conventions when adding, updating,
moving, splitting, or validating tests.

#### Scenario: Tests exercise behavior

- **WHEN** tests are added or updated
- **THEN** they assert behavior, invariants, error contracts, and integration
  boundaries rather than implementation trivia or default configuration strings.

#### Scenario: Tests preserve meaningful invalid states

- **WHEN** tests exercise invalid data or boundary validation
- **THEN** they pass raw invalid data through validation/parsing code or use
  precise helper types rather than casts, broad mocks, or impossible typed
  values that production code could not construct.

#### Scenario: Test grouping remains readable

- **WHEN** a test module covers multiple production functions, classes, public
  models, or behavior areas
- **THEN** tests use `Test<Subject>` grouping when it improves scanability and
  avoid base test classes, mutable shared state, hidden setup, and giant opaque
  autouse fixtures.

#### Scenario: Passing tests are quiet

- **WHEN** tests pass under default pytest arguments
- **THEN** they do not leave incidental stdout, stderr, or INFO-and-above log
  records that are not part of the asserted contract.

### Requirement: Repository validation commands are normative

The system SHALL treat the repository commands documented in `AGENTS.md` and
`pyproject.toml` as the required validation surface for completed work.

#### Scenario: Python changes run canonical validation

- **WHEN** source, tests, tooling, OpenSpec requirements, or quality policy
  change
- **THEN** validation uses the smallest relevant focused check first and then the
  canonical lint, format, type-check, and coverage-enabled test commands that
  apply to the changed surface.

#### Scenario: Ruff suppressions are exceptional

- **WHEN** Ruff reports a finding
- **THEN** the code is improved directly unless a localized, rule-specific
  suppression is demonstrably unavoidable and narrower than any practical
  alternative.

#### Scenario: Formatting is required validation

- **WHEN** Ruff validation is required
- **THEN** both format and lint validation are run; one is not a substitute for
  the other.

### Requirement: Module size and split criteria are enforceable

The system SHALL keep Python modules focused and SHALL treat oversized or
multi-responsibility modules as design problems.

#### Scenario: Large modules require split review

- **WHEN** a Python module under `src/` or `scripts/` reaches repository module
  size thresholds or accumulates unrelated responsibilities
- **THEN** the change either splits the module into responsibility-bearing owners
  or records a narrow split-review justification.

#### Scenario: Split names identify ownership

- **WHEN** a module is split
- **THEN** new modules use responsibility-bearing names rather than vague bucket
  names such as `helpers`, `utils`, or `common`.

### Requirement: Agent guidance mirrors specification rules

The system SHALL keep root and scoped `AGENTS.md` guidance aligned with OpenSpec
quality requirements so future sessions receive the same strict typing, testing,
style, validation-command, and suppression guidance.

#### Scenario: Quality policy changes update guidance

- **WHEN** an OpenSpec quality requirement changes contributor behavior
- **THEN** the applicable `AGENTS.md` guidance is updated or confirmed already
  equivalent before completion.

### Requirement: Strict typing escape hatches are flake8-diagnosable
The system SHALL provide flake8 diagnostics for strict typing escape hatches that repository policy already treats as exceptional, including broad dynamic annotations, unsafe casts, forbidden type suppressions, vague callable surfaces, and avoidable legacy type-parameter declarations.

#### Scenario: Quality validation can run through flake8
- **WHEN** repository validation runs flake8 with the `AGT` plugin enabled
- **THEN** strict typing escape-hatch violations are reported through flake8 diagnostics rather than a repository-specific script runner.

#### Scenario: Rule behavior mirrors strict typing policy
- **WHEN** production Python code introduces `Any`, broad `object`, `dict[str, object]`, `Callable[..., ReturnType]`, `typing.cast`, `# type: ignore`, bare `# pyrefly: ignore`, or avoidable legacy type-parameter declarations
- **THEN** the flake8 plugin reports diagnostics that map those syntax forms to the repository strict typing policy.

#### Scenario: Flake8 suppression remains standard
- **WHEN** a strict typing escape-hatch diagnostic is intentionally suppressed
- **THEN** suppression uses flake8-supported mechanisms such as exact-code `# noqa`, configured ignores, or per-file ignores rather than custom reason-required guard comments.

