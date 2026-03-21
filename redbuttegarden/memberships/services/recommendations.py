from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Mapping, Optional, Sequence, Set, Tuple


logger = logging.getLogger(__name__)

TICKET_STEPS: Tuple[int, ...] = (0, 2, 4, 6)
RECOMMENDATION_SLOT_ORDER: Tuple[str, ...] = (
    "downsell_1",
    "downsell_2",
    "upsell_1",
    "upsell_2",
)
DEFAULT_RECOMMENDATION_FORMULAS: dict[str, Tuple[str, ...]] = {
    "downsell_1": ("(C, G, prev(T))", "(C, G-1, T)"),
    "downsell_2": ("(C-1, G+1, T)", "(C, G-1, T)", "(C, G-2, T)"),
    "upsell_1": ("(C, G, next(T))", "(C, G+1, T)"),
    "upsell_2": ("(C+1, G-1, T)", "(C, G+1, T)", "(C, G+2, T)"),
}
PRICE_FALLBACK_FORMULAS: dict[str, str] = {
    "downsell_1": "price_fallback_2",
    "downsell_2": "price_fallback_3",
    "upsell_1": "price_fallback_2",
    "upsell_2": "price_fallback_3",
}
FORMULA_EXPRESSION_TOKEN_RE = re.compile(r"\s*(prev\(T\)|next\(T\)|[CGT]|\d+|[+-])")


@dataclass(frozen=True)
class Level:
    pk: int
    name: str
    cardholders_included: int
    admissions_allowed: int  # guests
    member_sale_ticket_allowance: int
    price: Decimal
    active: bool = True


@dataclass(frozen=True)
class RecommendationResult:
    match_type: Optional[str]  # "Exact", "Best", or None

    highlighted: Optional[Level]
    highlighted_formula: Optional[str]

    downsell_1: Optional[Level]
    downsell_1_formula: Optional[str]

    downsell_2: Optional[Level]
    downsell_2_formula: Optional[str]

    upsell_1: Optional[Level]
    upsell_1_formula: Optional[str]

    upsell_2: Optional[Level]
    upsell_2_formula: Optional[str]


def get_default_recommendation_formulas() -> dict[str, Tuple[str, ...]]:
    return {
        slot: tuple(formulas)
        for slot, formulas in DEFAULT_RECOMMENDATION_FORMULAS.items()
    }


def _next_step(tickets: int) -> Optional[int]:
    for v in TICKET_STEPS:
        if v > tickets:
            return v
    return None


def _prev_step(tickets: int) -> Optional[int]:
    prev = None
    for v in TICKET_STEPS:
        if v < tickets:
            prev = v
        else:
            break
    return prev


def _parse_formula_expression(expression: str) -> List[str]:
    expression = expression.strip()
    if not expression:
        raise ValueError("Expression cannot be empty.")

    pos = 0
    tokens: List[str] = []
    expecting_term = True
    while pos < len(expression):
        match = FORMULA_EXPRESSION_TOKEN_RE.match(expression, pos)
        if not match:
            raise ValueError(f"Unsupported token near '{expression[pos:]}'")

        token = match.group(1)
        pos = match.end()

        if expecting_term:
            if token in {"+", "-"}:
                raise ValueError("Expected a variable, function, or integer.")
            tokens.append(token)
            expecting_term = False
            continue

        if token not in {"+", "-"}:
            raise ValueError("Expected '+' or '-'.")
        tokens.append(token)
        expecting_term = True

    if expecting_term:
        raise ValueError("Expression cannot end with an operator.")

    return tokens


def _evaluate_formula_expression(
    expression: str, *, cardholders: int, guests: int, tickets: int
) -> Optional[int]:
    def resolve_term(token: str) -> Optional[int]:
        if token == "C":
            return cardholders
        if token == "G":
            return guests
        if token == "T":
            return tickets
        if token == "prev(T)":
            return _prev_step(tickets)
        if token == "next(T)":
            return _next_step(tickets)
        return int(token)

    tokens = _parse_formula_expression(expression)
    value = resolve_term(tokens[0])
    if value is None:
        return None

    for i in range(1, len(tokens), 2):
        operator = tokens[i]
        term_value = resolve_term(tokens[i + 1])
        if term_value is None:
            return None
        if operator == "+":
            value += term_value
        else:
            value -= term_value

    return value


