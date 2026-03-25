from pathlib import Path

import pytest

from memberships.services.matrix import load_levels_from_fixture
from memberships.services.recommendations import Level

FIXTURE_PATH = (
    Path(__file__).resolve().parents[2] / "fixtures" / "membership_levels.json"
)


@pytest.fixture(scope="session")
def levels_from_fixture() -> list[Level]:
    return load_levels_from_fixture(FIXTURE_PATH)
