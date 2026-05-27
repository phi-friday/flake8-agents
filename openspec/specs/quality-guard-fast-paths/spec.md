# quality-guard-fast-paths Specification

## Purpose

Define repository guard optimization requirements that preserve policy outcomes
while allowing native and ast-grep-backed fast paths.

## Requirements

### Requirement: Quality guard fast paths preserve policy results

Repository quality guard optimizations SHALL preserve policy results, success and
failure exit codes, deterministic diagnostic ordering, and actionable diagnostic
content of existing guard entrypoints while replacing Python-heavy scanning work
with native or ast-grep-backed fast paths.

#### Scenario: Existing compliant fixture remains compliant

- **WHEN** an optimized guard scans a fixture or source tree that passed before
  the optimization
- **THEN** it still exits successfully with no new diagnostics.

#### Scenario: Existing violation remains a violation

- **WHEN** an optimized guard scans a fixture or source tree with a known
  violation
- **THEN** it exits non-zero and reports the same policy category and remediation
  guidance.

### Requirement: ast-grep dependency is reproducible

Repository quality guards that invoke ast-grep SHALL use a pinned development
dependency or documented repository-managed executable rather than relying on an
unpinned system installation.

#### Scenario: Developer environment is synced

- **WHEN** a developer syncs repository dependencies
- **THEN** guard commands that require ast-grep can resolve the expected version
  without manual global installation.

### Requirement: Candidate collection does not replace semantic validation

Optimized guards SHALL use ast-grep as the final authority only for purely
structural violations. Policies involving aliases, shadowing, allowlists, allow
comments, cross-file exports, stale comments, or runtime side-effect avoidance
SHALL keep Python semantic validation after candidate collection.

#### Scenario: Structural anti-pattern is reported from candidates

- **WHEN** ast-grep finds a purely structural anti-pattern that requires no
  cross-file context
- **THEN** the guard may report it directly if diagnostics remain deterministic.

#### Scenario: Export semantics remain Python-validated

- **WHEN** a guard checks whether imports target declared exports
- **THEN** ast-grep may collect candidates, but Python validation remains the
  authority for cross-file export semantics.

### Requirement: Native module-size scanning includes new worktree files

The module-size guard SHALL scan Python files that are tracked or
untracked-but-not-ignored under configured scan roots, so newly created modules
are subject to size policy before they are added to Git.

#### Scenario: Untracked Python module exceeds threshold

- **WHEN** a new untracked Python file under `src/` or `scripts/` exceeds the
  configured threshold
- **THEN** module-size validation reports it.

### Requirement: Multi-pattern structural candidate collection is batched

The repository SHALL execute quality guards that need more than one fixed
ast-grep structural pattern over the same file set through a single
command-scoped batched structural scan when batching preserves existing candidate
semantics and diagnostic results.

#### Scenario: Guard candidates share one scan

- **WHEN** a guard needs multiple independent structural candidates from the same
  files
- **THEN** it batches candidate collection rather than launching one subprocess
  per pattern, unless batching would change semantics.

### Requirement: Guard subprocess failures fail closed

Repository guard scripts SHALL treat Git, native line counting, ast-grep, or
other subprocess failures as incomplete candidate collection and therefore as a
guard failure rather than a successful scan.

#### Scenario: Candidate collection fails

- **WHEN** a subprocess used for guard candidate collection exits non-zero or
  returns malformed data
- **THEN** the guard exits non-zero and reports the collection failure.
