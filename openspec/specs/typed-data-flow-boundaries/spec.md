# typed-data-flow-boundaries Specification

## Purpose

Define named, typed data-flow boundaries for flake8 plugin options, parsed source
state, rule diagnostics, and serialized/reportable outputs so each data shape has
one clear owner.

## Requirements

### Requirement: Named data-flow boundaries

The system SHALL define named boundaries for option loading, checker state,
rule-domain data, diagnostics, and user-facing output so each data shape has one
clear owner.

#### Scenario: Boundary owner is clear

- **WHEN** a new data shape is introduced
- **THEN** its owner is identifiable from the module and type name, and callers
  do not pass anonymous broad dictionaries between layers.

### Requirement: External input and internal models are distinct

The system SHALL model externally supplied inputs separately from validated
internal domain values.

#### Scenario: Flake8 option input is validated

- **WHEN** command-line, configuration, or flake8-provided option values enter
  the package
- **THEN** parse-boundary code validates and normalizes them before passing
  precise internal types to rule code.

#### Scenario: AST and token data are wrapped intentionally

- **WHEN** Python AST, token, line, or flake8 framework data needs additional
  repository-owned semantics
- **THEN** the code introduces precise wrapper or result types rather than
  spreading ad-hoc tuples and mappings through the package.

### Requirement: Strict production typing at boundaries

The system SHALL keep broad dynamic types local to true external boundaries and
SHALL NOT leak them into production checker logic, rule implementations,
diagnostic models, or public APIs.

#### Scenario: Broad parse value is narrowed

- **WHEN** a parse boundary receives an untyped value from flake8, Python parser
  APIs, or another third-party API
- **THEN** the value is checked, converted, or rejected before it reaches domain
  code.

#### Scenario: Diagnostic payload is explicit

- **WHEN** a rule produces a violation
- **THEN** it returns or yields a precise diagnostic type or documented tuple
  shape rather than a broad mapping or partially typed container.

### Requirement: Practical immutability for shared models

The system SHALL make shared boundary models practically immutable when mutation
would make rule evaluation order-dependent or hard to reason about.

#### Scenario: Shared nested collections are immutable

- **WHEN** a boundary type is intended to be reused across rule checks
- **THEN** nested collections use immutable containers such as tuples or mapping
  proxies, or mutation remains local to construction.

### Requirement: Explicit serialization adapters

The system SHALL convert internal domain models to flake8-compatible result
values, console output, or JSON-compatible payloads through explicit adapters
rather than ad-hoc construction spread across modules.

#### Scenario: Domain diagnostic adapts to flake8 tuple

- **WHEN** a checker must yield a flake8-compatible result
- **THEN** conversion from internal diagnostic fields to the framework result
  shape happens at the checker boundary.

### Requirement: Safe boundary errors

The system SHALL report option parsing, source parsing, rule evaluation, and
serialization errors with enough context to diagnose the invalid boundary while
avoiding noisy tracebacks for expected user input failures.

#### Scenario: Invalid option identifies boundary

- **WHEN** user configuration is invalid
- **THEN** the error identifies the option and invalid value category without
  exposing unrelated internal state.

### Requirement: Shared aliases have canonical owners

The system SHALL define each type alias consumed across production module
boundaries or mirrored by tests in one canonical owner.

#### Scenario: Alias is reused from owner

- **WHEN** multiple modules need the same diagnostic, location, option, or AST
  helper type alias
- **THEN** they import it from the canonical owner instead of redeclaring local
  aliases.

### Requirement: Legacy aliases are removed after canonicalization

The system SHALL remove redundant type alias declarations whose only purpose is
to preserve an old local name for a canonical shared alias.

#### Scenario: Old local alias disappears

- **WHEN** a shared alias is moved to its canonical owner
- **THEN** old aliases and compatibility exports are removed with affected
  callsites updated to the canonical name.
