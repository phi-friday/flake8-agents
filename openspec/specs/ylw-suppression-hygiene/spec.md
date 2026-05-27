# suppression-hygiene Specification

## Purpose
The system SHALL audit explicit numeric AGT `# noqa` suppressions so stale or unmatched AGT codes are surfaced without affecting bare, digitless, or non-`AGT` suppressions.

## Requirements
### Requirement: Explicit AGT noqa suppressions are audited
The system SHALL report `AGT001` when an explicit inline `# noqa` comment names one or more numeric AGT suppression codes that do not match any raw AGT diagnostic on the applicable flake8-mapped line.

#### Scenario: Used exact AGT suppression is accepted
- **WHEN** Python source contains a AGT violation and an inline `# noqa: <AGT-code>` comment names that exact diagnostic code for the same flake8-mapped line
- **THEN** the checker does not report `AGT001` for that AGT suppression code.

#### Scenario: Unused exact AGT suppression is reported
- **WHEN** Python source contains an inline `# noqa: <AGT-code>` comment and the same flake8-mapped line has no raw AGT diagnostic matched by that suppression code
- **THEN** the checker reports `AGT001` at the suppression comment location.

#### Scenario: Mixed suppression list reports only stale AGT codes
- **WHEN** Python source contains an inline `# noqa` list with multiple numeric AGT codes and only some of those AGT codes match raw diagnostics on the applicable flake8-mapped line
- **THEN** the checker reports `AGT001` identifying the unmatched AGT codes without reporting the matched AGT codes.

#### Scenario: Non-AGT and digitless AGT suppression codes are not audited
- **WHEN** Python source contains an inline `# noqa` list with non-AGT codes or the digitless `AGT` family prefix
- **THEN** the checker does not use `AGT001` to report whether those suppression codes are used or unused.

### Requirement: AGT suppression matching follows flake8 code-prefix semantics
The system SHALL treat an explicit numeric AGT suppression code as used when it exactly equals a raw AGT diagnostic code or when a raw AGT diagnostic code starts with the suppression code.

#### Scenario: Numeric AGT family prefix suppresses a concrete AGT diagnostic
- **WHEN** Python source contains a raw `AGT105` diagnostic and an applicable inline `# noqa: AGT1` suppression
- **THEN** the checker treats the `AGT1` suppression code as used and does not report `AGT001` for it.

#### Scenario: AGT subfamily prefix suppresses a concrete AGT diagnostic
- **WHEN** Python source contains a raw `AGT105` diagnostic and an applicable inline `# noqa: AGT10` suppression
- **THEN** the checker treats the `AGT10` suppression code as used and does not report `AGT001` for it.

#### Scenario: Unmatched AGT prefix is reported
- **WHEN** Python source contains an inline `# noqa: AGT20` suppression and the applicable logical line has no raw diagnostic whose code starts with `AGT20`
- **THEN** the checker reports `AGT001` for the unused `AGT20` suppression code.

### Requirement: AGT noqa audit uses flake8 line placement
The system SHALL evaluate explicit inline AGT `# noqa` comments against the line mapping that flake8 uses when applying inline suppressions.

#### Scenario: Suppression on diagnostic line is accepted
- **WHEN** Python source places an explicit AGT `# noqa` comment on the line that flake8 checks for a matching raw AGT diagnostic
- **THEN** the checker treats the AGT suppression code as used and does not report `AGT001` for it.

#### Scenario: Unused suppression on mapped line is reported
- **WHEN** Python source places an explicit AGT `# noqa` comment on a flake8-mapped line and that mapped line has no matching raw AGT diagnostic
- **THEN** the checker reports `AGT001` at the suppression comment location.

### Requirement: Bare, digitless, and file-level noqa comments are outside AGT suppression hygiene
The system SHALL NOT report `AGT001` solely for bare inline `# noqa` comments, digitless `# noqa: AGT` comments, or file-level `# flake8: noqa` comments.

#### Scenario: Bare inline noqa is ignored by suppression hygiene
- **WHEN** Python source contains a bare inline `# noqa` comment without explicit numeric AGT codes
- **THEN** the checker does not report `AGT001` for that comment.

#### Scenario: Digitless AGT prefix is ignored by suppression hygiene
- **WHEN** Python source contains an inline `# noqa: AGT` comment without explicit numeric AGT codes
- **THEN** the checker does not report `AGT001` for that comment.

#### Scenario: File-level noqa is ignored by suppression hygiene
- **WHEN** Python source contains a file-level `# flake8: noqa` comment
- **THEN** the AGT suppression-hygiene capability does not define any `AGT001` diagnostic for that file-level comment.
