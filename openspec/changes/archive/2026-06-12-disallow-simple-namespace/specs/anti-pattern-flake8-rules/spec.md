## ADDED Requirements

### Requirement: SimpleNamespace dynamic namespace diagnostics
The system SHALL report stdlib `types.SimpleNamespace` use as a dynamic namespace anti-pattern because it exposes arbitrary mutable attributes and `Any`-typed member access.

#### Scenario: Direct SimpleNamespace construction is reported
- **WHEN** Python source imports `SimpleNamespace` from `types` and calls the imported name or its alias
- **THEN** the checker reports `AGT212` at the call site.

#### Scenario: Qualified SimpleNamespace construction is reported
- **WHEN** Python source imports `types` and calls `types.SimpleNamespace(...)` or the same attribute through a `types` module alias
- **THEN** the checker reports `AGT212` at the call site.

#### Scenario: SimpleNamespace annotations are reported
- **WHEN** Python source uses an annotation that resolves to stdlib `types.SimpleNamespace` in a parameter, return annotation, variable annotation, or type alias value
- **THEN** the checker reports `AGT212` at the annotation site.

#### Scenario: SimpleNamespace string annotations are reported when resolvable
- **WHEN** Python source uses a string-literal annotation expression that resolves to an imported stdlib `types.SimpleNamespace` name or qualified module attribute
- **THEN** the checker reports `AGT212` at the string annotation site without evaluating the annotation.

#### Scenario: Local SimpleNamespace shadowing is accepted
- **WHEN** Python source defines or binds a local `SimpleNamespace` name that shadows the stdlib import before the name is called or annotated
- **THEN** the checker does not report `AGT212` for that shadowed local name.

#### Scenario: Import-only SimpleNamespace references are accepted
- **WHEN** Python source imports `types.SimpleNamespace` but does not construct or annotate with it
- **THEN** the checker does not report `AGT212` for the import statement alone.

#### Scenario: Structured alternatives are accepted
- **WHEN** Python source uses dataclasses, `NamedTuple`, or `TypedDict` to model explicit field shapes
- **THEN** the checker does not report `AGT212` for those structured alternatives.
