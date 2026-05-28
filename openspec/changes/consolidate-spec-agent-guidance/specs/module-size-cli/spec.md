## MODIFIED Requirements

### Requirement: Module-size scans use async orchestration and worker-thread file reads

The module-size CLI SHALL expose an async scan API for module-size scans. The
synchronous console-script entry point SHALL adapt to that async implementation.
Blocking filesystem discovery and physical line counting SHALL run in worker
threads so scanning many files does not serialize all blocking file I/O on the
event loop. Concurrent line-count scheduling SHALL remain bounded and compatible
with the repository's supported Python versions.

#### Scenario: Async scan API can be awaited

- **WHEN** repository code calls the module-size scan API from an async context
- **THEN** it can await the scan without invoking the console-script adapter.

#### Scenario: Physical line reads are thread-offloaded

- **WHEN** the async scanner counts physical lines for scanned Python files
- **THEN** blocking line-count reads run through worker-thread offloading rather
  than directly on the event loop.

#### Scenario: Line-count concurrency is bounded

- **WHEN** the async scanner schedules line-count work for scanned Python files
- **THEN** it uses bounded command-scoped concurrency without requiring APIs that
  are unavailable on supported Python versions.

## ADDED Requirements

### Requirement: Module-size capability owns CLI presentation contract
The module-size CLI capability SHALL own the active human-readable output contract for `module-size`, including deterministic finding order, displayed columns, output streams, and warning suppression behavior.

#### Scenario: Separate table-formatting capability is retired
- **WHEN** stale CLI table-formatting specs are removed during consolidation
- **THEN** `module-size-cli` still specifies the active `module-size` finding output contract.

#### Scenario: Unsupported CLI help and logging specs are not active contracts
- **WHEN** specs describing colorized help, no-color handling, verbose logging, or debug logging are not implemented by the current CLI
- **THEN** those specs are removed or archived rather than treated as current `module-size` requirements.
