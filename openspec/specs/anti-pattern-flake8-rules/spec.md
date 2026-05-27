# anti-pattern-flake8-rules Specification

## Purpose
TBD - created by archiving change add-anti-pattern-flake8-rules. Update Purpose after archive.
## Requirements
### Requirement: Anti-pattern flake8 extension diagnostics
The system SHALL expose dynamic anti-pattern rules as stable `AGT2xx` flake8 diagnostics through the installed `AGT` extension namespace.

#### Scenario: Anti-pattern diagnostics use stable codes
- **WHEN** the checker reports a dynamic anti-pattern violation
- **THEN** the diagnostic message begins with a stable `AGT2xx` code that flake8 can select, ignore, and suppress by code.

#### Scenario: Anti-pattern rules run through installed flake8 plugin
- **WHEN** flake8 runs against Python source with `AGT` selected
- **THEN** the anti-pattern checker participates in flake8's normal per-file checking pipeline.

### Requirement: Dynamic lookup and mutation diagnostics
The system SHALL report dynamic attribute lookup and mutation escape hatches that hide known member access from static analysis.

#### Scenario: Getattr call is reported
- **WHEN** Python source calls the builtin `getattr(...)`
- **THEN** the checker reports `AGT200` at the call site.

#### Scenario: Setattr call is reported
- **WHEN** Python source calls the builtin `setattr(...)`
- **THEN** the checker reports `AGT201` at the call site.

#### Scenario: Vars call is reported
- **WHEN** Python source calls the builtin `vars(...)`
- **THEN** the checker reports `AGT202` at the call site.

#### Scenario: Attribute setattr call is reported
- **WHEN** Python source calls an attribute named `setattr` on an object other than pytest's `monkeypatch` fixture
- **THEN** the checker reports `AGT205` at the call site.

#### Scenario: Monkeypatch setattr is accepted
- **WHEN** Python source calls `monkeypatch.setattr(...)`
- **THEN** the checker does not report the call as a dynamic mutation anti-pattern.

#### Scenario: Dunder setattr call is reported
- **WHEN** Python source calls `__setattr__(...)` through attribute access on a known target
- **THEN** the checker reports `AGT206` at the call site.

#### Scenario: Shadowed builtin call names are accepted
- **WHEN** a local binding shadows a builtin dynamic lookup or mutation name before that name is called
- **THEN** the checker does not report that call as a builtin dynamic anti-pattern.

### Requirement: Dynamic import diagnostics
The system SHALL report dynamic import calls that hide import dependencies from static analysis.

#### Scenario: Dunder import call is reported
- **WHEN** Python source calls the builtin `__import__(...)`
- **THEN** the checker reports `AGT203` at the call site.

#### Scenario: Importlib import_module call is reported
- **WHEN** Python source calls `importlib.import_module(...)` or an alias imported from `importlib.import_module`
- **THEN** the checker reports `AGT204` at the call site.

#### Scenario: Aliased importlib module call is reported
- **WHEN** Python source imports `importlib` with an alias and calls `<alias>.import_module(...)`
- **THEN** the checker reports `AGT204` at the call site.

#### Scenario: Shadowed dynamic import names are accepted
- **WHEN** a local binding shadows `__import__` or an imported `import_module` name before that name is called
- **THEN** the checker does not report that call as a dynamic import anti-pattern.

### Requirement: Construction bypass diagnostics
The system SHALL report direct `__new__` calls that bypass ordinary construction APIs and class invariants.

#### Scenario: Dunder new call is reported
- **WHEN** Python source calls `__new__(...)` through attribute access on a target other than `object`
- **THEN** the checker reports `AGT207` at the call site.

#### Scenario: Object dunder new call is accepted
- **WHEN** Python source calls `object.__new__(...)`
- **THEN** the checker does not report that call as a construction bypass anti-pattern.

### Requirement: Raw namespace diagnostics
The system SHALL report raw namespace access through `__dict__` or aliases of `__dict__`.

#### Scenario: Direct namespace dictionary index is reported
- **WHEN** Python source indexes `obj.__dict__`
- **THEN** the checker reports `AGT208` at the subscript expression.

#### Scenario: Namespace dictionary alias assignment is reported
- **WHEN** Python source assigns `obj.__dict__` to a name using assignment or annotated assignment
- **THEN** the checker reports `AGT209` at the assignment line.

#### Scenario: Namespace dictionary alias index is reported
- **WHEN** Python source indexes a name previously bound to `obj.__dict__` in an active scope
- **THEN** the checker reports `AGT210` at the subscript expression.

#### Scenario: Alias tracking respects nested scopes
- **WHEN** Python source indexes a `__dict__` alias from the current scope or an enclosing active scope
- **THEN** the checker reports the alias-index diagnostic deterministically for the indexed expression.

### Requirement: Dotted import alias diagnostics
The system SHALL report import aliases that hide a dotted module path behind an arbitrary name while allowing explicit top-level and from-import alias forms.

#### Scenario: Dotted module import alias is reported
- **WHEN** Python source contains `import package.module as alias`
- **THEN** the checker reports `AGT211` at the import statement.

#### Scenario: Top-level import alias is accepted
- **WHEN** Python source contains `import package as alias`
- **THEN** the checker does not report the import as a dotted import alias violation.

#### Scenario: From import alias is accepted
- **WHEN** Python source contains `from package import module as alias`
- **THEN** the checker does not report the import as a dotted import alias violation.

#### Scenario: Unaliased dotted import is accepted
- **WHEN** Python source contains `import package.module` without an alias
- **THEN** the checker does not report the import as a dotted import alias violation.

### Requirement: Anti-pattern file-local deterministic analysis
The system SHALL implement anti-pattern diagnostics as deterministic file-local analysis over flake8-provided source data, without requiring repository-defined pre-sorted checker iteration order for direct `run()` callers.

#### Scenario: No subprocess candidate discovery is required
- **WHEN** flake8 invokes the checker for a Python file
- **THEN** the anti-pattern checker analyzes the file without invoking ast-grep, spawning subprocesses, or traversing repository directories.

#### Scenario: Direct diagnostics contain expected violations
- **WHEN** a direct anti-pattern checker invocation emits multiple anti-pattern violations
- **THEN** the emitted diagnostics contain the expected codes, line numbers, column numbers, and messages without requiring a repository-defined sorted iteration order.

