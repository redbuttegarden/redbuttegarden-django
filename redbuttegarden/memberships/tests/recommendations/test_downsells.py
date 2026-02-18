import pytest
from memberships.services.recommendations import recommend_levels

TICKET_STEPS = (0, 2, 4, 6)


def prev_ticket_step(tickets: int):
    prev = None
    for v in TICKET_STEPS:
        if v < tickets:
            prev = v
        else:
            break
    return prev


def test_downsells_use_ticket_decrement_when_available_else_fallback(
    levels_from_fixture,
):
    """
    Regression for: input (1 cardholder, 2 guests, 2 tickets)

    New contract:
      - We must return at least one downsell (when any cheaper membership exists).
      - Downsells must be cheaper than highlighted.
      - If the fixture contains an exact (cardholders=1, guests=2) membership at the decremented ticket step,
        then at least one downsell should be that exact distribution with fewer tickets.
      - Otherwise, we should still return downsells via "closest feasible cheaper" fallback.
    """
    cardholders, guests, tickets = 1, 2, 2
    rec = recommend_levels(
        levels=levels_from_fixture,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )

    assert rec.highlighted is not None, "Expected a highlighted match from fixture data"

    downsells = [d for d in (rec.downsell_1, rec.downsell_2) if d is not None]
    assert downsells, "Expected at least one downsell when cheaper memberships exist"

    # Downsells must be cheaper than highlighted under the current logic
    assert all(d.price < rec.highlighted.price for d in downsells)

    # Conditional: if a decremented-ticket exact-distribution level exists, ensure we pick it.
    prev = prev_ticket_step(tickets)
    assert prev is not None  # for tickets=2, this should be 0

    dec_exact_exists = any(
        l.active
        and l.cardholders_included == cardholders
        and l.admissions_allowed == guests
        and l.member_sale_ticket_allowance == prev
        and l.price < rec.highlighted.price
        for l in levels_from_fixture
    )

    if dec_exact_exists:
        assert any(
            d.cardholders_included == cardholders
            and d.admissions_allowed == guests
            and d.member_sale_ticket_allowance == prev
            for d in downsells
        ), (
            "Expected a downsell with same cardholders+guests at the decremented ticket step "
            "when such a cheaper level exists in the fixture."
        )
    else:
        # Fallback expectation: at least one downsell should be "close" in total admissions.
        req_total = cardholders + guests
        assert any(
            (d.cardholders_included + d.admissions_allowed)
            in {req_total, req_total - 1, req_total + 1}
            for d in downsells
        ), (
            "No decremented-ticket exact-distribution level exists; expected fallback downsell(s) "
            "to be reasonably close in total admissions."
        )


def test_returns_two_distinct_downsells_when_fixture_allows(levels_from_fixture):
    rec = recommend_levels(
        levels=levels_from_fixture,
        cardholders=1,
        guests=2,
        tickets=2,
    )

    downsells = [d for d in (rec.downsell_1, rec.downsell_2) if d is not None]
    # If you want this to ALWAYS be true for this input, keep it strict:
    assert len(downsells) == 2, "Expected two downsell slots for this input"

    assert downsells[0].pk != downsells[1].pk, "Downsells must be distinct"
    assert all(
        d.price < rec.highlighted.price for d in downsells
    ), "Downsells must be cheaper than highlighted"


@pytest.mark.parametrize("cardholders", [1, 2, 3])
@pytest.mark.parametrize("guests", list(range(0, 9)))
@pytest.mark.parametrize("tickets", TICKET_STEPS)
def test_downsells_are_never_more_expensive(
    levels_from_fixture, cardholders, guests, tickets
):
    rec = recommend_levels(
        levels=levels_from_fixture,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )
    if not rec.highlighted:
        return

    for d in (rec.downsell_1, rec.downsell_2):
        if d is None:
            continue
        assert d.price < rec.highlighted.price, (
            f"Downsell must be cheaper than highlighted for input "
            f"({cardholders=}, {guests=}, {tickets=})"
        )
