## ADDED Requirements

### Requirement: Anti-pattern capability is canonical for AGT2xx behavior
The anti-pattern flake8 rules capability SHALL be the canonical OpenSpec contract for AGT2xx dynamic anti-pattern diagnostics, including dynamic lookup, dynamic mutation, dynamic imports, construction bypasses, raw namespace access, and dotted import aliases.

#### Scenario: Contributor guidance references AGT2xx contract
- **WHEN** repository guidance needs to mention dynamic anti-pattern policies enforced by AGT2xx diagnostics
- **THEN** it references this capability and flake8 validation instead of duplicating the rule catalog.

#### Scenario: Duplicate dynamic policy text is removed
- **WHEN** another active spec or `AGENTS.md` restates AGT2xx dynamic anti-pattern syntax as repository policy
- **THEN** implementation removes that duplicate text unless it describes behavior not covered by this capability.
