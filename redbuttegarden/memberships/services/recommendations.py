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


def _total_adm(cardholders: int, guests: int) -> int:
    return cardholders + guests


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
        idx[(l.cardholders_included, l.admissions_allowed, l.member_sale_ticket_allowance)] = l
    return idx


def _sorted_by_price(levels: Iterable[Level]) -> List[Level]:
    return sorted(levels, key=lambda l: (l.price, l.pk))


def _nth_cheapest_after_highlighted(
    *,
    all_active_sorted: Sequence[Level],
    highlighted: Level,
    exclude: Set[int],
    n: int,
) -> Optional[Level]:
    """
    Return the nth cheapest membership AFTER highlighted in global price ordering,
    skipping excluded items. n=1 => next cheapest, n=2 => next-next cheapest.
    If not enough after highlighted, fall back to nth overall non-excluded if possible else cheapest.
    """
    if n <= 0:
        raise ValueError("n must be >= 1")

    non_excluded = [l for l in all_active_sorted if l.pk not in exclude]
    if not non_excluded:
        return None

    try:
        idx_h = next(i for i, l in enumerate(all_active_sorted) if l.pk == highlighted.pk)
    except StopIteration:
        return non_excluded[n - 1] if len(non_excluded) >= n else non_excluded[0]

    found = 0
    for j in range(idx_h + 1, len(all_active_sorted)):
        cand = all_active_sorted[j]
        if cand.pk in exclude:
            continue
        found += 1
        if found == n:
            return cand

    return non_excluded[n - 1] if len(non_excluded) >= n else non_excluded[0]


def _nth_most_expensive_after_highlighted(
    *,
    all_active_sorted: Sequence[Level],
    highlighted: Level,
    exclude: Set[int],
    n: int,
) -> Optional[Level]:
    """
    Reverse of _nth_cheapest_after_highlighted:
    Return the nth most expensive membership AFTER highlighted, meaning:
      - sort ascending by price
      - walk backwards from highlighted to find more expensive options? (actually "more expensive" is AFTER in price order)
    Since list is ascending, "more expensive after highlighted" is *forward*.
    For symmetry with downsells, we interpret:
      Upsell 1 fallback = next MORE EXPENSIVE after highlighted (n=1),
      Upsell 2 fallback = next-next MORE EXPENSIVE after highlighted (n=2).

    This is actually identical traversal direction as "cheapest after highlighted" because both scan forward.
    The difference is only conceptual; we keep a separate function for clarity/logging.
    """
    return _nth_cheapest_after_highlighted(
        all_active_sorted=all_active_sorted,
        highlighted=highlighted,
        exclude=exclude,
        n=n,
    )