def validate_recommendation_formula(formula: str) -> None:
    formula = formula.strip()
    if not formula.startswith("(") or not formula.endswith(")"):
        raise ValueError("Formula must use the format '(expr, expr, expr)'.")

    parts = [part.strip() for part in formula[1:-1].split(",")]
    if len(parts) != 3 or any(not part for part in parts):
        raise ValueError("Formula must contain exactly three expressions.")

    for part in parts:
        _parse_formula_expression(part)


def resolve_recommendation_formula(
    formula: str, *, cardholders: int, guests: int, tickets: int
) -> Optional[tuple[int, int, int]]:
    validate_recommendation_formula(formula)
    parts = [part.strip() for part in formula.strip()[1:-1].split(",")]
    resolved = tuple(
        _evaluate_formula_expression(
            part,
            cardholders=cardholders,
            guests=guests,
            tickets=tickets,
        )
        for part in parts
    )
    if any(value is None or value < 0 for value in resolved):
        return None
    return resolved  # type: ignore[return-value]


def _normalize_recommendation_formulas(
    formulas: Optional[Mapping[str, Sequence[str]]],
) -> dict[str, Tuple[str, ...]]:
    normalized = get_default_recommendation_formulas()
    if not formulas:
        return normalized

    unknown_slots = set(formulas.keys()) - set(RECOMMENDATION_SLOT_ORDER)
    if unknown_slots:
        unknown = ", ".join(sorted(unknown_slots))
        raise ValueError(f"Unknown recommendation slots: {unknown}")

    for slot in RECOMMENDATION_SLOT_ORDER:
        if slot not in formulas:
            continue
        slot_formulas = tuple(
            formula.strip() for formula in formulas[slot] if formula and formula.strip()
        )
        for formula in slot_formulas:
            validate_recommendation_formula(formula)
        normalized[slot] = slot_formulas

    return normalized


def _build_index(levels: Sequence[Level]) -> dict[tuple[int, int, int], Level]:
    """
    Uniqueness constraint guarantees a single (active) level per entitlement triple.
    """
    idx: dict[tuple[int, int, int], Level] = {}
    for l in levels:
        if not l.active:
            continue
        idx[
            (
                l.cardholders_included,
                l.admissions_allowed,
                l.member_sale_ticket_allowance,
            )
        ] = l
    return idx


def _sorted_by_price(levels: Iterable[Level]) -> List[Level]:
    return sorted(levels, key=lambda l: (l.price, l.pk))


def _closest_by_price_sorted(
    *,
    all_active_sorted: Sequence[Level],
    highlighted: Level,
    exclude: Set[int],
) -> List[Level]:
    """
    Candidates ordered by absolute distance from highlighted.price, then by price, then pk.
    Deterministic and stable. Includes cheaper, equal, and more expensive.
    """
    hp = highlighted.price
    cands = [l for l in all_active_sorted if l.pk not in exclude]
    cands.sort(key=lambda l: (abs(l.price - hp), l.price, l.pk))
    return cands


