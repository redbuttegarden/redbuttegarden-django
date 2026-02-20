from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence, Set, Tuple


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


def _closest_feasible(
    *,
    candidates: Iterable[Level],
    exclude: Set[int],
    highlighted: Level,
    requested_total: int,
    cardholders: int,
    guests: int,
    tickets: int,
    direction: str,  # "down" or "up"
) -> Optional[Level]:
    """
    Filler pick when ideal down/up slots don't exist.
    direction=down: requires price < highlighted
    direction=up:   requires price > highlighted
    """
    if direction == "down":
        pool = [
            l for l in candidates if l.pk not in exclude and l.price < highlighted.price
        ]
        ticket_rank_fn = lambda l: (
            0
            if l.member_sale_ticket_allowance < tickets
            else (1 if l.member_sale_ticket_allowance == tickets else 2)
        )
    else:
        pool = [
            l for l in candidates if l.pk not in exclude and l.price > highlighted.price
        ]
        ticket_rank_fn = lambda l: (
            0
            if l.member_sale_ticket_allowance > tickets
            else (1 if l.member_sale_ticket_allowance == tickets else 2)
        )

    if not pool:
        return None

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

    # -------- Highlighted --------
    exact = idx.get((cardholders, guests, tickets))
    if exact:
        highlighted = exact
        match_type = "Exact"
    else:
        # Best match: same cardholders+guests, ignore tickets.
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

    # NOTE: for downsell/upsell ranking, we still anchor to the highlighted tier for "closest feasible"
    base_tickets = highlighted.member_sale_ticket_allowance

    downs: List[Level] = []
    ups: List[Level] = []

    # -------- Downsell 1 (NEW RULE) --------
    # 1) same cardholders+guests, one step fewer *requested* tickets
    prev_req = _prev_step(tickets)
    d1: Optional[Level] = None

    if prev_req is not None:
        cand = idx.get((cardholders, guests, prev_req))
        if cand and cand.pk not in exclude and cand.price < highlighted.price:
            d1 = cand

    # 2) fallback: same cardholders+requested tickets, one fewer guest
    if d1 is None and guests > 0:
        cand = idx.get((cardholders, guests - 1, tickets))
        if cand and cand.pk not in exclude and cand.price < highlighted.price:
            d1 = cand

    if d1:
        downs.append(d1)
        exclude.add(d1.pk)

    # -------- Downsell 2 (keep simple: step down from highlighted tier, then fill) --------
    # Try ticket-step downsell(s) around the highlighted tier (same cardholders+guests)
    t = _prev_step(base_tickets)
    while t is not None and len(downs) < 2:
        cand = idx.get((cardholders, guests, t))
        if cand and cand.pk not in exclude and cand.price < highlighted.price:
            downs.append(cand)
            exclude.add(cand.pk)
        t = _prev_step(t)

    # -------- Upsells: step from highlighted tier --------
    t = _next_step(base_tickets)
    while t is not None and len(ups) < 2:
        cand = idx.get((cardholders, guests, t))
        if cand and cand.pk not in exclude and cand.price > highlighted.price:
            ups.append(cand)
            exclude.add(cand.pk)
        t = _next_step(t)

    # -------- Fill missing downsells/upsells with closest feasible --------
    while len(downs) < 2:
        cand = _closest_feasible(
            candidates=active,
            exclude=exclude,
            highlighted=highlighted,
            requested_total=requested_total,
            cardholders=cardholders,
            guests=guests,
            tickets=base_tickets,  # anchor to highlighted tier
            direction="down",
        )
        if not cand:
            break
        downs.append(cand)
        exclude.add(cand.pk)

    while len(ups) < 2:
        cand = _closest_feasible(
            candidates=active,
            exclude=exclude,
            highlighted=highlighted,
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

    return RecommendationResult(
        match_type=match_type,
        highlighted=highlighted,
        downsell_1=downs[0] if len(downs) > 0 else None,
        downsell_2=downs[1] if len(downs) > 1 else None,
        upsell_1=ups[0] if len(ups) > 0 else None,
        upsell_2=ups[1] if len(ups) > 1 else None,
    )
