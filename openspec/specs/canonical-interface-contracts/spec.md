# canonical-interface-contracts Specification

## Purpose

Define canonical pre-release interface contracts for flake8 plugin inputs, rule
codes, diagnostic payloads, model fields, CLI options, and compatibility shim
removal.

## Requirements

### Requirement: Canonical plugin option names

Flake8 plugin option parsing SHALL accept only the canonical option names
documented for the current pre-release interface. Legacy aliases, alternate
spellings, and duplicate compatibility fields MUST NOT be accepted as equivalent
inputs unless a current external contract requires them.

#### Scenario: Canonical option accepted

- **WHEN** a user supplies a documented canonical option
- **THEN** the plugin parses it directly into the canonical internal option
  model.

#### Scenario: Legacy option rejected

- **WHEN** a removed or duplicate compatibility option spelling is supplied
- **THEN** the plugin rejects it or lets flake8 report it as unsupported rather
  than silently normalizing it.

### Requirement: Canonical diagnostic shape

Rule implementations SHALL produce the current diagnostic shape directly. Legacy
nested payloads, alternate tuple meanings, or duplicate message fields MUST NOT
be normalized behind the boundary.

#### Scenario: Diagnostic uses canonical fields

- **WHEN** a rule reports a violation
- **THEN** line, column, rule code, and message data are produced from canonical
  fields only.

### Requirement: Canonical rule codes

The package SHALL expose one canonical spelling for each rule code and SHALL NOT
preserve duplicate aliases for historical names.

#### Scenario: Rule code has one owner

- **WHEN** a rule code is shared across implementation, tests, and documentation
- **THEN** the code is declared in one canonical owner and imported from that
  owner.

### Requirement: Canonical model fields

Domain and transport models SHALL expose canonical field names only when a
legacy property exists solely as an alias for the same value.

#### Scenario: Legacy field alias removed

- **WHEN** a model field alias exists only to preserve an old spelling
- **THEN** the alias is removed and callsites use the canonical field.

### Requirement: Canonical CLI options

Optional CLI commands SHALL expose one canonical spelling for each option unless
a duplicate spelling has a current non-compatibility purpose.

#### Scenario: Duplicate CLI option removed

- **WHEN** a duplicate option is maintained only for legacy convenience
- **THEN** it is removed from the command surface and tests cover the canonical
  spelling.

### Requirement: Compatibility shim removal policy

The codebase SHALL remove compatibility shims, aliases, and fallback branches
unless they are documented as required for current runtime correctness rather
than historical compatibility.

#### Scenario: User-facing compatibility path removed

- **WHEN** a compatibility branch accepts a retired input or import path with no
  current contract requirement
- **THEN** the branch is removed and validation or tests cover the canonical
  path.

#### Scenario: Current runtime fallback is documented

- **WHEN** a fallback remains because it handles a current supported runtime or
  third-party behavior
- **THEN** the code documents the current reason and tests cover that branch.