def _pick_nth_prefer_band_else_closest(
    *,
    all_active_sorted: Sequence[Level],
    highlighted: Level,
    exclude: Set[int],
    n: int,
    prefer: str,
) -> Optional[Level]:
    """
    Always tries to return something (unless there are no non-excluded levels).

    prefer:
      - "cheaper": prefer strictly cheaper-than-highlighted with same number of cardholders, else fill from closest-by-price overall
      - "expensive": prefer strictly more-expensive-than-highlighted with same number of cardholders, else fill from closest-by-price overall

    n=1 returns first pick, n=2 returns second pick, etc. This function does NOT mutate exclude.
    """
    if n <= 0:
        raise ValueError("n must be >= 1")

    remaining = [l for l in all_active_sorted if l.pk not in exclude if l.cardholders_included == highlighted.cardholders_included]
    if not remaining:
        return None

    if prefer == "cheaper":
        primary = [l for l in remaining if l.price < highlighted.price]
    elif prefer == "expensive":
        primary = [l for l in remaining if l.price > highlighted.price]
    else:
        raise ValueError("prefer must be 'cheaper' or 'expensive'")
    primary.sort(key=lambda l: (l.price, l.pk))

    # If we have enough in the preferred band, just return that nth.
    if len(primary) >= n:
        return primary[n - 1]

    # Otherwise, build a combined list:
    #   - all preferred-band candidates first (already sorted)
    #   - then fill the rest with closest-by-price candidates not already included
    picked_pks = {l.pk for l in primary}
    closest = _closest_by_price_sorted(
        all_active_sorted=all_active_sorted, highlighted=highlighted, exclude=exclude
    )
    fill = [l for l in closest if l.pk not in picked_pks]

    combined = primary + fill
    return (
        combined[n - 1] if len(combined) >= n else (combined[0] if combined else None)
    )


def _pick_formula_candidate(
    *,
    idx: Mapping[tuple[int, int, int], Level],
    formulas: Sequence[str],
    exclude: Set[int],
    cardholders: int,
    guests: int,
    tickets: int,
) -> tuple[Optional[Level], str]:
    for formula in formulas:
        resolved = resolve_recommendation_formula(
            formula,
            cardholders=cardholders,
            guests=guests,
            tickets=tickets,
        )
        if resolved is None:
            continue

        cand = idx.get(resolved)
        if cand and cand.pk not in exclude:
            return cand, formula

    return None, ""


