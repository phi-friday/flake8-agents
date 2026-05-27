## Why

AGT106 currently requires PEP 695 type parameter syntax whenever it sees avoidable module-level `TypeVar`, `ParamSpec`, or `TypeVarTuple` declarations. That syntax is only valid on Python versions that can express generic type parameters without legacy factory calls, so projects targeting older Python versions receive an unusable recommendation.

## What Changes

- Gate AGT106 legacy type-parameter diagnostics on the Python version used to analyze source.
- Keep AGT106 active only when that Python version supports native type parameter syntax without `TypeVar`-family factory declarations.
- Preserve existing AGT106 shadowing, alias, and module-level declaration behavior when the version gate enables the rule.
- Do not change AGT100-AGT105 or AGT107 behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `type-escape-flake8-rules`: legacy type-parameter diagnostics become conditional on Python versions that support native generic type parameter syntax.

## Impact

- Affects `TypeEscapeChecker` AGT106 emission and aggregate Flake8 output.
- Requires tests for both Python targets that support PEP 695 syntax and targets that still require legacy `TypeVar`-family declarations.
- No new runtime dependencies, public CLI options, or diagnostic codes are introduced.
