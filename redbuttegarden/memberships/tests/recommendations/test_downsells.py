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

    Current contract:
      - We should return at least one downsell slot when alternate memberships exist.
      - Downsell formulas are evaluated in order, and the first matching tuple wins.
      - If the fixture contains an exact (cardholders=1, guests=2) membership at the
        decremented ticket step, at least one downsell should use that match.
      - Otherwise, the service should move to the next configured fallback formula.
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
    assert downsells, "Expected at least one downsell slot when fixture alternatives exist"

    # Conditional: if a decremented-ticket exact-distribution level exists, ensure we pick it.
    prev = prev_ticket_step(tickets)
    assert prev is not None  # for tickets=2, this should be 0

    dec_exact_exists = any(
        l.active
        and l.cardholders_included == cardholders
        and l.admissions_allowed == guests
        and l.member_sale_ticket_allowance == prev
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
            "when such a level exists in the fixture."
        )
    else:
        assert rec.downsell_1 is not None
        assert rec.downsell_1_formula == "(C, G-1, T)"
        assert rec.downsell_1.cardholders_included == cardholders
        assert rec.downsell_1.admissions_allowed == guests - 1
        assert rec.downsell_1.member_sale_ticket_allowance == tickets


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
    assert rec.downsell_1_formula
    assert rec.downsell_2_formula


@pytest.mark.parametrize("cardholders", [1, 2, 3])
@pytest.mark.parametrize("guests", list(range(0, 9)))
@pytest.mark.parametrize("tickets", TICKET_STEPS)
def test_downsells_are_distinct_from_highlighted_and_annotated(
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

    valid_formulas = {
        "(C, G, prev(T))",
        "(C, G-1, T)",
        "(C-1, G+1, T)",
        "(C, G-2, T)",
        "price_fallback_2",
        "price_fallback_3",
    }

    if rec.downsell_1 is not None:
        assert rec.downsell_1.pk != rec.highlighted.pk
        assert rec.downsell_1_formula in valid_formulas

    if rec.downsell_2 is not None:
        assert rec.downsell_2.pk != rec.highlighted.pk
        assert rec.downsell_2_formula in valid_formulas

    if rec.downsell_1 is not None and rec.downsell_2 is not None:
        assert rec.downsell_1.pk != rec.downsell_2.pk
