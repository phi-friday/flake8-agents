# layered-exception-organization Specification

## Purpose

Define where exception classes live across architectural layers and how they
remain dependency-light, typed, and behavior-preserving when organized by layer.

## Requirements

### Requirement: Exception modules are grouped by architectural layer

The system SHALL define reusable project exceptions only in approved exception
owner modules.

#### Scenario: Package exceptions have canonical owner

- **WHEN** an exception represents reusable `flake8_agents` package behavior
- **THEN** it lives in a canonical package exception owner module and is exported
  through that owner's `__all__` surface.

#### Scenario: CLI-only exceptions stay with CLI layer

- **WHEN** an exception is used only by an optional CLI or process adapter
- **THEN** it lives under the CLI-owned package area rather than a shared domain
  module.

#### Scenario: Rule exceptions stay near rule ownership

- **WHEN** an exception is private to one rule implementation or parser helper
- **THEN** it remains local to that owning module unless it becomes a reusable
  package contract.

### Requirement: Exception ownership guard rejects scattered reusable exceptions

Repository validation SHALL detect public reusable exception classes added
outside approved exception owner modules unless a documented OpenSpec
exception-owner exception applies.

#### Scenario: Reusable exception is scattered

- **WHEN** validation finds an exported exception class in an unapproved module
- **THEN** it reports the module and requires moving the class to the canonical
  owner or documenting a narrow exception.

### Requirement: Exception modules remain dependency-light

Exception modules SHALL avoid imports from runtime services, CLI command wiring,
rule implementations, parser implementations, and configuration model internals.
Code MAY import exception modules directly when it needs to raise or catch the
exception classes.

#### Scenario: Exception owner has no heavy runtime dependency

- **WHEN** an exception module is imported
- **THEN** it does not import flake8 plugin registration, AST scanning, CLI
  wiring, or other heavy runtime modules as a side effect.

### Requirement: Structured exception state is explicit where meaningful

Exception classes that represent reusable dynamic state SHALL expose that state
as typed attributes and SHALL render a stable message through initialization or
`__str__`.

#### Scenario: Dynamic state is typed

- **WHEN** an exception carries a rule code, option name, source location, or
  diagnostic context
- **THEN** those fields are typed attributes with documented meaning.

#### Scenario: Message is stable

- **WHEN** callers or tests rely on an exception message
- **THEN** the message is generated deterministically from explicit fields rather
  than incidental object representation.

### Requirement: Exception reorganization preserves behavior

The system SHALL preserve existing command output, validation outcomes, flake8
plugin behavior, and runtime exception semantics while moving exception
definitions.

#### Scenario: Import path cutover is clean

- **WHEN** an exception moves to a canonical owner before a stable public release
- **THEN** callsites and tests use the canonical path and no compatibility shim
  remains solely for the retired path.
