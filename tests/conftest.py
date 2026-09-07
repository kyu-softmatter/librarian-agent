"""Fixtures. Integration tests skip rather than fail when cache/ is empty.

A test that needs a clone is not a test of this repository, so it announces the
dependency instead of turning an absent checkout into a red build.
"""

from pathlib import Path

import pytest

CACHE = Path(__file__).resolve().parent.parent / "cache"


def _repo(name: str) -> Path:
    p = CACHE / name
    if not (p / ".git").exists():
        pytest.skip(f"cache/{name} is not cloned")
    return p


@pytest.fixture
def ms() -> Path:
    return _repo("ms")


@pytest.fixture
def bd() -> Path:
    return _repo("bd")
