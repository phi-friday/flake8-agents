# import-boundary-flake8-rules Specification

## Purpose

Define file-local flake8 diagnostics for `flake8_agents` import-boundary violations, including private project imports, retired project import paths, and top-of-module import-section lifecycle ordering.
## Requirements
### Requirement: Import-boundary flake8 extension diagnostics
The system SHALL expose import-boundary rules as stable `AGT3xx` flake8 diagnostics through the installed `AGT` extension namespace.

#### Scenario: Import-boundary diagnostics use stable codes
- **WHEN** the checker reports an import-boundary violation
- **THEN** the diagnostic message begins with a stable `AGT3xx` code that flake8 can select, ignore, and suppress by code.

#### Scenario: Import-boundary rules run through installed flake8 plugin
- **WHEN** flake8 runs against Python source with `AGT` selected
- **THEN** the import-boundary checker participates in flake8's normal per-file checking pipeline.

### Requirement: Private project import diagnostics
The system SHALL report imports that cross into private `flake8_agents` modules or private symbols from project-owned modules.

#### Scenario: Private project module import is reported
- **WHEN** Python source imports a project module path containing a leading-underscore module component
- **THEN** the checker reports `AGT300` at the import statement.

#### Scenario: From-import from private project module is reported
- **WHEN** Python source imports any symbol from a project module path containing a leading-underscore module component
- **THEN** the checker reports `AGT300` at the import statement.

#### Scenario: Private project symbol import is reported
- **WHEN** Python source imports a leading-underscore symbol from a non-private project module path
- **THEN** the checker reports `AGT300` at the import statement.

#### Scenario: Dunder project symbol import is not private by name alone
- **WHEN** Python source imports a double-underscore symbol whose name both starts and ends with double underscores from a non-private project module path
- **THEN** the checker does not report `AGT300` solely because of that imported symbol name.

#### Scenario: Non-project private import is ignored
- **WHEN** Python source imports a private module or leading-underscore symbol from outside the `flake8_agents` package
- **THEN** the checker does not report a private project import diagnostic for that import.

### Requirement: Retired project import diagnostics
The system SHALL report imports from explicitly configured retired or banned `flake8_agents` module paths without discovering repository state dynamically.

#### Scenario: Retired project module import is reported
- **WHEN** Python source imports a project module path that exactly matches a configured retired import path
- **THEN** the checker reports `AGT301` at the import statement.

#### Scenario: Retired project submodule import is reported
- **WHEN** Python source imports a project module path below a configured retired import path
- **THEN** the checker reports `AGT301` at the import statement.

#### Scenario: No configured retired path is accepted
- **WHEN** Python source imports a project module path that is not configured as retired or below a retired path
- **THEN** the checker does not report a retired project import diagnostic for that import.

### Requirement: Module import section ordering diagnostics
The system SHALL report top-of-module import-section lifecycle ordering violations without enforcing Ruff-owned import sorting or post-import declaration ordering.

#### Scenario: Future import after declaration is reported
- **WHEN** Python source contains a `from __future__ import ...` statement after a non-import declaration
- **THEN** the checker reports `AGT302` at the future import statement.

#### Scenario: Runtime import after type-checking block is reported
- **WHEN** Python source contains a runtime import after a top-level `if TYPE_CHECKING:` block
- **THEN** the checker reports `AGT302` at the runtime import statement.

#### Scenario: Runtime import after declaration is reported
- **WHEN** Python source contains a runtime import after `__all__` or another non-import declaration
- **THEN** the checker reports `AGT302` at the runtime import statement.

#### Scenario: Type-checking block after declaration is reported
- **WHEN** Python source contains a top-level `if TYPE_CHECKING:` block after `__all__` or another non-import declaration
- **THEN** the checker reports `AGT302` at the type-checking block.

#### Scenario: Import sorting is not reported
- **WHEN** Python source contains imports that are alphabetically unsorted, grouped differently, or separated by Ruff-format-owned whitespace while remaining in a valid import-section lifecycle order
- **THEN** the checker does not report `AGT302` solely for sorting, grouping, or whitespace.

#### Scenario: Post-import declaration ordering is not reported
- **WHEN** Python source has completed the import section and `__all__` declaration and then declares globals, constants, classes, or functions in any order
- **THEN** the checker does not report `AGT302` solely for the order of those post-import declarations.

### Requirement: Import-boundary file-local deterministic analysis
The system SHALL implement import-boundary diagnostics as deterministic file-local analysis over flake8-provided source data, without requiring repository-defined pre-sorted checker iteration order for direct `run()` callers.

#### Scenario: No subprocess or repository traversal is required
- **WHEN** flake8 invokes the checker for a Python file
- **THEN** the import-boundary checker analyzes the file without invoking ast-grep, spawning subprocesses, reading provider modules, or traversing repository directories.

#### Scenario: Direct diagnostics contain expected violations
- **WHEN** a direct import-boundary checker invocation emits multiple import-boundary violations
- **THEN** the emitted diagnostics contain the expected codes, line numbers, column numbers, and messages without requiring a repository-defined sorted iteration order.

### Requirement: Import-boundary capability is canonical for AGT3xx behavior
The import-boundary flake8 rules capability SHALL be the canonical OpenSpec contract for AGT3xx import-boundary diagnostics, including private project imports, retired project import paths, and module import-section lifecycle ordering.

#### Scenario: Contributor guidance references AGT3xx contract
- **WHEN** repository guidance needs to mention import-boundary policies enforced by AGT3xx diagnostics
- **THEN** it references this capability and flake8 validation instead of duplicating the rule catalog.

#### Scenario: Import ordering policy remains tool-owned
- **WHEN** guidance or specs discuss import ordering after consolidation
- **THEN** Ruff-owned sorting remains outside AGT302, and AGT302 remains limited to import-section lifecycle ordering described by this capability.
