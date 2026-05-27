# cli-logging-control Specification

## Purpose

Define CLI-local logging controls for command execution output and stream
behavior.

## Requirements

### Requirement: CLI local logging level controls

The CLI SHALL expose local console logging controls for command execution when a
CLI surface exists. Controls such as `--log-level`, `--verbose`, or `--debug`
SHALL configure command-local logging without changing package import behavior or
flake8 plugin diagnostics.

#### Scenario: Debug logging is opt-in

- **WHEN** a user runs a CLI command without debug or verbose logging controls
- **THEN** routine debug records are not emitted.

#### Scenario: Verbose logging increases detail

- **WHEN** a user enables verbose or debug logging
- **THEN** the CLI emits additional command-local diagnostic context without
  changing the command's semantic result.

### Requirement: CLI logging preserves command output streams

The CLI SHALL send local logging output to stderr and SHALL preserve stdout for
intentional command output.

#### Scenario: Structured command output remains on stdout

- **WHEN** a command intentionally writes machine-readable or table-shaped output
- **THEN** stdout contains that output without interleaved log records.

#### Scenario: Diagnostics use stderr

- **WHEN** a command emits progress, warnings, or debug logs
- **THEN** those records are written to stderr.

### Requirement: Logging changes preserve quiet tests

CLI logging SHALL not introduce incidental output in passing tests.

#### Scenario: Passing CLI tests are quiet

- **WHEN** CLI tests pass under default pytest capture settings
- **THEN** they do not leave unasserted stdout, stderr, or INFO-and-above log
  records.
