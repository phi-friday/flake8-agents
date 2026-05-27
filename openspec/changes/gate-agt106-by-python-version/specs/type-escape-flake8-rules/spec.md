## MODIFIED Requirements

### Requirement: Legacy type-parameter diagnostics
The system SHALL report avoidable module-level legacy `TypeVar`, `ParamSpec`, and `TypeVarTuple` usage in repository-owned code only when the Python version used for analysis supports native type parameter syntax.

#### Scenario: Legacy type-parameter import is reported on native-generic Python
- **WHEN** Python source imports `TypeVar`, `ParamSpec`, or `TypeVarTuple` from `typing` or `typing_extensions`, the import is used for legacy declarations, and the analysis Python version is 3.12 or newer
- **THEN** the checker reports a legacy-type-parameter diagnostic.

#### Scenario: Legacy type-parameter assignment is reported on native-generic Python
- **WHEN** a module-level assignment calls `TypeVar`, `ParamSpec`, or `TypeVarTuple` through an imported or qualified typing name and the analysis Python version is 3.12 or newer
- **THEN** the checker reports a legacy-type-parameter diagnostic at the declaration.

#### Scenario: Legacy type-parameter assignment is accepted before native-generic Python
- **WHEN** a module-level assignment calls `TypeVar`, `ParamSpec`, or `TypeVarTuple` through an imported or qualified typing name and the analysis Python version is earlier than 3.12
- **THEN** the checker does not report a legacy-type-parameter diagnostic for that declaration.

#### Scenario: Shadowed factory is not reported
- **WHEN** the apparent legacy type-parameter factory name is shadowed by a local declaration before use
- **THEN** the checker does not report that shadowed name as a typing factory.
