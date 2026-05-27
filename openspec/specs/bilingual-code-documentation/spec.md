# bilingual-code-documentation Specification

## Purpose

Define English-first/Korean-second source documentation and reusable guardrail
requirements for public code documentation quality in `flake8_agents`.

## Requirements

### Requirement: Bilingual documentation format

Source-level documentation added under this policy SHALL use English-first and
Korean-second text for each documented concept.

#### Scenario: Docstring has both languages

- **WHEN** a covered docstring is added or materially rewritten
- **THEN** it presents the English description first and the Korean description
  second for the same concept.

#### Scenario: Attribute documentation has both languages

- **WHEN** a covered public attribute or constant uses declaration-adjacent
  documentation
- **THEN** the documentation includes English-first and Korean-second prose.

### Requirement: Covered documentation surfaces

The documentation policy SHALL classify source declarations as covered or
excluded before enforcing docstring requirements, and covered declarations SHALL
have readable declaration-site documentation.

#### Scenario: Public API is documented

- **WHEN** a public class, function, method, exception, option model, diagnostic
  model, or rule entrypoint is exported by `flake8_agents`
- **THEN** it has meaningful English-first/Korean-second documentation when the
  symbol can carry a Python docstring or declaration-adjacent attribute
  documentation.

#### Scenario: Private helpers are selectively documented

- **WHEN** a private helper encodes non-obvious policy, parsing, rule semantics,
  or performance-sensitive behavior
- **THEN** it has enough documentation to make the invariant maintainable even
  if it is not part of the public API.

### Requirement: Public contract attributes are documented

The documentation policy SHALL require public data attributes on exported
dataclasses, exceptions, and other explicit contract classes to use
declaration-adjacent attribute docstrings when the attribute is part of the
public API contract.

#### Scenario: Exception state is documented

- **WHEN** an exported exception exposes constructor-assigned public attributes
- **THEN** each public attribute has meaningful English-first/Korean-second
  documentation describing the state and caller contract.

#### Scenario: Dataclass field is documented

- **WHEN** an exported dataclass field is part of the public contract
- **THEN** the field has declaration-adjacent documentation that describes the
  field's purpose, not merely its type.

### Requirement: Constant attribute docstrings

The documentation policy SHALL require module-level constants, including private
constants with non-obvious policy meaning, to use declaration-adjacent attribute
docstrings.

#### Scenario: Policy constant explains intent

- **WHEN** a constant controls diagnostics, thresholds, rule codes, formatting,
  or guard behavior
- **THEN** nearby documentation explains the policy reason and uses
  English-first/Korean-second prose.

### Requirement: Meaningful bilingual documentation content

Covered documentation surfaces SHALL describe the documented symbol's actual
purpose, contract, parameters, return value, error behavior, or domain role.
Korean documentation MUST NOT be a generic placeholder.

#### Scenario: Placeholder documentation is rejected

- **WHEN** documentation repeats only the identifier, generic filler, or a
  mechanical phrase that does not describe the symbol's contract
- **THEN** it is treated as missing documentation.

### Requirement: Documentation guard avoids runtime imports

The repository SHALL provide or preserve a reusable guard that enforces covered
documentation policy without importing scanned application modules at guard
runtime.

#### Scenario: Guard scans source statically

- **WHEN** documentation validation runs against package source
- **THEN** it parses files statically and reports file, line, symbol, and missing
  or placeholder documentation category without executing package code.

### Requirement: Documentation-only changes preserve behavior

Documentation changes SHALL preserve runtime behavior unless a separate
behavioral requirement explicitly changes it.

#### Scenario: Docstrings do not change diagnostics

- **WHEN** documentation is added to checker, rule, or diagnostic code
- **THEN** flake8-visible rule behavior, options, exit codes, and diagnostic
  messages remain unchanged unless another requirement states otherwise.
