## 1. Behavior Coverage

- [x] 1.1 Add direct `AntiPatternChecker` tests for `AGT212` on `SimpleNamespace(...)`, imported aliases, `types.SimpleNamespace(...)`, and `types` module aliases.
- [x] 1.2 Add tests for `AGT212` on parameter, return, variable, type alias, and string-literal annotations that resolve to stdlib `types.SimpleNamespace`.
- [x] 1.3 Add acceptance tests for import-only references, local shadowing, `argparse.Namespace`, dataclasses, `NamedTuple`, and `TypedDict`.

## 2. Checker Implementation

- [x] 2.1 Add `AGT212` to the anti-pattern diagnostic enum and message catalog.
- [x] 2.2 Track unshadowed stdlib `types` module imports and `types.SimpleNamespace` direct imports across nested scopes.
- [x] 2.3 Report `AGT212` for matching construction calls while preserving existing dynamic-import and namespace-alias diagnostics.
- [x] 2.4 Inspect annotation sites, parse string-literal annotations as expressions, and report resolvable `SimpleNamespace` annotations without evaluating code.

## 3. Integration and Validation

- [x] 3.1 Add or update Flake8 integration coverage proving `AGT212` is selectable through the installed `AGT` plugin.
- [x] 3.2 Run focused coverage-enabled pytest for anti-pattern behavior.
- [x] 3.3 Run applicable formatting, lint, type, Flake8, module-size, and coverage checks for the touched source and test files.
