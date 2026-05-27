## Context

`TypeEscapeChecker` emits AGT106 when module-level assignments call `TypeVar`, `ParamSpec`, or `TypeVarTuple` through recognized `typing` or `typing_extensions` aliases. The diagnostic message recommends PEP 695 type parameter syntax, which is only syntactically available on Python 3.12 and newer. The package still supports Python 3.10+, and source analyzed while running on Python 3.10 or 3.11 cannot necessarily replace legacy factories with native type parameter syntax.

## Goals / Non-Goals

**Goals:**

- Disable AGT106 on Python versions earlier than 3.12.
- Preserve the existing AGT106 detection behavior on Python 3.12 and newer.
- Keep the gate cheap, deterministic, and file-local.
- Keep all other type-escape diagnostics unchanged.

**Non-Goals:**

- Add a new AGT diagnostic code or rewrite the AGT106 message.
- Introduce project configuration discovery or a new Flake8 option for target-version selection.
- Change support for PEP 695 `type` aliases, `Self`, broad dynamic annotations, or suppression auditing.

## Decisions

- Use Python 3.12 as the activation threshold for AGT106.
  - Rationale: PEP 695 native type parameter syntax is introduced in Python 3.12. Earlier runtimes cannot parse every replacement AGT106 recommends.
  - Alternative considered: Python 3.13+ only. Rejected because the syntax is already available in 3.12.

- Gate AGT106 at the legacy-type-parameter emission point, not by removing import alias collection or assignment traversal.
  - Rationale: alias resolution and traversal are shared, cheap operations, and keeping the gate close to diagnostic emission minimizes risk to AGT100-AGT105 and AGT107.
  - Alternative considered: skip the whole `TypeEscapeChecker` visitor before Python 3.12. Rejected because it would also disable unrelated type-escape diagnostics.

- Model the version check as a small helper or constant in `type_escape.py`.
  - Rationale: tests can exercise both enabled and disabled behavior by targeting that single predicate, and production code avoids per-node recomputation.
  - Alternative considered: hard-code `sys.version_info` checks inside every AGT106 branch. Rejected because repeated checks are noisier and easier to apply inconsistently.

## Risks / Trade-offs

- Runtime version is not always the same as project target version. → Mitigation: this change fixes the guaranteed invalid recommendation on Python <3.12 without introducing configuration semantics; project-target configuration can be proposed separately if needed.
- Tests running on only one interpreter version may miss one branch. → Mitigation: expose the gate through an injectable helper or monkeypatchable module-level predicate so unit tests cover both enabled and disabled AGT106 behavior in the same test environment.
- Existing tests currently expecting AGT106 unconditionally will fail on Python <3.12. → Mitigation: update tests to assert version-gated behavior explicitly instead of depending on the host interpreter.
