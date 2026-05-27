# cli-tabular-output Specification

## Purpose

Define readable, deterministic formatting requirements for optional `flake8-agents`
CLI outputs that are intentionally presented as row-and-column tables.

## Requirements

### Requirement: CLI table outputs use aligned columns

The system SHALL render every CLI output intentionally presented as a
row-and-column table with deterministic aligned columns instead of relying on
terminal tab stops.

#### Scenario: Table rows align

- **WHEN** a CLI command prints multiple rows of related values
- **THEN** column starts are deterministic for the rendered text.

### Requirement: CLI table formatting preserves semantic values

The system SHALL preserve semantic values displayed by table-shaped CLI commands
while changing only their tabular presentation.

#### Scenario: Values are unchanged

- **WHEN** table formatting changes
- **THEN** rule codes, paths, counts, option names, and other semantic values are
  not renamed or normalized unless another requirement explicitly changes them.

### Requirement: CLI table alignment is display-width aware

The system SHALL pad table cells using terminal display width so visually wide
characters do not misalign following columns in supported table outputs.

#### Scenario: Wide text does not break following columns

- **WHEN** a table cell contains wide Unicode text
- **THEN** following columns remain visually aligned in supported terminals.

### Requirement: Machine-readable output is not table-formatted

The system SHALL keep machine-readable output separate from human table
presentation.

#### Scenario: JSON output stays structural

- **WHEN** a command supports JSON or another machine-readable output format
- **THEN** it emits structural data directly rather than formatted table text.
