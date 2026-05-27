# type-escape-flake8-rules Specification

## Purpose
TBD - created by archiving change add-type-escape-flake8-plugin. Update Purpose after archive.
## Requirements
### Requirement: Flake8 extension registration
The system SHALL expose repository `AGT` rule families, including the existing type-escape rules and import-boundary rules, as an installed flake8 extension under the `AGT` diagnostic namespace.

#### Scenario: Installed plugin is selected by flake8
- **WHEN** flake8 runs against Python source with `AGT` selected
- **THEN** the installed checker participates in flake8's normal per-file checking pipeline for each enabled `AGT` rule family.

#### Scenario: Diagnostics use stable code prefixes
- **WHEN** the checker reports a violation
- **THEN** the message begins with a stable `AGT` diagnostic code that flake8 can select, ignore, and suppress by code.

#### Scenario: One entry point owns the AGT namespace
- **WHEN** the package registers flake8 extensions
- **THEN** a single installed `AGT` entry point owns the repository's `AGT` diagnostic namespace without registering overlapping `AGT` prefixes.

### Requirement: Standard flake8 suppression semantics
The system SHALL rely on flake8-native suppression and configuration behavior rather than custom reason-required guard comments or central allowlists for repository `AGT` diagnostics. Explicit inline AGT `# noqa` suppressions SHALL remain standard flake8 suppressions, and stale explicit AGT suppression codes SHALL be audited by the AGT suppression-hygiene capability.

#### Scenario: Inline noqa suppresses matching diagnostic
- **WHEN** a source line contains a `AGT` violation and a matching `# noqa: <AGT-code>` suppression
- **THEN** flake8 suppresses that diagnostic through its standard suppression path.

#### Scenario: Per-file ignore suppresses matching diagnostic
- **WHEN** flake8 configuration ignores a matching `AGT` code for a file
- **THEN** the plugin does not require any additional repository-specific allow comment for that diagnostic to be suppressed.

#### Scenario: Reason comments are not required
- **WHEN** a user suppresses a `AGT` diagnostic through flake8-supported configuration or `# noqa`
- **THEN** the plugin does not require a `because` reason or `guard: allow` comment.

#### Scenario: Explicit stale AGT noqa is audited
- **WHEN** a user leaves an explicit inline `# noqa: <AGT-code>` suppression that no longer suppresses a matching raw AGT diagnostic
- **THEN** the plugin reports the stale AGT suppression through the AGT suppression-hygiene diagnostic rather than requiring a custom suppression mechanism.

### Requirement: Type suppression diagnostics
The system SHALL report forbidden type-checker suppression comments as flake8 diagnostics.

#### Scenario: Type ignore is reported
- **WHEN** Python source contains `# type: ignore` with or without bracketed codes
- **THEN** the checker reports a type-suppression diagnostic at the comment line.

#### Scenario: Bare pyrefly ignore is reported
- **WHEN** Python source contains `# pyrefly: ignore` without exact bracketed diagnostic names
- **THEN** the checker reports a type-suppression diagnostic at the comment line.

#### Scenario: Rule-qualified pyrefly ignore is accepted
- **WHEN** Python source contains `# pyrefly: ignore[<diagnostic>]` with exact diagnostic names
- **THEN** the checker does not report a type-suppression diagnostic for that comment.

### Requirement: Unsafe cast diagnostics
The system SHALL report `typing.cast` calls and imported or aliased `cast` calls that bypass ordinary narrowing.

#### Scenario: Imported cast is reported
- **WHEN** Python source imports `cast` from `typing` or `typing_extensions` and calls that imported name
- **THEN** the checker reports an unsafe-cast diagnostic at the call site.

#### Scenario: Qualified typing cast is reported
- **WHEN** Python source calls `typing.cast`, an alias for `typing.cast`, or the equivalent `typing_extensions.cast`
- **THEN** the checker reports an unsafe-cast diagnostic at the call site.

#### Scenario: Shadowed cast name is not reported
- **WHEN** a local variable, parameter, function, or class shadows the imported `cast` name
- **THEN** calls to the shadowed local name are not reported as typing cast diagnostics.

### Requirement: Broad dynamic annotation diagnostics
The system SHALL report broad dynamic annotations that leak imprecise types into checker-visible contracts.

#### Scenario: Broad Any annotation is reported
- **WHEN** a function parameter, return annotation, variable annotation, or type alias contains `Any` from `typing` or `typing_extensions`
- **THEN** the checker reports a broad-Any diagnostic at the annotation location.

#### Scenario: Broad object annotation is reported
- **WHEN** a function parameter, return annotation, variable annotation, or type alias contains `object` as a broad placeholder
- **THEN** the checker reports a broad-object diagnostic at the annotation location.

#### Scenario: Known-shape object container is reported
- **WHEN** an annotation uses `dict`, `Dict`, `tuple`, `Tuple`, `Mapping`, or `MutableMapping` with `object` inside the shaped container
- **THEN** the checker reports a broad known-shape container diagnostic at the annotation location.

#### Scenario: Type aliases are inspected
- **WHEN** a PEP 695 type alias or `TypeAlias` assignment contains a broad dynamic annotation
- **THEN** the checker reports the matching broad dynamic annotation diagnostic for the alias value.

### Requirement: Practical object annotation exceptions
The system SHALL avoid reporting `object` annotations when the syntax represents a narrow, idiomatic opaque-object contract.

