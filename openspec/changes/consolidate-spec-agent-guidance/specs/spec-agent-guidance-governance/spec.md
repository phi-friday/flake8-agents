## ADDED Requirements

### Requirement: Persistent specs describe current contracts
Persistent OpenSpec capabilities SHALL describe current product behavior, current repository-maintenance contracts, or explicit change proposals, and SHALL NOT preserve stale requirements for absent tooling surfaces or historical implementation phases.

#### Scenario: Obsolete capability is removed from active specs
- **WHEN** a persistent spec describes a guard script, CLI option, validation command, or documentation policy that the current repository does not implement and this change does not intend to implement
- **THEN** the capability is removed or archived rather than retained as an active requirement.

#### Scenario: Product behavior remains specified
- **WHEN** a capability describes user-visible AGT flake8 diagnostics or `module-size` CLI behavior that remains implemented
- **THEN** the capability remains in persistent OpenSpec as the canonical product contract.

### Requirement: Executable checks own low-level rule catalogs
The repository SHALL treat AGT diagnostics, Ruff, Pyrefly, and `module-size` validation as the executable source of truth for low-level syntax, typing, anti-pattern, import-boundary, formatting, and module-size enforcement.

#### Scenario: Agent guidance avoids diagnostic catalog duplication
- **WHEN** root or scoped `AGENTS.md` guidance references policies already enforced by AGT, Ruff, Pyrefly, or `module-size`
- **THEN** the guidance points maintainers to the executable check and canonical product spec instead of restating every forbidden syntax form or diagnostic scenario.

#### Scenario: Product specs retain diagnostic behavior
- **WHEN** an executable check exposes user-visible behavior such as an AGT code, line placement rule, CLI option, output field, or exit-code contract
- **THEN** the relevant product spec describes that behavior with scenarios.

### Requirement: Agent guidance remains operational
Root and scoped `AGENTS.md` files SHALL focus on repository orientation, codebase conventions not fully represented by tool configuration, validation commands, and pointers to canonical specs.

#### Scenario: Guidance update removes duplicated policy text
- **WHEN** implementation updates `AGENTS.md` during this consolidation
- **THEN** duplicated rule catalogs and stale guard-script instructions are removed while repository-specific commands and directory guidance remain available.

#### Scenario: Scoped test guidance remains useful
- **WHEN** implementation updates `src/tests/AGENTS.md`
- **THEN** test organization, focused validation, and behavior-testing guidance remain available without duplicating AGT type-escape or anti-pattern rule catalogs.
