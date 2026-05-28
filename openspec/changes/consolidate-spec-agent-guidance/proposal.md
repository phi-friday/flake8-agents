## Why

The repository now enforces many formerly documented quality policies through executable checks, especially the AGT flake8 diagnostics, Ruff, Pyrefly, and the `module-size` CLI. The persistent OpenSpec surface and `AGENTS.md` guidance still repeat obsolete guard-script, typing, anti-pattern, and contributor-policy details, making the documented contract harder to trust than the checks that actually run.

## What Changes

- Consolidate persistent OpenSpec coverage around current product contracts: the AGT flake8 plugin and the `module-size` CLI.
- Introduce a small governance capability that defines what belongs in persistent specs versus `AGENTS.md` versus executable tooling.
- Remove or archive stale specs whose requirements describe absent guard scripts, unimplemented CLI surfaces, or policies now owned by AGT/Ruff/Pyrefly/module-size validation.
- Fold duplicated `Self` return-typing requirements into the AGT type-escape rule contract and retire the standalone `self-return-typing` capability.
- Narrow repository quality guidance to validation workflow, artifact ownership, and guidance/spec alignment rather than restating lint rule catalogs.
- Update root and test-scoped `AGENTS.md` so they point maintainers to executable checks and product specs instead of duplicating diagnostic-level policy.
- Preserve the existing runtime behavior of the flake8 plugin and `module-size`; this change reorganizes documented contracts and guidance only.

## Capabilities

### New Capabilities
- `spec-agent-guidance-governance`: Defines the ownership boundary between persistent OpenSpec requirements, agent guidance, and executable validation checks.

### Modified Capabilities
- `repository-quality-guardrails`: Remove duplicated strict typing, anti-pattern, and suppression rule catalogs; keep only repository validation workflow and guidance/spec alignment requirements that are not already owned by executable checks.
- `type-escape-flake8-rules`: Make AGT100-family and AGT107 the canonical type-escape contract, including the `Self` return-typing behavior currently duplicated by `self-return-typing`.
- `anti-pattern-flake8-rules`: Keep AGT200-family behavior as the canonical dynamic anti-pattern contract and remove duplicate policy restatements elsewhere.
- `import-boundary-flake8-rules`: Keep AGT300-family behavior as the canonical import-boundary contract and remove duplicate policy restatements elsewhere.
- `ylw-suppression-hygiene`: Keep AGT001 behavior as the canonical AGT suppression-hygiene contract and rename or otherwise clarify the capability as AGT suppression hygiene during consolidation.
- `module-size-cli`: Keep current CLI behavior as the canonical module-size contract and remove stale adjacent CLI requirements that describe unsupported help-color or logging surfaces.

## Impact

- Affected documentation artifacts: `openspec/specs/**/spec.md`, `openspec/changes/consolidate-spec-agent-guidance/**`, root `AGENTS.md`, and `src/tests/AGENTS.md`.
- No production Python behavior, flake8 diagnostic code, CLI option, packaging entry point, runtime dependency, or public API change is intended.
- OpenSpec validation should continue to pass after deleted, renamed, or merged specs are reflected in the change artifacts.
