from typing import Any

__all__ = ["__commit_id__", "__version__"]

__version__: str
__commit_id__: str | None


def __getattr__(name: str) -> Any:  # noqa: AGT105
    match name:
        case "__version__":
            try:
                # pyrefly: ignore[missing-import]
                from flake8_agents._version import (  # noqa: PLC0415,AGT300
                    __version__ as _version,
                )
            except ImportError:  # pragma: no cover
                from importlib.metadata import version  # noqa: PLC0415

                _version = version("flake8-agents")
            globals()["__version__"] = _version
            return _version
        case "__commit_id__":
            try:
                # pyrefly: ignore[missing-import]
                from flake8_agents._version import (  # noqa: PLC0415,AGT300
                    __commit_id__ as _commit_id,
                )
            except ImportError:  # pragma: no cover
                _commit_id = None
            globals()["__commit_id__"] = _commit_id
            return _commit_id

    error_msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(error_msg)
