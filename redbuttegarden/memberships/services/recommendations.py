from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional, Sequence


@dataclass(frozen=True)
class Level:
    pk: int
    name: str
    cardholders_included: int
    admissions_allowed: int  # guests per visit
    member_sale_ticket_allowance: int
    price: Decimal
    active: bool = True


@dataclass(frozen=True)
class RecommendationResult:
    match_type: Optional[str]  # "Exact", "Best", or None
    highlighted: Optional[Level]
    suggestions: List[Level]


def recommend_levels(
    *,
    levels: Sequence[Level],
    cardholders: int,
    guests: int,
    tickets: int,
    suggestion_slots: int = 4,
) -> RecommendationResult:
    """
    Mirrors the spreadsheet behavior you described:
    - pool: active levels with matching cardholders, ordered by (price, pk)
    - highlighted: Exact first else Best (same guests; tickets >= requested; smallest ticket allowance then cheapest)
    - suggestions: fill fixed count from the same pool using your "cheaper then fill forward" scheme
    """
    pool = sorted(
        [l for l in levels if l.active and l.cardholders_included == cardholders],
        key=lambda l: (l.price, l.pk),
    )

    # Exact
    exact = [
        l
        for l in pool
        if l.admissions_allowed == guests and l.member_sale_ticket_allowance == tickets
    ]
    exact.sort(key=lambda l: (l.price, l.pk))
    highlighted = exact[0] if exact else None
    match_type = "Exact" if highlighted else None

    # Best
    if highlighted is None:
        best = [
            l
            for l in pool
            if l.admissions_allowed == guests
            and l.member_sale_ticket_allowance >= tickets
        ]
        best.sort(key=lambda l: (l.member_sale_ticket_allowance, l.price, l.pk))
        highlighted = best[0] if best else None
        match_type = "Best" if highlighted else None

    if highlighted is None:
        return RecommendationResult(match_type=None, highlighted=None, suggestions=[])

    # Suggestions: prefer up to 2 cheaper than highlighted, then fill forward
    try:
        idx = next(i for i, l in enumerate(pool) if l.pk == highlighted.pk)
    except StopIteration:
        # extremely unlikely; fall back to "first N not highlighted"
        suggestions = [l for l in pool if l.pk != highlighted.pk][:suggestion_slots]
        return RecommendationResult(
            match_type=match_type, highlighted=highlighted, suggestions=suggestions
        )

    picks: List[Level] = []

    # up to 2 cheaper
    cheaper = pool[max(idx - 2, 0) : idx]
    picks.extend(cheaper)

    # if fewer than 2 cheaper, fill from after highlighted
    needed = 2 - len(cheaper)
    cursor = idx + 1
    if needed > 0:
        picks.extend(pool[cursor : cursor + needed])
        cursor += needed

    # fill remaining continuing forward
    remaining = suggestion_slots - len(picks)
    if remaining > 0:
        picks.extend(pool[cursor : cursor + remaining])

    # de-dupe and remove highlighted
    seen = {highlighted.pk}
    suggestions: List[Level] = []
    for l in picks:
        if l.pk in seen:
            continue
        seen.add(l.pk)
        suggestions.append(l)

    return RecommendationResult(
        match_type=match_type, highlighted=highlighted, suggestions=suggestions
    )
