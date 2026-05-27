import pytest


@pytest.fixture(params=[pytest.param(("asyncio", {"use_uvloop": False}), id="asyncio")])
def anyio_backend(request: pytest.FixtureRequest) -> tuple[str, dict[str, bool]]:
    return request.param
