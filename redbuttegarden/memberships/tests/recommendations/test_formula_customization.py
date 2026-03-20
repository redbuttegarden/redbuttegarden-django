from decimal import Decimal

import pytest

from memberships.services.recommendations import (
    Level,
    recommend_levels,
    resolve_recommendation_formula,
    validate_recommendation_formula,
)


def make_level(pk, name, cardholders, guests, tickets, price):
    return Level(
        pk=pk,
        name=name,
        cardholders_included=cardholders,
        admissions_allowed=guests,
        member_sale_ticket_allowance=tickets,
        price=Decimal(price),
    )


def test_custom_formula_can_change_downsell_1_result():
    levels = [
        make_level(1, "Highlighted", 1, 2, 2, "100.00"),
        make_level(2, "Default Downsell", 1, 2, 0, "80.00"),
        make_level(3, "Custom Downsell", 2, 2, 0, "90.00"),
        make_level(4, "Fallback Downsell", 1, 1, 2, "70.00"),
        make_level(5, "Upsell", 1, 3, 2, "120.00"),
    ]

    default_rec = recommend_levels(
        levels=levels,
        cardholders=1,
        guests=2,
        tickets=2,
    )
    assert default_rec.downsell_1 is not None
    assert default_rec.downsell_1.name == "Default Downsell"
    assert default_rec.downsell_1_formula == "(C, G, prev(T))"

    custom_rec = recommend_levels(
        levels=levels,
        cardholders=1,
        guests=2,
        tickets=2,
        formulas={"downsell_1": ("(C+1, G, prev(T))",)},
    )
    assert custom_rec.downsell_1 is not None
    assert custom_rec.downsell_1.name == "Custom Downsell"
    assert custom_rec.downsell_1_formula == "(C+1, G, prev(T))"


def test_formula_resolution_supports_offsets_and_prev_next():
    assert (
        resolve_recommendation_formula(
            "(C+1, G-2, prev(T))",
            cardholders=1,
            guests=4,
            tickets=2,
        )
        == (2, 2, 0)
    )
    assert (
        resolve_recommendation_formula(
            "(C, G+1, next(T)-2)",
            cardholders=1,
            guests=2,
            tickets=2,
        )
        == (1, 3, 2)
    )


@pytest.mark.parametrize(
    "formula",
    ("C, G, T", "(C, G)", "(C, G, bad(T))", "(C+, G, T)"),
)
def test_formula_validation_rejects_invalid_syntax(formula):
    with pytest.raises(ValueError):
        validate_recommendation_formula(formula)
