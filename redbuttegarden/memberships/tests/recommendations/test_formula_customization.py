from decimal import Decimal

import pytest

from memberships.services.recommendations import (
    DEFAULT_PRICE_FALLBACK_FORMULAS,
    DEFAULT_RECOMMENDATION_FORMULAS,
    Level,
    PriceFallbackSpec,
    get_default_price_fallback_formulas,
    recommend_levels,
    resolve_price_fallback_formula,
    resolve_recommendation_formula,
    validate_price_fallback_formula,
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


def test_default_formulas_match_configured_recommendation_order():
    assert DEFAULT_RECOMMENDATION_FORMULAS == {
        "downsell_1": (
            "(C, G, prev(T))",
            "(C-1, G+1, T)",
            "(C, G-1, T)",
            "(C, G-2, T)",
            "(C-1, G+1, T+2)",
            "(C, G-1, T+2)",
            "(C, G-2, T+2)",
        ),
        "downsell_2": (
            "(C, G, prev(T))",
            "(C-1, G+1, T)",
            "(C, G-1, T)",
            "(C+1, G-2, T)",
            "(C, G-2, T)",
            "(C-1, G+1, T+2)",
            "(C-2, G+2, T+2)",
            "(C, G-1, T+2)",
            "(C+1, G-2, T+2)",
            "(C, G-2, T+2)",
            "(C+1, G-1, prev(T))",
            "(C, G-1, prev(T))",
            "(C-1, G, prev(T))",
            "(C+1, G-1, T)",
            "(C-2, G+2, T)",
            "(C-1, G, T)",
            "(C, G, next(T))",
            "(C, G+1, T)",
            "(C, G+2, T)",
        ),
        "upsell_1": (
            "(C, G, next(T))",
            "(C+1, G-1, T)",
            "(C, G+1, T)",
            "(C+2, G-2, T)",
            "(C, G+2, T)",
            "(C+1, G-1, T+2)",
            "(C, G+1, T+2)",
            "(C+2, G-2, T+2)",
            "(C, G+2, T+2)",
        ),
        "upsell_2": (
            "(C, G, next(T))",
            "(C+1, G-1, T)",
            "(C, G+1, next(T))",
            "(C, G+1, T)",
            "(C+2, G-2, T)",
            "(C+1, G-1, T+2)",
            "(C, G+1, T+2)",
            "(C+2, G-2, T+2)",
            "(C, G+2, T+2)",
            "(C, G, T+4)",
            "(C+1, G, T)",
        ),
    }
    assert DEFAULT_PRICE_FALLBACK_FORMULAS == {
        "downsell_1": "cheaper(1)",
        "downsell_2": "cheaper(2)",
        "upsell_1": "expensive(1)",
        "upsell_2": "expensive(2)",
    }
    assert get_default_price_fallback_formulas() == DEFAULT_PRICE_FALLBACK_FORMULAS


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


def test_custom_price_fallback_can_change_downsell_1_result():
    levels = [
        make_level(1, "Highlighted", 1, 2, 2, "100.00"),
        make_level(2, "Cheaper First", 1, 0, 0, "70.00"),
        make_level(3, "Cheaper Second", 1, 1, 0, "80.00"),
        make_level(4, "Upsell", 1, 3, 2, "120.00"),
    ]

    default_rec = recommend_levels(
        levels=levels,
        cardholders=1,
        guests=2,
        tickets=2,
        formulas={"downsell_1": ()},
    )
    assert default_rec.downsell_1 is not None
    assert default_rec.downsell_1.name == "Cheaper First"
    assert default_rec.downsell_1_formula == "cheaper(1)"

    custom_rec = recommend_levels(
        levels=levels,
        cardholders=1,
        guests=2,
        tickets=2,
        formulas={"downsell_1": ()},
        price_fallbacks={"downsell_1": "cheaper(2)"},
    )
    assert custom_rec.downsell_1 is not None
    assert custom_rec.downsell_1.name == "Cheaper Second"
    assert custom_rec.downsell_1_formula == "cheaper(2)"


def test_custom_price_fallback_can_limit_candidates_by_requested_dimensions():
    levels = [
        make_level(1, "Highlighted", 1, 2, 2, "100.00"),
        make_level(2, "Cheapest Same Cardholders", 1, 0, 0, "70.00"),
        make_level(3, "Same Cardholders And Guests", 1, 2, 0, "90.00"),
        make_level(4, "Upsell", 1, 3, 2, "120.00"),
    ]

    default_rec = recommend_levels(
        levels=levels,
        cardholders=1,
        guests=2,
        tickets=2,
        formulas={"downsell_1": ()},
    )
    assert default_rec.downsell_1 is not None
    assert default_rec.downsell_1.name == "Cheapest Same Cardholders"
    assert default_rec.downsell_1_formula == "cheaper(1)"

    filtered_rec = recommend_levels(
        levels=levels,
        cardholders=1,
        guests=2,
        tickets=2,
        formulas={"downsell_1": ()},
        price_fallbacks={"downsell_1": "cheaper(1; match=cardholders,guests)"},
    )
    assert filtered_rec.downsell_1 is not None
    assert filtered_rec.downsell_1.name == "Same Cardholders And Guests"
    assert filtered_rec.downsell_1_formula == "cheaper(1; match=cardholders,guests)"


def test_default_price_fallback_widens_when_no_preferred_dimension_matches():
    levels = [
        make_level(1, "Highlighted", 3, 2, 2, "100.00"),
        make_level(2, "Only Remaining Option", 2, 2, 2, "90.00"),
    ]

    rec = recommend_levels(
        levels=levels,
        cardholders=3,
        guests=2,
        tickets=2,
        formulas={"downsell_1": ()},
    )

    assert rec.downsell_1 is not None
    assert rec.downsell_1.name == "Only Remaining Option"
    assert rec.downsell_1_formula == "cheaper(1)"


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
    assert (
        resolve_recommendation_formula(
            "(C, G, T+2)",
            cardholders=1,
            guests=2,
            tickets=2,
        )
        == (1, 2, 4)
    )
    assert (
        resolve_recommendation_formula(
            "(C, G, T+4)",
            cardholders=1,
            guests=2,
            tickets=2,
        )
        == (1, 2, 6)
    )
    assert (
        resolve_recommendation_formula(
            "(C, G, T-2)",
            cardholders=1,
            guests=2,
            tickets=2,
        )
        == (1, 2, 0)
    )
    assert (
        resolve_recommendation_formula(
            "(C, G, T+1)",
            cardholders=1,
            guests=2,
            tickets=2,
        )
        is None
    )
    assert resolve_price_fallback_formula("cheaper(2)") == PriceFallbackSpec(
        direction="cheaper",
        n=2,
        prefer_dimensions=("cardholders",),
        match_dimensions=(),
    )
    assert resolve_price_fallback_formula(
        "expensive(1; prefer=guests; match=cardholders,guests)"
    ) == PriceFallbackSpec(
        direction="expensive",
        n=1,
        prefer_dimensions=("guests",),
        match_dimensions=("cardholders", "guests"),
    )


@pytest.mark.parametrize(
    "formula",
    ("C, G, T", "(C, G)", "(C, G, bad(T))", "(C+, G, T)"),
)
def test_formula_validation_rejects_invalid_syntax(formula):
    with pytest.raises(ValueError):
        validate_recommendation_formula(formula)


@pytest.mark.parametrize(
    "formula",
    (
        "price_fallback_2",
        "cheaper()",
        "closest(1)",
        "cheaper(1; match=color)",
        "expensive(1; unknown=guests)",
    ),
)
def test_price_fallback_validation_rejects_invalid_syntax(formula):
    with pytest.raises(ValueError):
        validate_price_fallback_formula(formula)
