## Context

The repository has converged on a small set of executable enforcement surfaces:

- The installed `AGT` flake8 extension owns type-escape, dynamic anti-pattern, import-boundary, and unused AGT `noqa` diagnostics.
- Ruff and Pyrefly own formatting, import sorting, annotation coverage, type-checking, and many style constraints.
- The `module-size` CLI owns physical line-count threshold validation.
- `AGENTS.md` tells future maintainers how to work in the repository and which checks to run.

The persistent OpenSpec tree still contains many fine-grained policy specs from earlier guard-script and repository-policy phases. Some are now duplicated by executable AGT rules, some describe absent guard scripts or unimplemented CLI surfaces, and some restate contributor guidance that belongs in `AGENTS.md` rather than persistent product requirements.

## Goals / Non-Goals

**Goals:**

- Make persistent specs describe current, user-visible product behavior and durable repository documentation governance.
- Remove stale specs that cannot be validated against the current codebase without inventing new guard scripts or CLI features.
- Keep AGT rule-family specs as the canonical behavioral contracts for diagnostics.
- Keep `module-size-cli` as the canonical behavioral contract for the `module-size` command.
- Make `AGENTS.md` shorter and operational: repository shape, conventions, validation commands, and where to find product rule contracts.
- Preserve OpenSpec validity after the consolidation.

**Non-Goals:**

- No changes to production Python behavior, diagnostic messages, rule codes, CLI options, or package entry points.
- No new lint rules, no new guard scripts, and no new dependencies.
- No attempt to document every AGT scenario in `AGENTS.md`.
- No compatibility shim or fallback behavior introduced solely to satisfy old specs.

## Decisions

### Decision: Product specs own behavior; AGENTS.md owns workflow

Persistent specs should describe behavior a user or maintainer can depend on. `AGENTS.md` should explain how contributors and agents should operate: which directories matter, which commands validate work, and which conventions are repository-local.

Alternative considered: keep policy catalogs in both places for visibility. Rejected because duplicated rule lists drift and make future changes require multiple edits for one behavior.

### Decision: Executable checks are the source of truth for low-level style and rule catalogs

When AGT, Ruff, Pyrefly, or `module-size` already enforces a rule, guidance should point to the check instead of restating all forbidden syntax forms. The detailed behavior remains in the relevant product spec when it is user-visible.

Alternative considered: retain OpenSpec policy specs as a second layer of normative enforcement. Rejected because the current repository has no separate guard implementation for many of those specs, so they read as requirements without an executable owner.

### Decision: Retire stale capabilities rather than preserve them as empty shells

Capabilities that describe absent surfaces should be removed instead of rewritten into vague placeholders. This applies to guard-script optimization/concurrency specs, code-organization policy specs without current automated owners, and CLI help/logging specs that are not implemented by the current `module-size` CLI.

Alternative considered: keep a single umbrella "future guardrails" spec. Rejected because persistent specs should describe current or deliberately proposed behavior, not a backlog of maybe-future policies.

### Decision: Merge duplicated requirements into their canonical product capability

`self-return-typing` is represented by `AGT107` inside `type-escape-flake8-rules`. Suppression hygiene remains represented by the existing `ylw-suppression-hygiene` capability directory, with its title and purpose clarified as AGT-specific suppression hygiene. Repeated strict typing and dynamic anti-pattern policy text in `repository-quality-guardrails` is removed in favor of the AGT behavior specs.

Alternative considered: keep standalone topic specs for readability. Rejected because small duplicated specs make ownership less clear and increase drift.

### Decision: Preserve the suppression-hygiene directory name for this cutover

The existing `ylw-suppression-hygiene` directory name is preserved to avoid coupling this cleanup to a capability rename. The active spec title and purpose are updated to say AGT suppression hygiene, and future work can rename the capability if OpenSpec tooling provides an explicit rename path.

Alternative considered: rename the directory to `agt-suppression-hygiene`. Rejected for this change because the existing change artifact already modifies `ylw-suppression-hygiene`, and the user-visible contract is clearer once the title and purpose are corrected.

### Decision: Delete retired persistent specs directly

