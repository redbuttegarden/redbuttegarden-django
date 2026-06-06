"""Test fixtures for no-database external integration unit tests."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests() -> None:
    """Keep repository-wide database setup out of these unit tests."""
