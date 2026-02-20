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


def _level_total_adm(l: Level) -> int:
    return l.cardholders_included + l.admissions_allowed


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


def _nth_cheapest_after_highlighted(
    *,
    all_active_sorted: Sequence[Level],
    highlighted: Level,
    exclude: Set[int],
    n: int,
) -> Optional[Level]:
    """
    Return the nth cheapest membership AFTER highlighted in the global price ordering,
    skipping excluded items. n=1 means "next cheapest after highlighted", n=2 means "next-next", etc.
    If there aren't enough items after highlighted, we fall back to the cheapest non-excluded overall.
    """
    if n <= 0:
        raise ValueError("n must be >= 1")

    # All non-excluded, in global price order
    non_excluded = [l for l in all_active_sorted if l.pk not in exclude]
    if not non_excluded:
        return None

    try:
        idx_h = next(
            i for i, l in enumerate(all_active_sorted) if l.pk == highlighted.pk
        )
    except StopIteration:
        # highlighted not found (shouldn't happen) -> nth from start
        return non_excluded[n - 1] if len(non_excluded) >= n else non_excluded[0]

    found = 0
    for j in range(idx_h + 1, len(all_active_sorted)):
        cand = all_active_sorted[j]
        if cand.pk in exclude:
            continue
        found += 1
        if found == n:
            return cand

    # Not enough after highlighted -> pick nth overall if possible, else cheapest
    return non_excluded[n - 1] if len(non_excluded) >= n else non_excluded[0]


