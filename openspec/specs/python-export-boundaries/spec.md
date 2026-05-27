# python-export-boundaries Specification

## Purpose

Define explicit Python module export surfaces, package re-export contracts,
cross-module import rules, private naming boundaries, test access policy, and
automated validation expectations for the `flake8_agents` package.

## Requirements

### Requirement: Python export surfaces are explicit

The system SHALL make each intentional Python module export surface explicit
through a sorted literal `__all__` placed as the first module declaration after
runtime and type-only imports, or through an implementation-private module policy
that intentionally exposes no cross-module API.

#### Scenario: Module exports are declared

- **WHEN** a module under `src/flake8_agents/` intentionally provides symbols to
  other modules, tests, or users
- **THEN** it declares a sorted literal `__all__` containing only the supported
  exported names.

#### Scenario: Private implementation module exports nothing

- **WHEN** a module is implementation-private and has no supported imports from
  outside its owning package seam
- **THEN** it declares `__all__ = []` or is covered by a documented validation
  exclusion for implementation-private modules.

### Requirement: Package re-exports are declared

The system SHALL declare package and subpackage re-export surfaces explicitly
instead of relying on incidental module attributes.

#### Scenario: Package facade re-exports symbols

- **WHEN** `flake8_agents` or a subpackage re-exports modules, classes, functions,
  constants, or lazy attributes
- **THEN** its `__init__.py` includes explicit sorted `__all__` entries for those
  supported names.

### Requirement: Cross-module imports use declared exports

Production modules SHALL import from project modules through declared export
surfaces unless an explicitly documented exception is needed for a local
implementation seam.

#### Scenario: Production import targets exported name

- **WHEN** a production module imports a project-owned symbol from another module
- **THEN** the provider module exports that symbol through its declared
  `__all__` surface.

#### Scenario: Private imports remain local

- **WHEN** a module imports a leading-underscore symbol or private module
- **THEN** the import is local to the owning package seam or documented as a
  narrow exception that cannot be expressed through a supported surface.

### Requirement: Leading underscores indicate true implementation privacy

The system SHALL reserve leading underscores for implementation-private symbols
whose consumers are local to the owning module or explicitly documented seam.

#### Scenario: Public behavior avoids underscore names

- **WHEN** a symbol is part of a supported public or package-internal contract
- **THEN** it uses a non-underscore name and is included in the provider export
  surface.

### Requirement: Tests prefer exported behavior boundaries

The test suite SHALL verify behavior through public or package-internal exported
surfaces by default and keep private-symbol access exceptional.

#### Scenario: Tests import through exported contract

- **WHEN** a test exercises behavior available through a supported module or
  package boundary
- **THEN** it imports through that exported boundary instead of reaching into
  private modules or leading-underscore symbols.

#### Scenario: Private access tests a private boundary contract

- **WHEN** a test must access a private symbol to verify a guardrail, import
  boundary, or intentionally private seam
- **THEN** the test name or nearby assertion makes the boundary contract clear.

### Requirement: Export-boundary policy is validated

The repository SHALL provide automated validation for export-boundary rules that
are not enforced by existing lint, format, type-check, or test commands.

#### Scenario: Export declaration is missing

- **WHEN** validation scans a module with intentional cross-module exports and no
  explicit `__all__`
- **THEN** validation reports the module and remediation guidance.

#### Scenario: Stale export is declared

- **WHEN** `__all__` contains a name that is no longer defined by the module or
  package facade
- **THEN** validation fails with the module path and stale name.

#### Scenario: Undeclared project import crosses a boundary

- **WHEN** repository code imports a project-owned symbol from another module
  that does not export the symbol
- **THEN** validation fails unless a documented exception covers that seam.

### Requirement: Public exports avoid redundant aliases

The system SHALL NOT include public or package-internal export names whose only
purpose is to alias another exported project symbol to the same runtime object.

#### Scenario: Compatibility-only alias is removed

- **WHEN** an alias exists solely to preserve an old import path or duplicate
  spelling for the same project-owned object
- **THEN** the alias and its export are removed rather than retained as a
  compatibility shim.

### Requirement: Shared constants and types have canonical owners

The system SHALL keep shared constants and type aliases in canonical owner
modules instead of duplicating declarations across behavior modules.

#### Scenario: Shared constant has one owner

- **WHEN** a constant is consumed by more than one production module or mirrored
  by tests
- **THEN** it is declared in a canonical owner module and imported from that
  owner through a declared export.

#### Scenario: Shared type alias has one owner

- **WHEN** a type alias is consumed across production module boundaries or
  mirrored by tests
- **THEN** it is declared once in a canonical owner module or package and not
  duplicated under legacy local names.

### Requirement: Retired paths are not compatibility surfaces

The system SHALL reject stale import paths after symbols move to canonical owner
modules and SHALL NOT preserve old paths through aliases, compatibility shims, or
deprecated re-export modules unless a current runtime requirement is specified.

#### Scenario: Retired path is unavailable

- **WHEN** a symbol moves to a canonical owner
- **THEN** tests or validation cover that the retired path is no longer the
  supported import surface.
