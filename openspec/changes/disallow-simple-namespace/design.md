## Context

`AntiPatternChecker` owns the `AGT2xx` family for dynamic lookup, mutation, import, construction-bypass, raw namespace, and dotted-import alias diagnostics. `types.SimpleNamespace` fits this family: it stores fields in `__dict__`, permits arbitrary attribute mutation, and typeshed exposes attribute reads and writes as `Any`.

Current checker state already tracks imported names, shadowed names, and nested scopes for dynamic imports and namespace aliases. The new rule should reuse that shape rather than introducing a second analysis convention.

## Goals / Non-Goals

**Goals:**

- Add one stable diagnostic, `AGT212`, for stdlib `types.SimpleNamespace` use.
- Report construction calls and annotations that resolve to stdlib `types.SimpleNamespace`.
- Support direct imports, aliases, `import types`, and `import types as alias`.
- Preserve local shadowing so project-defined `SimpleNamespace` names are accepted.
- Keep the analysis deterministic and file-local.

**Non-Goals:**

- Do not ban `argparse.Namespace`; it is returned by an external stdlib API and needs a separate policy.
- Do not introduce configuration, allowlists, runtime imports, or repository traversal.
- Do not report structured alternatives such as dataclasses, `NamedTuple`, or `TypedDict`.

## Decisions

1. **Place the rule in `AntiPatternChecker` as `AGT212`.**
   - Rationale: the problem is a dynamic runtime namespace escape, not only a type annotation escape.
   - Alternative considered: put it in `TypeEscapeChecker`. That would cover annotations but miss construction, the more common source of the dynamic object.

2. **Resolve stdlib references before reporting.**
   - Report `from types import SimpleNamespace`, including aliases, when the imported name is called or used as an annotation.
   - Report `types.SimpleNamespace` and module aliases imported from `types`.
   - Do not report a bare `SimpleNamespace` name unless it resolves to `types.SimpleNamespace` through an import.
   - Alternative considered: report every name spelled `SimpleNamespace`. That is simpler but creates false positives for local classes and test fakes.

3. **Report the use site, not import-only statements.**
   - Rationale: this matches existing rules such as `typing.cast` and `importlib.import_module`; importing alone is not the dynamic behavior.
   - Import-only cleanup remains the job of standard unused-import lint.

4. **Inspect annotation positions explicitly.**
   - Cover function parameters, returns, variable annotations, and type alias values where supported by the running Python version.
   - Parse string-literal annotations only as expressions and only for this rule's normal import-resolution path, matching the existing type-escape approach without evaluating code.

5. **Keep message wording direct.**
   - Proposed message: `AGT212 avoid SimpleNamespace dynamic attribute bags`.
   - This points at the structural problem without prescribing a single replacement; tests can document dataclass and TypedDict alternatives.

## Risks / Trade-offs

- False positives from shadowing → maintain scope-aware import/name tracking and cover local class/function/assignment shadowing in tests.
- Missed aliases through unusual dynamic import forms → acceptable; existing dynamic import rules already report those forms separately.
- Annotation traversal can duplicate type-escape helper concepts → keep helpers local and small unless a later refactor proves reuse is worth it.
- String annotations can contain arbitrary text → parse as expression only, ignore syntax failures, and never evaluate.
