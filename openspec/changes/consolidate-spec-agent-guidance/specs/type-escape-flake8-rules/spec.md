## ADDED Requirements

### Requirement: Type-escape capability is canonical for AGT1xx behavior
The type-escape flake8 rules capability SHALL be the canonical OpenSpec contract for AGT1xx typing escape diagnostics, including forbidden type suppressions, unsafe casts, broad dynamic annotations, vague callable surfaces, legacy type-parameter diagnostics, and Self return-typing diagnostics.

#### Scenario: Contributor guidance references AGT1xx contract
- **WHEN** repository guidance needs to mention typing escape policies enforced by AGT1xx diagnostics
- **THEN** it references this capability and flake8 validation instead of duplicating the rule catalog.

#### Scenario: Standalone Self typing policy is retired
- **WHEN** the standalone `self-return-typing` capability is removed during consolidation
- **THEN** avoidable concrete return annotations for subtype-preserving classmethod factories remain specified by this capability's Self return typing diagnostics requirement.
