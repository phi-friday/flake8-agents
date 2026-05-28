## ADDED Requirements

### Requirement: Suppression-hygiene capability is canonical for AGT001 behavior
The suppression-hygiene capability SHALL be the canonical OpenSpec contract for `AGT001` unused explicit AGT `# noqa` diagnostics and their flake8 line-mapping behavior.

#### Scenario: Contributor guidance references AGT001 contract
- **WHEN** repository guidance needs to mention unused AGT `noqa` suppression behavior
- **THEN** it references this capability and flake8 validation instead of duplicating the matching rules.

#### Scenario: Non-flake8 guard exception policy is not required for AGT suppressions
- **WHEN** a user suppresses an AGT diagnostic through flake8-supported mechanisms
- **THEN** this capability remains the only persistent AGT suppression-hygiene contract and no separate guard exception policy is required.

### Requirement: Suppression-hygiene naming is AGT-specific
The active suppression-hygiene capability SHALL identify itself as AGT suppression hygiene so maintainers do not confuse it with unrelated repository guard exception policies.

#### Scenario: Capability title is clarified
- **WHEN** implementation updates the suppression-hygiene spec during consolidation
- **THEN** the title and purpose use AGT-specific wording even if the existing capability directory name is preserved for OpenSpec continuity.