def recommend_levels(
    *,
    levels: Sequence[Level],
    cardholders: int,
    guests: int,
    tickets: int,
    formulas: Optional[Mapping[str, Sequence[str]]] = None,
) -> RecommendationResult:
    logger.debug(f"Getting recommendations for C: {cardholders}, G: {guests}, T: {tickets}")
    active = [l for l in levels if l.active]
    if not active:
        return RecommendationResult(
            match_type=None,
            highlighted=None,
            highlighted_formula=None,
            downsell_1=None,
            downsell_1_formula=None,
            downsell_2=None,
            downsell_2_formula=None,
            upsell_1=None,
            upsell_1_formula=None,
            upsell_2=None,
            upsell_2_formula=None,
        )

    idx = _build_index(active)
    all_active_sorted = _sorted_by_price(active)
    normalized_formulas = _normalize_recommendation_formulas(formulas)

    d1_formula = ""
    d2_formula = ""
    u1_formula = ""
    u2_formula = ""

    # -------- Highlighted --------
    exact = idx.get((cardholders, guests, tickets))
    if exact:
        highlighted = exact
        match_type = "Exact"
        highlighted_formula = "exact"
    else:
        # Best: same (C,G), ignore tickets, pick smallest ticket allowance >= requested else smallest available
        available = [
            l
            for l in active
            if l.cardholders_included == cardholders and l.admissions_allowed == guests
        ]
        if not available:
            return RecommendationResult(
                match_type=None,
                highlighted=None,
                highlighted_formula=None,
                downsell_1=None,
                downsell_1_formula=None,
                downsell_2=None,
                downsell_2_formula=None,
                upsell_1=None,
                upsell_1_formula=None,
                upsell_2=None,
                upsell_2_formula=None,
            )

        available.sort(key=lambda l: (l.member_sale_ticket_allowance, l.price, l.pk))
        above_or_equal = [
            l for l in available if l.member_sale_ticket_allowance >= tickets
        ]
        highlighted = above_or_equal[0] if above_or_equal else available[0]
        match_type = "Best"
        highlighted_formula = (
            "best_same_cg_ticket_gte"
            if above_or_equal
            else "best_same_cg_smallest_ticket"
        )

    exclude: Set[int] = {highlighted.pk}

    # -----------------------------
    # Downsell 1
    # -----------------------------
    d1: Optional[Level] = None
    d1, d1_formula = _pick_formula_candidate(
        idx=idx,
        formulas=normalized_formulas["downsell_1"],
        exclude=exclude,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )
    if d1:
        logger.debug(
            "Downsell 1 formula %s hit -> pk=%s price=%s",
            d1_formula,
            d1.pk,
            d1.price,
        )

    # 3) price fallback: prefer cheaper, else closest-by-price
    if d1 is None:
        d1 = _pick_nth_prefer_band_else_closest(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=1,
            prefer="cheaper",
        )
        if d1:
            d1_formula = PRICE_FALLBACK_FORMULAS["downsell_1"]
            logger.debug(
                "Downsell 1 final fallback #2 prefer-cheaper-else-closest -> pk=%s price=%s (highlighted=%s)",
                d1.pk,
                d1.price,
                highlighted.price,
            )

    if d1:
        exclude.add(d1.pk)

    # -----------------------------
    # Downsell 2
    # -----------------------------
    d2: Optional[Level] = None
    d2, d2_formula = _pick_formula_candidate(
        idx=idx,
        formulas=normalized_formulas["downsell_2"],
        exclude=exclude,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )
    if d2:
        logger.debug(
            "Downsell 2 formula %s hit -> pk=%s price=%s",
            d2_formula,
            d2.pk,
            d2.price,
        )

    # 4) price fallback: prefer cheaper, else closest-by-price (2nd pick)
    if d2 is None:
        d2 = _pick_nth_prefer_band_else_closest(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=2,
            prefer="cheaper",
        )
        if d2:
            d2_formula = PRICE_FALLBACK_FORMULAS["downsell_2"]
            logger.debug(
                "Downsell 2 price final fallback #3 prefer-cheaper-else-closest (#2) -> pk=%s price=%s (highlighted=%s)",
                d2.pk,
                d2.price,
                highlighted.price,
            )

    if d2:
        exclude.add(d2.pk)

    # -----------------------------
    # Upsell 1
    # -----------------------------
    u1: Optional[Level] = None
    u1, u1_formula = _pick_formula_candidate(
        idx=idx,
        formulas=normalized_formulas["upsell_1"],
        exclude=exclude,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )
    if u1:
        logger.debug(
            "Upsell 1 formula %s hit -> pk=%s price=%s",
            u1_formula,
            u1.pk,
            u1.price,
        )

    # 3) price fallback: prefer more expensive, else closest-by-price
    if u1 is None:
        u1 = _pick_nth_prefer_band_else_closest(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=1,
            prefer="expensive",
        )
        if u1:
            u1_formula = PRICE_FALLBACK_FORMULAS["upsell_1"]
            logger.debug(
                "Upsell 1 final fallback #2 prefer-expensive-else-closest -> pk=%s price=%s (highlighted=%s)",
                u1.pk,
                u1.price,
                highlighted.price,
            )

    if u1:
        exclude.add(u1.pk)

    # -----------------------------
    # Upsell 2
    # -----------------------------
    u2: Optional[Level] = None
    u2, u2_formula = _pick_formula_candidate(
        idx=idx,
        formulas=normalized_formulas["upsell_2"],
        exclude=exclude,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )
    if u2:
        logger.debug(
            "Upsell 2 formula %s hit -> pk=%s price=%s",
            u2_formula,
            u2.pk,
            u2.price,
        )

    # 4) price fallback: prefer more expensive, else closest-by-price (2nd pick)
    if u2 is None:
        u2 = _pick_nth_prefer_band_else_closest(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=2,
            prefer="expensive",
        )
        if u2:
            u2_formula = PRICE_FALLBACK_FORMULAS["upsell_2"]
            logger.debug(
                "Upsell 2 final fallback #3 prefer-expensive-else-closest (#2) -> pk=%s price=%s (highlighted=%s)",
                u2.pk,
                u2.price,
                highlighted.price,
            )

    if u2:
        exclude.add(u2.pk)

    return RecommendationResult(
        match_type=match_type,
        highlighted=highlighted,
        highlighted_formula=highlighted_formula,
        downsell_1=d1,
        downsell_1_formula=d1_formula,
        downsell_2=d2,
        downsell_2_formula=d2_formula,
        upsell_1=u1,
        upsell_1_formula=u1_formula,
        upsell_2=u2,
        upsell_2_formula=u2_formula,
    )
