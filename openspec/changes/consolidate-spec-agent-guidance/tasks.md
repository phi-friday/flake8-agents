## 1. Inventory and Cutover Decisions

- [ ] 1.1 List active persistent specs and classify each as product behavior, durable governance, duplicated policy, or stale/unimplemented surface.
- [ ] 1.2 Decide whether to preserve the existing `ylw-suppression-hygiene` directory name or cleanly rename it to an AGT-specific suppression-hygiene capability.
- [ ] 1.3 Decide whether retired specs are deleted outright or moved to an archive location supported by the repository's OpenSpec workflow.

## 2. OpenSpec Consolidation

- [ ] 2.1 Add the persistent `spec-agent-guidance-governance` capability from this change's added requirements.
- [ ] 2.2 Update `repository-quality-guardrails` so it keeps validation and guidance-alignment requirements while removing duplicated strict typing, callable, style, async, testing, module-size, and type-escape catalog requirements.
- [ ] 2.3 Keep `type-escape-flake8-rules`, `anti-pattern-flake8-rules`, and `import-boundary-flake8-rules` as the canonical AGT product contracts and remove duplicate rule-catalog policy text from other active specs.
- [ ] 2.4 Fold standalone `self-return-typing` requirements into the `AGT107` type-escape contract and retire the `self-return-typing` capability.
- [ ] 2.5 Clarify AGT suppression hygiene naming and keep `AGT001` behavior as the canonical suppression-hygiene contract.
- [ ] 2.6 Update `module-size-cli` to own the active CLI presentation contract and Python-version-compatible async scheduling requirement.
- [ ] 2.7 Retire stale or over-granular specs that describe absent guard scripts, unimplemented CLI help/logging surfaces, duplicated code-organization policy, or historical implementation phases.

## 3. Agent Guidance Cleanup

- [ ] 3.1 Update root `AGENTS.md` to focus on repository overview, architecture, conventions not fully represented by tool config, and canonical validation commands.
- [ ] 3.2 Remove diagnostic-level AGT, Ruff, Pyrefly, and module-size rule catalogs from `AGENTS.md` where executable checks and product specs already own them.
- [ ] 3.3 Update `src/tests/AGENTS.md` so test organization and behavior-testing guidance remains, while duplicated type-escape and anti-pattern policy text is removed or replaced with references to validation checks.

## 4. Verification

- [ ] 4.1 Run `openspec validate consolidate-spec-agent-guidance` after applying spec deltas.
- [ ] 4.2 Run `openspec validate --all` after removing or archiving obsolete specs.
- [ ] 4.3 Search active OpenSpec and `AGENTS.md` guidance for stale references to retired capability names and remove or update them.
- [ ] 4.4 Confirm no production Python files changed; if production code changes unexpectedly, run the focused tests and validation commands for the touched code before completion.
