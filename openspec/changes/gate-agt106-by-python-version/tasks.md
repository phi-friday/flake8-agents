## 1. Tests

- [ ] 1.1 Read `src/tests/AGENTS.md` before changing checker tests.
- [ ] 1.2 Add focused `TypeEscapeChecker` tests proving AGT106 is not emitted when the Python-version gate is below 3.12.
- [ ] 1.3 Add focused `TypeEscapeChecker` tests proving existing AGT106 alias, qualified-name, and shadowing behavior remains unchanged when the gate is 3.12 or newer.
- [ ] 1.4 Update aggregate checker or Flake8 integration expectations if version-gated AGT106 changes observed AGT output.

## 2. Implementation

- [ ] 2.1 Add a single Python-version gate in `src/flake8_agents/type_escape.py` for native type parameter syntax support.
- [ ] 2.2 Apply the gate only to AGT106 diagnostic emission for legacy `TypeVar`, `ParamSpec`, and `TypeVarTuple` declarations.
- [ ] 2.3 Keep AGT100-AGT105 and AGT107 traversal, alias resolution, diagnostics, and messages unchanged.
- [ ] 2.4 Remove or adjust any stale unconditional AGT106 assumptions in tests.

## 3. Verification

- [ ] 3.1 Run the focused type-escape tests that cover both enabled and disabled AGT106 branches.
- [ ] 3.2 Run `uv run ruff format src`.
- [ ] 3.3 Run `uv run ruff check src`.
- [ ] 3.4 Run `uv run pyrefly check src`.
- [ ] 3.5 Run `uv run flake8 src`.
- [ ] 3.6 Run `uv run pytest`.
