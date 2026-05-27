# performance-optimization-boundaries Specification

## Purpose

Define boundaries for local performance optimizations so improvements remain
request-scoped, deterministic, async-safe when applicable, and behavior-preserving.
## Requirements
### Requirement: Local performance structures remain request scoped

The system SHALL use lookup structures, sorted sequences, iterators, and
generators only within the bounded file, request, lifecycle, or command scope
that needs them, and MUST NOT introduce persistent caches unless a later
specification defines invalidation and capacity rules.

#### Scenario: Rule optimization uses bounded state

- **WHEN** a rule or checker builds a lookup table for one file or analysis pass
- **THEN** the structure is scoped to that file or pass and is released after the
  check completes.

#### Scenario: Persistent cache requires policy

- **WHEN** a performance change proposes a process-wide or cross-file cache
- **THEN** the change defines cache keys, invalidation, capacity, and correctness
  boundaries before implementation.

### Requirement: Generator use must remove materialization or clarify flow

The system SHALL use generators and comprehensions only where they reduce
unnecessary intermediate collections or make data flow clearer, and MUST NOT
treat a generator expression as an optimization when it still performs repeated
linear scans over the same collection.

#### Scenario: Repeated scan is not hidden

- **WHEN** code needs repeated membership or lookup over the same candidates
- **THEN** it uses an appropriate bounded set, mapping, or indexed structure
  instead of repeatedly scanning through generator syntax.

#### Scenario: Materialization is intentional

- **WHEN** code materializes a list, tuple, or mapping
- **THEN** the materialized collection is needed for reuse, ordering, stable
  diagnostics, or API shape.

### Requirement: Hot paths avoid avoidable allocation

Rule and checker hot paths SHALL avoid avoidable string allocation, copying, and
expensive recomputation when equivalent behavior can be expressed with existing
values or bounded precomputation.

#### Scenario: Diagnostic text is built once

- **WHEN** diagnostic text depends on a small set of known fields
- **THEN** the code avoids repeatedly constructing equivalent strings inside
  inner loops.

#### Scenario: Source line data is not copied unnecessarily

- **WHEN** a rule can inspect existing source, token, or AST data by reference
- **THEN** it avoids copying collections or substrings unless the copy is needed
  for correctness or stable ownership.

### Requirement: Async boundaries avoid event-loop blocking

When async code exists, the system SHALL keep synchronous file, subprocess,
parser, and CPU-heavy repository guard analysis out of hot async execution paths
unless explicitly run in a worker thread, isolated to CLI-only execution, or
replaced by a native command-scoped fast path.

#### Scenario: Synchronous analysis is isolated

- **WHEN** async orchestration needs synchronous per-file work
- **THEN** that work runs through bounded worker concurrency or remains outside
  the async runtime boundary.

### Requirement: Optimizations preserve behavior

Performance optimizations SHALL preserve public behavior, diagnostic ordering,
error messages that are part of the contract, exit codes, and validation results.

#### Scenario: Faster scan keeps deterministic diagnostics

- **WHEN** a scanner or guard is optimized
- **THEN** compliant inputs remain compliant, failing inputs still fail, and
  diagnostics stay deterministic and actionable.

### Requirement: Flake8 checker passes avoid redundant AST traversal

The system SHALL avoid redundant full-AST traversal inside a single flake8 file
check when equivalent diagnostics can be produced by an existing visitor pass or
bounded per-file precomputation.

#### Scenario: Aggregate checker performs bounded analysis
- **WHEN** the aggregate flake8 checker analyzes a Python file
- **THEN** each rule family uses only the AST passes needed for its diagnostics
  and MUST NOT add separate full-tree pre-walks for data that can be collected
  during its normal rule traversal.

#### Scenario: Import alias analysis stays local
- **WHEN** a checker needs import alias lookup data for one source file
- **THEN** the lookup data is built within that file's checker pass and released
  with the checker instance.

### Requirement: Flake8 checker optimizations preserve scope semantics

The system SHALL preserve Python lexical scope boundaries when replacing
repeated scans or lookup materialization in flake8 rule implementations.

#### Scenario: Nested scope assignments do not shadow outer calls
- **WHEN** an inner function, class, or lambda assigns a name that matches an
  imported typing helper or dynamic-call helper
- **THEN** checks in the containing outer scope still resolve the outer scope name
  according to the outer scope bindings.

#### Scenario: Overlapping shadowed names remain visible until their scope exits
- **WHEN** the same helper name is shadowed in nested scopes during a single
  checker traversal
- **THEN** leaving the inner scope MUST NOT remove the outer scope's shadowing
  state.

### Requirement: Flake8 checker diagnostics remain behavior-preserving

The system SHALL keep Flake8-facing diagnostic behavior stable while optimizing checker internals, while direct checker iteration order remains implementation-defined unless a narrower requirement explicitly owns that order.

#### Scenario: Optimized checker keeps diagnostic contract
- **WHEN** a file produces AGT diagnostics before the optimization
- **THEN** the optimized checker emits the same diagnostic codes, line numbers, column numbers, messages, and checker types for behaviorally equivalent cases.

#### Scenario: Flake8 report ordering remains source-location based
- **WHEN** multiple rule families emit diagnostics for the same file through Flake8
- **THEN** Flake8 reports diagnostics using its source-location ordering without requiring the checker to pre-sort direct `run()` iteration results.
