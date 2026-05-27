# freethread-script-guard-concurrency Specification

## Purpose

Define concurrency requirements for repository guard scripts that offload
synchronous per-file analysis while preserving async-first orchestration,
deterministic diagnostics, and bounded resource use.

## Requirements

### Requirement: Freethread guard scans offload synchronous analysis

Freethread-enabled repository guard scripts SHALL keep deterministic command
orchestration as the primary command flow while executing synchronous per-file
analysis through bounded worker threads or replacing that Python work with
command-scoped native or ast-grep-backed fast paths that preserve diagnostics.

#### Scenario: Per-file analysis is bounded

- **WHEN** a guard analyzes many Python files with synchronous parsing or source
  inspection
- **THEN** independent per-file work runs through bounded worker concurrency or a
  native fast path rather than an unbounded task fan-out.

#### Scenario: Semantic validation still owns policy

- **WHEN** guard policy depends on allowlists, aliases, cross-file state, or
  stale exception detection
- **THEN** concurrency changes do not bypass that semantic validation.

### Requirement: Threaded guard output remains deterministic

Freethread-enabled repository guard scripts SHALL produce diagnostics in
deterministic order independent of worker scheduling order.

#### Scenario: Diagnostics are sorted after concurrent work

- **WHEN** worker threads report findings in nondeterministic completion order
- **THEN** the command sorts or otherwise stabilizes diagnostics before printing
  them and choosing the exit status.

### Requirement: Worker concurrency is bounded and command scoped

Freethread-enabled repository guard scripts SHALL use finite, command-scoped
worker concurrency and MUST NOT introduce persistent worker pools, global queues,
or caches that outlive one guard invocation.

#### Scenario: Worker count is finite

- **WHEN** a guard accepts or computes worker concurrency
- **THEN** the value is positive, finite, and constrained to the command scope.

#### Scenario: No persistent guard state

- **WHEN** a guard command exits
- **THEN** no worker pool, queue, or analysis cache remains for a future command
  invocation.

### Requirement: CLI contracts are preserved after threaded refactor

Freethread-enabled repository guard scripts SHALL preserve supported arguments,
success exit codes, failure exit codes, and diagnostic text contracts after a
threaded or fast-path refactor.

#### Scenario: Same failure remains failing

- **WHEN** a pre-refactor fixture or source tree fails a guard policy
- **THEN** the threaded or fast-path implementation exits non-zero for the same
  policy reason.

#### Scenario: Same success remains successful

- **WHEN** a pre-refactor fixture or source tree passes a guard policy
- **THEN** the threaded or fast-path implementation exits successfully.
