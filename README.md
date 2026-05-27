# flake8-agents

![Flake8](https://img.shields.io/badge/Flake8-AGT-green)
![Typed](https://img.shields.io/badge/typing-typed-purple)
![License: MIT](https://img.shields.io/badge/license-MIT-informational)
[![PyPI version](https://badge.fury.io/py/flake8-agents.svg)](https://badge.fury.io/py/flake8-agents)
[![python version](https://img.shields.io/pypi/pyversions/flake8-agents.svg)](#)

`flake8-agents` is a Flake8 plugin for codebases that use AI-generated Python.
It exists because generated code often hides problems from static analysis with
reflection, broad types, casts, raw namespace access, and stale suppressions.

The plugin turns those escape hatches into explicit `AGT` diagnostics.

## Usage

```sh
uv sync
uv run flake8 --select AGT src
uv run module-size src --warn-lines 800 --error-lines 1000
```

Minimal Flake8 config:

```ini
[flake8]
select = AGT
```

## Rules

### Suppressions

| Code | Catches | Example |
| --- | --- | --- |
| `AGT001` | unused explicit AGT `noqa` suppressions | `value: int = 1  # noqa: AGT105` |
| `AGT100` | broad type-checker suppressions | `value = 1  # type: ignore[assignment]` |

### Type escapes

| Code | Catches | Example |
| --- | --- | --- |
| `AGT101` | `typing.cast` used as a narrowing bypass | `result = cast(int, value)` |
| `AGT102` | broad `object` annotations | `def handle(value: object) -> None: ...` |
| `AGT103` | known-shape containers that erase value shape | `payload: dict[str, object]` |
| `AGT104` | vague callable signatures | `callback: Callable[..., int]` |
| `AGT105` | broad `Any` at non-local boundaries | `def handle(value: Any) -> None: ...` |
| `AGT106` | legacy type-parameter factories | `T = TypeVar("T")` |
| `AGT107` | classmethod factories returning their class name | `def build(cls) -> "Box": ...` |

### Dynamic anti-patterns

| Code | Catches | Example |
| --- | --- | --- |
| `AGT200` | dynamic attribute reads | `value = getattr(target, "name")` |
| `AGT201` | dynamic attribute writes | `setattr(target, "name", value)` |
| `AGT202` | raw namespace extraction | `namespace = vars(target)` |
| `AGT203` | dynamic import builtin | `module = __import__("package")` |
| `AGT204` | `importlib.import_module` calls | `module = importlib.import_module("package")` |
| `AGT205` | setattr-style mutation methods | `target.setattr("name", value)` |
| `AGT206` | direct `__setattr__` calls | `target.__setattr__("name", value)` |
| `AGT207` | direct `__new__` construction | `instance = Target.__new__(Target)` |
| `AGT208` | direct raw `__dict__` indexing | `value = target.__dict__["name"]` |
| `AGT209` | aliasing raw `__dict__` | `namespace = target.__dict__` |
| `AGT210` | indexing raw `__dict__` aliases | `value = namespace["name"]` |
| `AGT211` | aliasing dotted module imports | `import package.module as alias` |

### Import boundaries

| Code | Catches | Example |
| --- | --- | --- |
| `AGT300` | private project imports across module boundaries | `from module import _private` |
| `AGT301` | configured retired project import paths | `import module.legacy` |
| `AGT302` | declarations before the module import section is complete | `VALUE = 1` before `import ast` |

## module-size

`module-size` is a separate command that fails on oversized Python modules.

```sh
uv run module-size src --warn-lines 800 --error-lines 1000
```

| Option | Default | Meaning |
| --- | ---: | --- |
| `paths` | required | Python files or directories to scan |
| `--warn-lines` | `800` | print warning findings at or above this line count |
| `--error-lines` | `1000` | return failure at or above this line count |
| `--exclude REGEX` | none | skip files whose resolved path matches the regex |
| `--suppress-warnings` | `false` | hide warning findings from stdout |

```text
PATH                              LINES  LEVEL    THRESHOLD
/path/to/src/package/large.py     1012   error    1000
```

## Python support

`flake8-agents` supports Python `>=3.10` and is typed (`py.typed`). Runtime
dependencies are intentionally small: `flake8` and `typing-extensions`.

## License

MIT. See [`LICENSE`](LICENSE).