#### Scenario: Equality other parameter is accepted
- **WHEN** a class defines `__eq__(self, other: object) -> bool`
- **THEN** the checker does not report the `other: object` annotation as a broad-object violation.

#### Scenario: Descriptor object parameters are accepted
- **WHEN** a descriptor protocol method annotates conventional instance, owner, or value parameters as `object`
- **THEN** the checker does not report those parameters solely because they use `object`.

#### Scenario: Opaque predicate object parameter is accepted
- **WHEN** an `is_*` predicate accepts an `object` parameter and the implementation does not inspect attributes or subscripts on that parameter
- **THEN** the checker does not report that parameter solely because it uses `object`.

### Requirement: Vague callable diagnostics
The system SHALL report callable surfaces that hide known argument structure behind an ellipsis or broad variadic boundary.

#### Scenario: Callable ellipsis is reported
- **WHEN** an annotation uses `Callable[..., ReturnType]` or an equivalent imported callable alias
- **THEN** the checker reports a vague-callable diagnostic at the annotation location.

#### Scenario: Variadic broad dynamic callable parameter is reported
- **WHEN** a `*args` or `**kwargs` annotation contains `Any` or broad `object`
- **THEN** the checker reports a vague-callable diagnostic for the variadic parameter surface.

### Requirement: Legacy type-parameter diagnostics
The system SHALL report avoidable module-level legacy `TypeVar`, `ParamSpec`, and `TypeVarTuple` usage in repository-owned code.

#### Scenario: Legacy type-parameter import is reported
- **WHEN** Python source imports `TypeVar`, `ParamSpec`, or `TypeVarTuple` from `typing` or `typing_extensions` and the import is used for legacy declarations
- **THEN** the checker reports a legacy-type-parameter diagnostic.

#### Scenario: Legacy type-parameter assignment is reported
- **WHEN** a module-level assignment calls `TypeVar`, `ParamSpec`, or `TypeVarTuple` through an imported or qualified typing name
- **THEN** the checker reports a legacy-type-parameter diagnostic at the declaration.

#### Scenario: Shadowed factory is not reported
- **WHEN** the apparent legacy type-parameter factory name is shadowed by a local declaration before use
- **THEN** the checker does not report that shadowed name as a typing factory.

### Requirement: Self return typing diagnostics
The system SHALL report classmethod factories that preserve receiver subtype behavior but avoidably use a concrete return annotation instead of `Self`.

#### Scenario: Direct cls construction requires Self
- **WHEN** a classmethod returns `cls(...)` and its return annotation does not contain `Self`
- **THEN** the checker reports a Self-return-typing diagnostic at the return annotation or method definition.

#### Scenario: Stored cls construction result requires Self
- **WHEN** a classmethod stores the result of `cls(...)` in a local name and returns that name
- **THEN** the checker reports a Self-return-typing diagnostic when the return annotation does not contain `Self`.

#### Scenario: Existing Self annotation is accepted
- **WHEN** a classmethod factory that returns `cls(...)` has a return annotation containing `Self`
- **THEN** the checker does not report a Self-return-typing diagnostic.

### Requirement: File-local deterministic analysis
The system SHALL implement repository `AGT` checks as deterministic file-local analysis over flake8-provided source data, without requiring repository-defined pre-sorted checker iteration order for direct `run()` callers.

#### Scenario: No subprocess candidate discovery is required
- **WHEN** flake8 invokes the checker for a Python file
- **THEN** the checker analyzes the file without invoking ast-grep, spawning subprocesses, or traversing repository directories.

#### Scenario: Alias resolution handles typing spellings
- **WHEN** annotations use aliases from `typing`, `typing_extensions`, or `collections.abc`
- **THEN** the checker resolves supported aliases consistently before deciding whether to report diagnostics.

#### Scenario: Direct diagnostics contain expected violations
- **WHEN** a direct checker invocation emits multiple `AGT` violations
- **THEN** the emitted diagnostics contain the expected codes, line numbers, column numbers, and messages without requiring a repository-defined sorted iteration order.

### Requirement: Literal value domains are not broad dynamic annotations
The system SHALL NOT report broad dynamic annotation diagnostics for string literal values that appear as value members inside `Literal` annotations.

#### Scenario: Literal object string is accepted
- **WHEN** Python source annotates a value with `Literal["array", "object"]`
- **THEN** the checker does not report `AGT102` for the `"object"` literal member.

#### Scenario: Literal dynamic-name strings are accepted
- **WHEN** Python source annotates a value with `Literal["Any"]`, `Literal["typing.Any"]`, or `Literal["list[object]"]`
- **THEN** the checker does not report `AGT102` or `AGT105` solely because those strings name broad dynamic annotations.

#### Scenario: Literal aliases are accepted
- **WHEN** Python source uses imported, qualified, or aliased `Literal` spellings from `typing` or `typing_extensions` with string literal members that look like broad dynamic annotations
- **THEN** the checker treats those members as literal values and does not report broad dynamic diagnostics for them.

#### Scenario: Broad annotations outside Literal remain reported
- **WHEN** Python source combines a safe literal value domain with an actual broad annotation outside the `Literal` value position, such as `Literal["object"] | object`
- **THEN** the checker still reports the broad annotation diagnostic for the real `object` annotation branch.

#### Scenario: Stringized broad annotations remain reported
- **WHEN** Python source uses a stringized broad annotation outside a `Literal` value position, such as `def handle(value: "object") -> None`
- **THEN** the checker reports `AGT102` for the stringized broad annotation.

