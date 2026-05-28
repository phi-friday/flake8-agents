## ADDED Requirements

### Requirement: Suppression-hygiene capability is canonical for AGT001 behavior
The suppression-hygiene capability SHALL be the canonical OpenSpec contract for `AGT001` unused explicit AGT `# noqa` diagnostics and their flake8 line-mapping behavior.

#### Scenario: Contributor guidance references AGT001 contract
- **WHEN** repository guidance needs to mention unused AGT `noqa` suppression behavior
- **THEN** it references this capability and flake8 validation instead of duplicating the matching rules.

