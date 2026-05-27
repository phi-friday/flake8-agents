from __future__ import annotations

import flake8_agents


def test_lazy_version_attributes_are_available() -> None:
    assert isinstance(flake8_agents.__version__, str)
    assert flake8_agents.__commit_id__ is None or isinstance(
        flake8_agents.__commit_id__, str
    )
