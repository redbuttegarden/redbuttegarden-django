import json
from decimal import Decimal
from pathlib import Path

import pytest

from memberships.services.recommendations import Level

FIXTURE_PATH = Path("/code/memberships/fixtures/membership_levels.json")


@pytest.fixture(scope="session")
def levels_from_fixture() -> list[Level]:
    raw = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    levels: list[Level] = []
    for obj in raw:
        model = (obj.get("model") or "").lower()
        if not model.endswith(".membershiplevel"):
            continue
        f = obj["fields"]
        levels.append(
            Level(
                pk=int(obj["pk"]),
                name=f["name"],
                cardholders_included=int(f["cardholders_included"]),
                admissions_allowed=int(f["admissions_allowed"]),
                member_sale_ticket_allowance=int(f["member_sale_ticket_allowance"]),
                price=Decimal(str(f["price"])),
                active=bool(f.get("active", True)),
            )
        )
    return levels
