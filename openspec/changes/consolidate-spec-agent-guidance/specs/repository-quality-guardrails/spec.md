## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: Strict typing rules are normative
**Reason**: Detailed strict typing escape-hatch behavior is now owned by Pyrefly configuration and the AGT type-escape flake8 rule contract.
**Migration**: Use `type-escape-flake8-rules`, `pyrefly.toml`, and validation commands documented in `AGENTS.md`.

### Requirement: Callable ellipsis usage is explicitly justified
**Reason**: Vague callable behavior is enforced and specified through AGT type-escape diagnostics.
**Migration**: Use `type-escape-flake8-rules` for `AGT104` behavior and run flake8 validation.

### Requirement: Repository Python style rules are normative
**Reason**: Import ordering, formatting, and many style constraints are owned by Ruff, Pyrefly, AGT import-boundary diagnostics, and concise `AGENTS.md` conventions.
**Migration**: Use `AGENTS.md`, `ruff.toml`, `pyrefly.toml`, and `import-boundary-flake8-rules`.

### Requirement: Async boundaries are explicit
**Reason**: This broad policy is not a current product capability and is too general for persistent OpenSpec after consolidation.
**Migration**: Keep async expectations in design docs for changes that introduce async behavior.

### Requirement: Testing conventions are normative
**Reason**: Test workflow belongs in scoped agent guidance unless it changes user-visible product behavior.
**Migration**: Use `src/tests/AGENTS.md` for test organization and validation guidance.

### Requirement: Module size and split criteria are enforceable
**Reason**: Line-count behavior is owned by the `module-size-cli` product contract and command configuration.
**Migration**: Use `module-size-cli` and the configured Poe tasks for module-size validation.

### Requirement: Strict typing escape hatches are flake8-diagnosable
**Reason**: The requirement duplicates the AGT type-escape flake8 product contract.
**Migration**: Use `type-escape-flake8-rules` as the canonical behavior specification.
