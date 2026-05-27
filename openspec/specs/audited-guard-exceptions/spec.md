# audited-guard-exceptions Specification

## Purpose

Define repository guard exception handling and diagnostics so suppression is
explicit, structured, narrow, and auditable.
## Requirements
### Requirement: Inline guard allow comments are structured and narrow

Repository guard scripts that support source-local suppressions SHALL recognize
only structured inline allow comments with the grammar
`# guard: allow <guard-id>/<category> because <reason>`, where the guard id
and category identify the exact policy being waived and the reason is non-empty.

#### Scenario: Structured allow comment is accepted

- **WHEN** a guard finding appears on a line with a matching structured allow
  comment for the same guard id and category
- **THEN** the guard may suppress that finding and SHALL keep the exception
  visible at the decision point.

#### Scenario: Loose suppression text is ignored

- **WHEN** source contains vague phrases such as `raw namespace`,
  `non-contract`, `implementation-only`, `ignore`, or `allowed` without the
  structured grammar
- **THEN** the guard does not use that phrase to suppress a finding.

#### Scenario: Wrong category does not suppress

- **WHEN** a structured allow comment names a different guard id or finding
  category from the current diagnostic
- **THEN** the current diagnostic is still reported.

### Requirement: Central guard allowlists are exact and reasoned

Repository guard scripts that use central allowlists or rationale maps SHALL
represent each exception as a typed audited entry containing the subject being
allowed, finding category or policy boundary, exact matching context, and a
non-empty reason.

#### Scenario: Central exception matches exactly

- **WHEN** a central allowlist entry matches the current path, symbol, category,
  and syntax context
- **THEN** the guard may suppress that finding and SHALL keep the rationale in
  the policy location.

#### Scenario: Stale central exception fails

- **WHEN** a central allowlist entry no longer matches a current finding or
  policy subject
- **THEN** validation fails with a stale exception diagnostic.

### Requirement: Guard exception diagnostics are actionable

Repository guard exception diagnostics SHALL include enough information for a
maintainer to locate the exception, identify the guard and category, and decide
whether to remove, move, or rewrite it.

#### Scenario: Diagnostic identifies decision point

- **WHEN** a guard reports an invalid, stale, or unused exception
- **THEN** the diagnostic includes the file, line when available, guard id,
  category, and remediation guidance.

#### Scenario: Guard fails closed on invalid policy

- **WHEN** a guard cannot parse allow comments, central policy entries, or the
  source required to decide whether an exception applies
- **THEN** it exits non-zero rather than treating the scan as successful.

### Requirement: Flake8 plugin suppressions remain flake8-native
The system SHALL NOT require audited repository guard exception comments or central allowlist entries for diagnostics emitted by the reusable flake8 plugin.

#### Scenario: No reason-required comment for flake8 suppression
- **WHEN** a user suppresses a `AGT` diagnostic using `# noqa: <AGT-code>` or flake8 configuration
- **THEN** the flake8 plugin accepts the standard flake8 suppression path without requiring a `guard: allow ... because ...` comment.

#### Scenario: Repository guard scripts may keep audited exceptions
- **WHEN** a separate repository guard script supports source-local or central audited exceptions
- **THEN** the audited exception requirements for that script remain governed by the repository guard exception specification.

