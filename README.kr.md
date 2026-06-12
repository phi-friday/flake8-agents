# flake8-agents

![Flake8](https://img.shields.io/badge/Flake8-AGT-green)
![Typed](https://img.shields.io/badge/typing-typed-purple)
![License: MIT](https://img.shields.io/badge/license-MIT-informational)
[![PyPI version](https://badge.fury.io/py/flake8-agents.svg)](https://badge.fury.io/py/flake8-agents)
[![python version](https://img.shields.io/pypi/pyversions/flake8-agents.svg)](#)

[English](README.md) | [한국어](README.kr.md)

`flake8-agents`는 AI가 생성한 Python 코드를 사용하는 코드베이스를 위한
Flake8 플러그인입니다. 생성된 코드는 reflection, 넓은 타입, 캐스트, 원시
namespace 접근, 오래된 억제 주석으로 정적 분석이 찾을 수 있는 문제를 숨기는
경우가 많습니다.

이 플러그인은 그런 escape hatch를 명시적인 `AGT` 진단으로 바꿉니다.

## 사용법

```sh
uv sync
uv run flake8 --select AGT src
uv run module-size src --warn-lines 800 --error-lines 1000
```

최소 Flake8 설정:

```ini
[flake8]
select = AGT
```

## 규칙

### 억제 주석

| 코드 | 감지 대상 | 예 |
| --- | --- | --- |
| `AGT001` | 사용되지 않는 명시적 AGT `noqa` 억제 | `value: int = 1  # noqa: AGT105` |
| `AGT100` | 넓은 타입 검사기 억제 | `value = 1  # type: ignore[assignment]` |

### 타입 회피

| 코드 | 감지 대상 | 예 |
| --- | --- | --- |
| `AGT101` | narrowing 우회로 쓰인 `typing.cast` | `result = cast(int, value)` |
| `AGT102` | 넓은 `object` annotation | `def handle(value: object) -> None: ...` |
| `AGT103` | 값의 형태를 지우는 알려진 형태의 container | `payload: dict[str, object]` |
| `AGT104` | 모호한 callable signature | `callback: Callable[..., int]` |
| `AGT105` | non-local boundary의 넓은 `Any` | `def handle(value: Any) -> None: ...` |
| `AGT106` | legacy type-parameter factory | `T = TypeVar("T")` |
| `AGT107` | 클래스 이름을 반환하는 classmethod factory | `def build(cls) -> "Box": ...` |

### 동적 안티패턴

| 코드 | 감지 대상 | 예 |
| --- | --- | --- |
| `AGT200` | 동적 attribute 읽기 | `value = getattr(target, "name")` |
| `AGT201` | 동적 attribute 쓰기 | `setattr(target, "name", value)` |
| `AGT202` | 원시 namespace 추출 | `namespace = vars(target)` |
| `AGT203` | 동적 import builtin | `module = __import__("package")` |
| `AGT204` | `importlib.import_module` 호출 | `module = importlib.import_module("package")` |
| `AGT205` | setattr-style mutation method | `target.setattr("name", value)` |
| `AGT206` | 직접 `__setattr__` 호출 | `target.__setattr__("name", value)` |
| `AGT207` | 직접 `__new__` construction | `instance = Target.__new__(Target)` |
| `AGT208` | 원시 `__dict__` 직접 indexing | `value = target.__dict__["name"]` |
| `AGT209` | 원시 `__dict__` aliasing | `namespace = target.__dict__` |
| `AGT210` | 원시 `__dict__` alias indexing | `value = namespace["name"]` |
| `AGT211` | dotted module import aliasing | `import package.module as alias` |
| `AGT212` | `types.SimpleNamespace` 동적 attribute bag | `data = types.SimpleNamespace(name="value")` |

### import boundary

| 코드 | 감지 대상 | 예 |
| --- | --- | --- |
| `AGT300` | module boundary를 넘는 private project import | `from module import _private` |
| `AGT301` | 설정된 retired project import path | `import module.legacy` |
| `AGT302` | module import section이 끝나기 전의 선언 | `VALUE = 1` before `import ast` |

## module-size

`module-size`는 크기가 너무 큰 Python module에서 실패하는 별도 명령입니다.

```sh
uv run module-size src --warn-lines 800 --error-lines 1000
```

| 옵션 | 기본값 | 의미 |
| --- | ---: | --- |
| `paths` | 필수 | 스캔할 Python 파일 또는 디렉터리 |
| `--warn-lines` | `800` | 이 line count 이상에서 warning finding 출력 |
| `--error-lines` | `1000` | 이 line count 이상에서 failure 반환 |
| `--exclude REGEX` | 없음 | resolved path가 regex와 일치하는 파일 제외 |
| `--suppress-warnings` | `false` | stdout에서 warning finding 숨김 |

```text
PATH                              LINES  LEVEL    THRESHOLD
/path/to/src/package/large.py     1012   error    1000
```

## Python 지원

`flake8-agents`는 Python `>=3.10`을 지원하며 typed package입니다(`py.typed`).
Runtime dependency는 의도적으로 작게 유지합니다: `flake8`와
`typing-extensions`입니다.

## 설계 메모

`AGT` 규칙은 사람과 정적 도구가 살펴볼 수 있는 코드를 선호합니다. 동적 선언,
동적 import, cast, 넓은 타입, 억제 주석을 모든 코드베이스에서 안티패턴이라고
주장하려는 것이 아닙니다. 문제는 AI가 생성한 코드가 이런 escape hatch를
남용하면 의도와 프로그램 구조를 사람이 검토하기 어려워진다는 점입니다. AI가 더
발전하면 나아질 수 있지만, 현재의 생성 코드는 직전 요구사항을 맞추기 위해 가장
짧은 길을 택하거나, 불확실성을 덮거나, 완료되지 않은 변경을 완료된 것처럼
보이게 만들 수 있습니다. 이 규칙들은 그런 처리를 숨기기 어렵게 만들기 위한
장치이기도 합니다. 의도한 선택이라면 해당 코드는 유지하고, 특정 진단 코드를
담은 targeted explicit `noqa`, 예를 들어 `# noqa: AGT204`를 추가하세요.

## 라이선스

MIT. [`LICENSE`](LICENSE)를 참고하세요.
