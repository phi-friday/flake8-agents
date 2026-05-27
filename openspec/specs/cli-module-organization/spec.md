# cli-module-organization Specification

## Purpose

Define how optional CLI production and test modules are organized so command
wiring, package entrypoints, and CLI-only adapters stay colocated under the CLI
package without leaking into core flake8 plugin rule modules.

## Requirements

### Requirement: CLI production modules are colocated

The system SHALL place CLI command wiring and CLI-only local workflow adapters
under the `flake8_agents.cli` package when such a package exists.

#### Scenario: CLI package owns command wiring

- **WHEN** a command entrypoint, option parser, display function, or CLI-only
  adapter is added
- **THEN** it lives under `flake8_agents.cli` rather than core rule, checker, or
  diagnostic modules.

#### Scenario: Module-size command wiring is CLI-owned

- **WHEN** the `module-size` command entrypoint, option parser, scanner
  orchestration, or display function is added
- **THEN** it lives under `flake8_agents.cli` rather than flake8 checker or rule
  modules.

### Requirement: CLI tests mirror CLI production modules

The system SHALL place CLI tests under `src/tests/cli/` and organize them by the
owning CLI production module or behavior area.

#### Scenario: CLI command tests are grouped under CLI tests

- **WHEN** tests exercise CLI command behavior
- **THEN** they live under `src/tests/cli/` with names that identify the owning
  command or display behavior.

#### Scenario: Module-size CLI tests are grouped under CLI tests

- **WHEN** tests exercise `module-size` command behavior
- **THEN** they live under `src/tests/cli/` with names that identify module-size
  CLI behavior.

### Requirement: Non-CLI runtime modules remain outside CLI package

The system SHALL keep rule implementations, checker integration, diagnostic
models, and plugin registration outside `flake8_agents.cli` unless they are
exclusively CLI-owned.

#### Scenario: Rule behavior remains package-owned

- **WHEN** both CLI and flake8 plugin code need the same rule behavior
- **THEN** the behavior lives in a non-CLI owner and the CLI imports it through a
  declared export.

### Requirement: CLI exception definitions are colocated with CLI package

The system SHALL place CLI-only service and orchestration exception definitions
under `flake8_agents.cli`.

#### Scenario: CLI exception is not shared globally

- **WHEN** an exception is raised and caught only by CLI code
- **THEN** it is defined in the CLI package rather than a shared package
  exception owner.

### Requirement: CLI shared constants have a canonical owner

The system SHALL place CLI-only shared defaults and display constants under a
canonical CLI-owned constant module when more than one CLI module or CLI test area
depends on them.

#### Scenario: Shared CLI constant has one source

- **WHEN** multiple CLI modules need the same option name, display width, or
  artifact path constant
- **THEN** they import it from the CLI canonical owner.

### Requirement: CLI display internals remain local

The system SHALL keep constants that only tune a single CLI formatting or display
function in the module that owns that behavior.

#### Scenario: Local display constant stays local

- **WHEN** a constant affects only one display function
- **THEN** it remains near that function instead of being moved to a broad shared
  constants module.
