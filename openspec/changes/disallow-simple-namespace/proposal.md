## Why

`types.SimpleNamespace` creates mutable attribute bags whose member reads are typed as `Any`, hiding object shape from static analysis while looking like a lightweight record type. `flake8-agents` already reports dynamic lookup, mutation, and raw namespace escapes; this closes the same escape hatch for ad hoc namespace objects.

## What Changes

- Add a stable `AGT2xx` anti-pattern diagnostic for constructing or annotating values as `types.SimpleNamespace`.
- Detect direct imports, aliases, and module-qualified references to `types.SimpleNamespace`.
- Preserve shadowing behavior so locally defined `SimpleNamespace` names are not reported as the stdlib class.
- Document accepted structured alternatives in tests and rule messaging through examples, not runtime dependencies.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `anti-pattern-flake8-rules`: add a SimpleNamespace diagnostic to the existing dynamic anti-pattern rule family.

## Impact

- Production: `src/flake8_agents/anti_pattern.py`
- Tests: `src/tests/test_anti_pattern.py`
- Specs: `openspec/specs/anti-pattern-flake8-rules/spec.md`
- Public behavior: one new `AGT2xx` diagnostic selectable, suppressible, and reportable through the installed `AGT` Flake8 plugin.
- Dependencies: none.
