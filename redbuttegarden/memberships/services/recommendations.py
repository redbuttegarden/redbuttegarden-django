from __future__ import annotations

import logging
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence, Set, Tuple


logger = logging.getLogger(__name__)

TICKET_STEPS: Tuple[int, ...] = (0, 2, 4, 6)


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
    downsell_1: Optional[Level]
    downsell_2: Optional[Level]
    upsell_1: Optional[Level]
    upsell_2: Optional[Level]


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


def recommend_levels(
    *,
    levels: Sequence[Level],
    cardholders: int,
    guests: int,
    tickets: int,
) -> RecommendationResult:
    active = [l for l in levels if l.active]
    if not active:
        return RecommendationResult(None, None, None, None, None, None)

    idx = _build_index(active)
    all_active_sorted = _sorted_by_price(active)

    # -------- Highlighted --------
    exact = idx.get((cardholders, guests, tickets))
    if exact:
        highlighted = exact
        match_type = "Exact"
    else:
        # Best: same (C,G), ignore tickets, pick smallest ticket allowance >= requested else smallest available
        available = [
            l
            for l in active
            if l.cardholders_included == cardholders and l.admissions_allowed == guests
        ]
        if not available:
            return RecommendationResult(None, None, None, None, None, None)

        available.sort(key=lambda l: (l.member_sale_ticket_allowance, l.price, l.pk))
        above_or_equal = [
            l for l in available if l.member_sale_ticket_allowance >= tickets
        ]
        highlighted = above_or_equal[0] if above_or_equal else available[0]
        match_type = "Best"

    exclude: Set[int] = {highlighted.pk}

    # -----------------------------
    # Downsell 1
    # -----------------------------
    d1: Optional[Level] = None
    prev_req = _prev_step(tickets)

    # 1) (C, G, prev(T))
    if prev_req is not None:
        cand = idx.get((cardholders, guests, prev_req))
        if cand and cand.pk not in exclude:
            d1 = cand
            logger.debug(
                "Downsell 1 primary (C,G,prevT) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
            )

    # 2) (C, G-1, T)
    if d1 is None and guests > 0:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            d1 = cand
            logger.debug(
                "Downsell 1 fallback (C,G-1,T) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
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
            logger.debug(
                "Downsell 1 price fallback prefer-cheaper-else-closest -> pk=%s price=%s (highlighted=%s)",
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

    # 1) (C-1, G+1, T)
    if cardholders > 1:
        cand = idx.get((cardholders - 1, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 fallback (C-1,G+1,T) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
            )

    # 2) (C, G-1, T)
    if d2 is None and guests >= 1:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 fallback (C,G-1,T) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
            )

    # 3) (C, G-2, T)
    if d2 is None and guests >= 2:
        cand = idx.get((cardholders, guests - 2, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 fallback (C,G-2,T) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
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
            logger.debug(
                "Downsell 2 price fallback prefer-cheaper-else-closest (#2) -> pk=%s price=%s (highlighted=%s)",
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
    next_req = _next_step(tickets)

    # 1) (C, G, next(T))
    if next_req is not None:
        cand = idx.get((cardholders, guests, next_req))
        if cand and cand.pk not in exclude:
            u1 = cand
            logger.debug(
                "Upsell 1 primary (C,G,nextT) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
            )

    # 2) (C, G+1, T)
    if u1 is None:
        cand = idx.get((cardholders, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            u1 = cand
            logger.debug(
                "Upsell 1 fallback (C,G+1,T) hit -> pk=%s price=%s", cand.pk, cand.price
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
            logger.debug(
                "Upsell 1 price fallback prefer-expensive-else-closest -> pk=%s price=%s (highlighted=%s)",
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

    # 1) (C+1, G-1, T)  [preserve total admissions]
    if guests >= 1:
        cand = idx.get((cardholders + 1, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            u2 = cand
            logger.debug(
                "Upsell 2 fallback (C+1,G-1,T) hit -> pk=%s price=%s",
                cand.pk,
                cand.price,
            )

    # 2) (C, G+1, T)
    if u2 is None:
        cand = idx.get((cardholders, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            u2 = cand
            logger.debug(
                "Upsell 2 fallback (C,G+1,T) hit -> pk=%s price=%s", cand.pk, cand.price
            )

    # 3) (C, G+2, T)
    if u2 is None:
        cand = idx.get((cardholders, guests + 2, tickets))
        if cand and cand.pk not in exclude:
            u2 = cand
            logger.debug(
                "Upsell 2 fallback (C,G+2,T) hit -> pk=%s price=%s", cand.pk, cand.price
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
            logger.debug(
                "Upsell 2 price fallback prefer-expensive-else-closest (#2) -> pk=%s price=%s (highlighted=%s)",
                u2.pk,
                u2.price,
                highlighted.price,
            )

    if u2:
        exclude.add(u2.pk)

    return RecommendationResult(
        match_type=match_type,
        highlighted=highlighted,
        downsell_1=d1,
        downsell_2=d2,
        upsell_1=u1,
        upsell_2=u2,
    )
