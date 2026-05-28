# repository-quality-guardrails Specification

## Purpose

Define repository validation workflow and guidance-alignment requirements that are not already owned by AGT diagnostics, Ruff, Pyrefly, `module-size`, or a product capability spec.

## Requirements

### Requirement: Repository validation commands are normative

The system SHALL treat the repository commands documented in `AGENTS.md` and
`pyproject.toml` as the required validation surface for completed work, while
leaving detailed rule catalogs to the executable tools and product specs that own
them.

#### Scenario: Python changes run canonical validation

- **WHEN** source, tests, tooling, OpenSpec requirements, or quality policy
  change
- **THEN** validation uses the smallest relevant focused check first and then the
  canonical lint, format, type-check, flake8, module-size, and coverage-enabled
  test commands that apply to the changed surface.

#### Scenario: Tool findings are fixed at the source

- **WHEN** Ruff, Pyrefly, AGT flake8 diagnostics, module-size, or tests report a
  finding
- **THEN** the code, test, or documentation source is improved directly unless a
  localized and tool-supported suppression is demonstrably unavoidable.

#### Scenario: Formatting is required validation

- **WHEN** Ruff validation is required
- **THEN** both format and lint validation are run; one is not a substitute for
  the other.

### Requirement: Agent guidance mirrors canonical ownership

The system SHALL keep root and scoped `AGENTS.md` guidance aligned with OpenSpec
and executable validation ownership so future sessions receive the same workflow,
validation-command, and repository-orientation guidance without duplicated rule
catalogs.

#### Scenario: Quality policy changes update guidance

- **WHEN** an OpenSpec quality requirement changes contributor behavior
- **THEN** the applicable `AGENTS.md` guidance is updated or confirmed already
  equivalent before completion.

#### Scenario: Executable rule catalogs are not duplicated

- **WHEN** AGT, Ruff, Pyrefly, or module-size owns a detailed rule catalog
- **THEN** `AGENTS.md` refers to the owning check and canonical spec rather than
  repeating each diagnostic rule as contributor prose.
