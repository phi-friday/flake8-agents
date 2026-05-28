## ADDED Requirements

### Requirement: Type-escape capability is canonical for AGT1xx behavior
The type-escape flake8 rules capability SHALL be the canonical OpenSpec contract for AGT1xx typing escape diagnostics, including forbidden type suppressions, unsafe casts, broad dynamic annotations, vague callable surfaces, legacy type-parameter diagnostics, and Self return-typing diagnostics.

#### Scenario: Contributor guidance references AGT1xx contract
- **WHEN** repository guidance needs to mention typing escape policies enforced by AGT1xx diagnostics
- **THEN** it references this capability and flake8 validation instead of duplicating the rule catalog.