Retired specs are removed from the active `openspec/specs/` tree rather than moved into a new spec archive. Their rationale remains in this change proposal, design, and tasks, and Git history preserves the deleted content.

Alternative considered: add a persistent spec archive directory. Rejected because archive mechanics are not defined for persistent specs in this repository, and a new archive surface would keep stale requirements close to active ones.

### Decision: Do not correct product behavior mismatches as part of this cleanup

Some existing specs describe behavior not currently implemented, such as color-aware CLI help or display-width-aware table padding. This change removes those stale requirements rather than implementing new behavior under a documentation cleanup.

Alternative considered: implement missing features while consolidating specs. Rejected because it would turn a documentation-governance cleanup into product expansion.

## Spec Inventory

| Capability | Classification | Action |
| --- | --- | --- |
| `type-escape-flake8-rules` | Product behavior | Keep and mark canonical for AGT1xx/AGT107 behavior. |
| `anti-pattern-flake8-rules` | Product behavior | Keep and mark canonical for AGT2xx behavior. |
| `import-boundary-flake8-rules` | Product behavior | Keep and mark canonical for AGT3xx behavior. |
| `ylw-suppression-hygiene` | Product behavior | Keep directory, clarify title/purpose as AGT suppression hygiene. |
| `module-size-cli` | Product behavior | Keep and own active CLI output/async compatibility contract. |
| `repository-quality-guardrails` | Durable governance | Keep only validation and guidance-alignment requirements. |
| `spec-agent-guidance-governance` | Durable governance | Add as the ownership boundary for specs, guidance, and executable checks. |
| `self-return-typing` | Duplicated policy | Remove after folding into `type-escape-flake8-rules`. |
| `audited-guard-exceptions` | Stale guard-script policy | Remove. |
| `quality-guard-fast-paths` | Stale guard-script policy | Remove. |
| `freethread-script-guard-concurrency` | Stale guard-script policy | Remove. |
| `bilingual-code-documentation` | Stale unimplemented guard policy | Remove. |
| `cli-help-presentation` | Unimplemented CLI surface | Remove. |
| `cli-logging-control` | Unimplemented CLI surface | Remove. |
| `cli-module-organization` | Duplicated code-organization policy | Remove. |
| `cli-tabular-output` | Duplicated/stale CLI presentation policy | Remove; `module-size-cli` owns current output. |
| `layered-exception-organization` | Duplicated code-organization policy | Remove. |
| `canonical-interface-contracts` | Duplicated pre-release cleanup policy | Remove. |
| `typed-data-flow-boundaries` | Duplicated typing/design policy | Remove. |
| `tooling-path-resolution` | Historical tooling policy | Remove. |
| `python-export-boundaries` | Duplicated export/import policy | Remove; `AGENTS.md`, Ruff, and AGT300 own active guidance/checks. |
| `performance-optimization-boundaries` | Duplicated design policy | Remove. |

## Risks / Trade-offs

- [Risk] Removing a spec may hide a useful future idea. → Mitigation: preserve rationale in the change record and rely on Git history for deleted content, but do not keep stale ideas as active requirements.
- [Risk] Over-consolidation may make product behavior harder to find. → Mitigation: keep AGT rule-family and `module-size` specs focused and named around product surfaces.
- [Risk] `AGENTS.md` may become too terse for future agents. → Mitigation: keep commands, repository architecture, and pointers to canonical specs; remove only duplicated rule catalogs.
- [Risk] The preserved `ylw-suppression-hygiene` directory name remains awkward. → Mitigation: clarify the spec title and purpose now; defer filesystem rename until OpenSpec capability rename semantics are explicit.

## Migration Plan

1. Add the governance spec that defines the boundary between OpenSpec, `AGENTS.md`, and executable checks.
2. Add delta specs that establish canonical ownership for AGT rule families, AGT suppression hygiene, repository-quality guidance, and `module-size`.
3. Delete obsolete persistent specs after their useful requirements are either removed as stale or folded into canonical specs.
4. Update root and test-scoped `AGENTS.md` to remove duplicate diagnostic catalogs and stale guard-script guidance.
5. Run OpenSpec validation and targeted documentation checks; no production behavior tests are required unless implementation accidentally touches Python code.

## Open Questions

None.
