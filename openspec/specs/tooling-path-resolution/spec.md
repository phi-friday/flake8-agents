# tooling-path-resolution Specification

## Purpose

Define repository tooling path-resolution rules so fixed repository-owned paths
remain file-anchored and stable while caller-selected Git worktree discovery stays
limited to command paths that explicitly require it.

## Requirements

### Requirement: Fixed tooling paths use constants

Repository tooling tests SHALL represent fixed repository-owned paths as
module-level constants instead of helper functions that return the same path on
every call.

#### Scenario: Static script path is constant

- **WHEN** a test or script needs a fixed path to a repository-owned file
- **THEN** it uses a named module-level constant derived from the owning file's
  location.

### Requirement: Repository-owned paths are file-anchored

Repository tooling SHALL derive paths to repository-owned scripts and files from
the owning file's resolved location unless caller-selected Git worktree behavior
is explicitly required.

#### Scenario: Tool finds repository file from owner

- **WHEN** a repository script needs to locate `src/`, `scripts/`, `openspec/`,
  or a configuration file
- **THEN** it resolves the path relative to the script or module file that owns
  the tool.

#### Scenario: Caller-selected worktree is explicit

- **WHEN** a command intentionally operates on a caller-selected worktree or scan
  root
- **THEN** that path is accepted through an explicit argument and not inferred by
  walking unrelated parent directories.

### Requirement: Existing guard behavior is preserved

Path-resolution cleanup SHALL preserve existing guard behavior, command-line
contracts, and validation outputs.

#### Scenario: Path cleanup does not change diagnostics

- **WHEN** a path-resolution implementation is simplified
- **THEN** the same valid inputs pass, the same invalid inputs fail, and reported
  paths remain understandable to the caller.
