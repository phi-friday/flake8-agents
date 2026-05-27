# self-return-typing Specification

## Purpose

Define repository typing conventions for classmethod factories that preserve the
receiver subclass type, including when `Self` is required and when concrete
return annotations remain intentional.
## Requirements
### Requirement: Subtype-preserving classmethod factories use Self

Repository-owned Python classmethod factories MUST use `Self` as the return
annotation when they construct and return `cls(...)` and the method contract
preserves the receiver class type.

#### Scenario: Direct cls construction

- **WHEN** a classmethod returns `cls(...)` or a helper result guaranteed to be an
  instance of the receiver class
- **THEN** the return annotation is `Self`.

#### Scenario: Alternative constructor preserves subclasses

- **WHEN** an alternative constructor is inherited by subclasses and returns the
  subclass when called on that subclass
- **THEN** the method uses `Self` instead of naming the base class.

### Requirement: Concrete return annotations are intentional

Repository-owned classmethod factories MUST keep concrete class return
annotations when they intentionally return a fixed implementation rather than
preserving the receiver class type.

#### Scenario: Fixed implementation constructor

- **WHEN** a classmethod always returns a specific concrete class regardless of
  the receiver
- **THEN** the return annotation names that concrete class and the implementation
  does not imply subtype preservation.

### Requirement: Self convention is guarded

The repository MUST include validation coverage that detects new classmethod
factories returning `cls(...)` with avoidable concrete return annotations.

#### Scenario: New avoidable concrete annotation

- **WHEN** validation scans a classmethod that returns `cls(...)` but annotates a
  concrete owning class
- **THEN** validation reports the location and recommends `Self` unless an
  explicit fixed-implementation exception applies.

### Requirement: Self convention is exposed as a flake8 diagnostic
The system SHALL expose avoidable classmethod factory return annotations as a flake8 diagnostic so the `Self` convention can be enforced through the standard flake8 plugin workflow.

#### Scenario: Flake8 reports avoidable concrete annotation
- **WHEN** flake8 checks a classmethod factory that constructs and returns `cls(...)` while annotating the return as a concrete class instead of `Self`
- **THEN** the type-escape flake8 plugin reports a Self-return-typing diagnostic.

#### Scenario: Flake8 accepts Self annotation
- **WHEN** flake8 checks a classmethod factory that constructs and returns `cls(...)` and annotates the return with `Self`
- **THEN** the type-escape flake8 plugin does not report a Self-return-typing diagnostic.