def recommend_levels(
    *,
    levels: Sequence[Level],
    cardholders: int,
    guests: int,
    tickets: int,
) -> RecommendationResult:
    active = [l for l in levels if l.active]
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
            l for l in active
            if l.cardholders_included == cardholders and l.admissions_allowed == guests
        ]
        if not available:
            return RecommendationResult(None, None, None, None, None, None)

        available.sort(key=lambda l: (l.member_sale_ticket_allowance, l.price, l.pk))
        above_or_equal = [l for l in available if l.member_sale_ticket_allowance >= tickets]
        highlighted = above_or_equal[0] if above_or_equal else available[0]
        match_type = "Best"

    exclude: Set[int] = {highlighted.pk}

    # -------- Downsell 1 --------
    prev_req = _prev_step(tickets)
    d1: Optional[Level] = None

    # 1) (C, G, prev(T))
    if prev_req is not None:
        cand = idx.get((cardholders, guests, prev_req))
        if cand and cand.pk not in exclude:
            d1 = cand
            logger.debug(
                "Downsell 1 selected via primary (C,G,prevT) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Downsell 1 primary (C,G,prevT) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 2) (C, G-1, T)
    if d1 is None and guests > 0:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            d1 = cand
            logger.debug(
                "Downsell 1 selected via fallback #1 (C,G-1,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Downsell 1 fallback #1 (C,G-1,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 3) next cheapest after highlighted
    if d1 is None:
        d1 = _nth_cheapest_after_highlighted(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=1,
        )
        if d1:
            logger.debug(
                "Downsell 1 fell back to next-cheapest-after-highlighted for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, d1.pk, d1.name, d1.price
            )

    exclude.add(d1.pk) if d1 else None

    # -------- Downsell 2 --------
    d2: Optional[Level] = None

    # 1) (C-1, G+1, T)
    if cardholders > 1:
        cand = idx.get((cardholders - 1, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 selected via fallback #1 (C-1,G+1,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Downsell 2 fallback #1 (C-1,G+1,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 2) (C, G-1, T)
    if d2 is None and guests >= 1:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 selected via fallback #2 (C,G-1,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Downsell 2 fallback #2 (C,G-1,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 3) (C, G-2, T)
    if d2 is None and guests >= 2:
        cand = idx.get((cardholders, guests - 2, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 selected via fallback #3 (C,G-2,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Downsell 2 fallback #3 (C,G-2,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 4) next-next cheapest after highlighted
    if d2 is None:
        d2 = _nth_cheapest_after_highlighted(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=2,
        )
        if d2:
            logger.debug(
                "Downsell 2 fell back to next-next-cheapest-after-highlighted for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, d2.pk, d2.name, d2.price
            )

    exclude.add(d2.pk) if d2 else None

    # -------- Upsell 1 (reverse of Downsell 1) --------
    next_req = _next_step(tickets)
    u1: Optional[Level] = None

    # 1) (C, G, next(T))
    if next_req is not None:
        cand = idx.get((cardholders, guests, next_req))
        if cand and cand.pk not in exclude:
            u1 = cand
            logger.debug(
                "Upsell 1 selected via primary (C,G,nextT) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Upsell 1 primary (C,G,nextT) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 2) (C, G+1, T)
    if u1 is None:
        cand = idx.get((cardholders, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            u1 = cand
            logger.debug(
                "Upsell 1 selected via fallback #1 (C,G+1,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Upsell 1 fallback #1 (C,G+1,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 3) next most-expensive-after-highlighted (in price order this is the next item after highlighted)
    if u1 is None:
        u1 = _nth_most_expensive_after_highlighted(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=1,
        )
        if u1:
            logger.debug(
                "Upsell 1 fell back to next-more-expensive-after-highlighted for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, u1.pk, u1.name, u1.price
            )

    exclude.add(u1.pk) if u1 else None

    # -------- Upsell 2 (reverse of Downsell 2) --------
    u2: Optional[Level] = None

    # 1) (C+1, G-1, T)  [preserve total admissions]
    if guests >= 1:
        cand = idx.get((cardholders + 1, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            u2 = cand
            logger.debug(
                "Upsell 2 selected via fallback #1 (C+1,G-1,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Upsell 2 fallback #1 (C+1,G-1,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 2) (C, G+1, T)
    if u2 is None:
        cand = idx.get((cardholders, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            u2 = cand
            logger.debug(
                "Upsell 2 selected via fallback #2 (C,G+1,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Upsell 2 fallback #2 (C,G+1,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 3) (C, G+2, T)
    if u2 is None:
        cand = idx.get((cardholders, guests + 2, tickets))
        if cand and cand.pk not in exclude:
            u2 = cand
            logger.debug(
                "Upsell 2 selected via fallback #3 (C,G+2,T) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, cand.pk, cand.name, cand.price
            )
        else:
            logger.debug(
                "Upsell 2 fallback #3 (C,G+2,T) not found for input (C=%s,G=%s,T=%s)",
                cardholders, guests, tickets
            )

    # 4) next-next more-expensive-after-highlighted
    if u2 is None:
        u2 = _nth_most_expensive_after_highlighted(
            all_active_sorted=all_active_sorted,
            highlighted=highlighted,
            exclude=exclude,
            n=2,
        )
        if u2:
            logger.debug(
                "Upsell 2 fell back to next-next-more-expensive-after-highlighted for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders, guests, tickets, u2.pk, u2.name, u2.price
            )

    exclude.add(u2.pk) if u2 else None

    return RecommendationResult(
        match_type=match_type,
        highlighted=highlighted,
        downsell_1=d1,
        downsell_2=d2,
        upsell_1=u1,
        upsell_2=u2,
    )
