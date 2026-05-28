## ADDED Requirements

### Requirement: Import-boundary capability is canonical for AGT3xx behavior
The import-boundary flake8 rules capability SHALL be the canonical OpenSpec contract for AGT3xx import-boundary diagnostics, including private project imports, retired project import paths, and module import-section lifecycle ordering.

#### Scenario: Contributor guidance references AGT3xx contract
- **WHEN** repository guidance needs to mention import-boundary policies enforced by AGT3xx diagnostics
- **THEN** it references this capability and flake8 validation instead of duplicating the rule catalog.

#### Scenario: Import ordering policy remains tool-owned
- **WHEN** guidance or specs discuss import ordering after consolidation
- **THEN** Ruff-owned sorting remains outside AGT302, and AGT302 remains limited to import-section lifecycle ordering described by this capability.
