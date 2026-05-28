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

Capabilities that describe absent surfaces should be removed or archived instead of rewritten into vague placeholders. This applies to guard-script optimization/concurrency specs and CLI help/logging specs that are not implemented by the current `module-size` CLI.

Alternative considered: keep a single umbrella "future guardrails" spec. Rejected because persistent specs should describe current or deliberately proposed behavior, not a backlog of maybe-future policies.

### Decision: Merge duplicated requirements into their canonical product capability

`self-return-typing` should be represented by `AGT107` inside `type-escape-flake8-rules`. Suppression hygiene should be represented by the AGT suppression-hygiene capability. Repeated strict typing and dynamic anti-pattern policy text in `repository-quality-guardrails` should be removed in favor of links or references to AGT behavior.

Alternative considered: keep standalone topic specs for readability. Rejected because small duplicated specs make ownership less clear and increase drift.

### Decision: Do not correct product behavior mismatches as part of this cleanup

Some existing specs describe behavior not currently implemented, such as color-aware CLI help or display-width-aware table padding. This change should remove or archive those stale requirements rather than implement new behavior under a documentation cleanup.

Alternative considered: implement missing features while consolidating specs. Rejected because it would turn a documentation-governance cleanup into product expansion.

## Risks / Trade-offs

- [Risk] Removing a spec may hide a useful future idea. → Mitigation: archive or preserve rationale in the change record when the idea is intentionally deferred, but do not keep it as an active requirement.
- [Risk] Over-consolidation may make product behavior harder to find. → Mitigation: keep AGT rule-family and `module-size` specs focused and named around product surfaces.
- [Risk] `AGENTS.md` may become too terse for future agents. → Mitigation: keep commands, repository architecture, and pointers to canonical specs; remove only duplicated rule catalogs.
- [Risk] Renaming `ylw-suppression-hygiene` may require careful filesystem and reference updates. → Mitigation: perform a clean cutover with no stale spec directory or duplicate capability unless OpenSpec tooling requires a transitional delta.

## Migration Plan

1. Add the governance spec that defines the boundary between OpenSpec, `AGENTS.md`, and executable checks.
2. Add delta specs that establish canonical ownership for AGT rule families, AGT suppression hygiene, repository-quality guidance, and `module-size`.
3. During implementation, delete or archive obsolete persistent specs after their useful requirements are either removed as stale or folded into canonical specs.
4. Update root and test-scoped `AGENTS.md` to remove duplicate diagnostic catalogs and stale guard-script guidance.
5. Run OpenSpec validation and targeted documentation checks; no production behavior tests are required unless implementation accidentally touches Python code.

## Open Questions

- Whether the existing `ylw-suppression-hygiene` capability should be renamed to `agt-suppression-hygiene` in-place or left with its current directory name while clarifying the title and purpose.
- Whether retired specs should be moved to an archive location or deleted outright as part of the clean cutover.