def _closest_feasible(
    *,
    candidates: Iterable[Level],
    exclude: Set[int],
    requested_total: int,
    cardholders: int,
    guests: int,
    tickets: int,
    direction: str,  # "down" or "up"
) -> Optional[Level]:
    """
    Filler pick when ideal down/up slots don't exist.
    NOTE: no longer enforces cheaper/more-expensive. 'direction' only biases ticket rank.
    """
    pool = [l for l in candidates if l.pk not in exclude]
    if not pool:
        return None

    if direction == "down":
        ticket_rank_fn = lambda l: (
            0
            if l.member_sale_ticket_allowance < tickets
            else (1 if l.member_sale_ticket_allowance == tickets else 2)
        )
    else:
        ticket_rank_fn = lambda l: (
            0
            if l.member_sale_ticket_allowance > tickets
            else (1 if l.member_sale_ticket_allowance == tickets else 2)
        )

    def key(l: Level) -> Tuple[int, int, int, int, Decimal, int]:
        total_diff = abs(_level_total_adm(l) - requested_total)
        same_card = 0 if l.cardholders_included == cardholders else 1
        same_guest = 0 if l.admissions_allowed == guests else 1
        ticket_rank = ticket_rank_fn(l)
        return (total_diff, same_card, same_guest, ticket_rank, l.price, l.pk)

    return min(pool, key=key)


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

    requested_total = _total_adm(cardholders, guests)
    exclude: Set[int] = {highlighted.pk}

    # Anchor used for generic ranking
    base_tickets = highlighted.member_sale_ticket_allowance

    downs: List[Level] = []
    ups: List[Level] = []

    # -------- Downsell 1 --------
    prev_req = _prev_step(tickets)
    d1: Optional[Level] = None

    # 1) same cardholders+guests, one step fewer *requested* tickets
    if prev_req is not None:
        cand = idx.get((cardholders, guests, prev_req))
        if cand and cand.pk not in exclude:
            d1 = cand
            logger.debug(
                "Downsell 1 selected via primary (same C,G; T-1step) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders,
                guests,
                tickets,
                cand.pk,
                cand.name,
                cand.price,
            )
        else:
            logger.debug(
                "Downsell 1 primary (same C,G; T-1step) not found for input (C=%s,G=%s,T=%s)",
                cardholders,
                guests,
                tickets,
            )

    # 2) fallback: same cardholders+requested tickets, one fewer guest
    if d1 is None and guests > 0:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            d1 = cand
            logger.debug(
                "Downsell 1 selected via fallback #1 (same C,T; G-1) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders,
                guests,
                tickets,
                cand.pk,
                cand.name,
                cand.price,
            )
        else:
            logger.debug(
                "Downsell 1 fallback #1 (same C,T; G-1) not found for input (C=%s,G=%s,T=%s)",
                cardholders,
                guests,
                tickets,
            )

    # 3) final fallback: next cheapest after highlighted (global price order)
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
                cardholders,
                guests,
                tickets,
                d1.pk,
                d1.name,
                d1.price,
            )

    if d1:
        downs.append(d1)
        exclude.add(d1.pk)

    # -------- Downsell 2 --------
    d2: Optional[Level] = None

    # 1) (cardholders-1, guests+1, tickets)
    if cardholders > 1:
        cand = idx.get((cardholders - 1, guests + 1, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 selected via fallback #1 (C-1,G+1) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders,
                guests,
                tickets,
                cand.pk,
                cand.name,
                cand.price,
            )
        else:
            logger.debug(
                "Downsell 2 fallback #1 (C-1,G+1) not found for input (C=%s,G=%s,T=%s)",
                cardholders,
                guests,
                tickets,
            )

    # 2) (cardholders, guests-1, tickets)
    if d2 is None and guests >= 1:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 selected via fallback #2 (C,G-1) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders,
                guests,
                tickets,
                cand.pk,
                cand.name,
                cand.price,
            )
        else:
            logger.debug(
                "Downsell 2 fallback #2 (C,G-1) not found for input (C=%s,G=%s,T=%s)",
                cardholders,
                guests,
                tickets,
            )

    # 3) (cardholders, guests-2, tickets)
    if d2 is None and guests >= 2:
        cand = idx.get((cardholders, guests - 2, tickets))
        if cand and cand.pk not in exclude:
            d2 = cand
            logger.debug(
                "Downsell 2 selected via fallback #3 (C,G-2) for input (C=%s,G=%s,T=%s): picked pk=%s name=%r price=%s",
                cardholders,
                guests,
                tickets,
                cand.pk,
                cand.name,
                cand.price,
            )
        else:
            logger.debug(
                "Downsell 2 fallback #3 (C,G-2) not found for input (C=%s,G=%s,T=%s)",
                cardholders,
                guests,
                tickets,
            )

    # Final fallback: next-next cheapest after highlighted (global price ordering)
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
                cardholders,
                guests,
                tickets,
                d2.pk,
                d2.name,
                d2.price,
            )

    if d2:
        downs.append(d2)
        exclude.add(d2.pk)

    # -------- Upsells: prefer higher ticket steps (non-strict) --------
    t = _next_step(base_tickets)
    while t is not None and len(ups) < 2:
        cand = idx.get((cardholders, guests, t))
        if cand and cand.pk not in exclude:
            ups.append(cand)
            exclude.add(cand.pk)
        t = _next_step(t)

    # -------- Fill missing upsells with closest feasible (non-strict) --------
    while len(ups) < 2:
        cand = _closest_feasible(
            candidates=active,
            exclude=exclude,
            requested_total=requested_total,
            cardholders=cardholders,
            guests=guests,
            tickets=base_tickets,
            direction="up",
        )
        if not cand:
            break
        ups.append(cand)
        exclude.add(cand.pk)

    # -------- Fill missing downsells with closest feasible (non-strict) --------
    while len(downs) < 2:
        cand = _closest_feasible(
            candidates=active,
            exclude=exclude,
            requested_total=requested_total,
            cardholders=cardholders,
            guests=guests,
            tickets=base_tickets,
            direction="down",
        )
        if not cand:
            break
        downs.append(cand)
        exclude.add(cand.pk)

    return RecommendationResult(
        match_type=match_type,
        highlighted=highlighted,
        downsell_1=downs[0] if len(downs) > 0 else None,
        downsell_2=downs[1] if len(downs) > 1 else None,
        upsell_1=ups[0] if len(ups) > 0 else None,
        upsell_2=ups[1] if len(ups) > 1 else None,
    )
