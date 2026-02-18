# memberships/services/recommendations.py
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, List, Optional, Sequence, Set, Tuple


# Allowed ticket steps (keep in sync with form constraints)
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

    # Named slots prevent badge/slot drift when some picks are missing
    downsell_1: Optional[Level]
    downsell_2: Optional[Level]
    upsell_1: Optional[Level]
    upsell_2: Optional[Level]


def _total_admissions(cardholders: int, guests: int) -> int:
    return cardholders + guests


def _level_total_admissions(l: Level) -> int:
    return l.cardholders_included + l.admissions_allowed


def _sorted_by_price(levels: Iterable[Level]) -> List[Level]:
    return sorted(levels, key=lambda l: (l.price, l.pk))


def _next_ticket_step(tickets: int) -> Optional[int]:
    for v in TICKET_STEPS:
        if v > tickets:
            return v
    return None


def _prev_ticket_step(tickets: int) -> Optional[int]:
    prev = None
    for v in TICKET_STEPS:
        if v < tickets:
            prev = v
        else:
            break
    return prev


def _pick_cheapest_under(
    levels: Iterable[Level],
    *,
    exclude: Set[int],
    under_price: Decimal,
    prefer_same_total: Optional[int] = None,
    prefer_exact_cardholders: Optional[int] = None,
    prefer_exact_guests: Optional[int] = None,
) -> Optional[Level]:
    """
    Cheapest candidate with price < under_price.
    Ranks candidates by preference flags first, then by price.
    """
    candidates = [l for l in levels if l.pk not in exclude and l.price < under_price]
    if not candidates:
        return None

    def key(l: Level) -> Tuple[int, int, int, Decimal, int]:
        same_total_rank = 0
        if prefer_same_total is not None:
            same_total_rank = (
                0 if _level_total_admissions(l) == prefer_same_total else 1
            )

        same_card_rank = 0
        if prefer_exact_cardholders is not None:
            same_card_rank = (
                0 if l.cardholders_included == prefer_exact_cardholders else 1
            )

        same_guest_rank = 0
        if prefer_exact_guests is not None:
            same_guest_rank = 0 if l.admissions_allowed == prefer_exact_guests else 1

        return (same_total_rank, same_card_rank, same_guest_rank, l.price, l.pk)

    return min(candidates, key=key)


def _pick_cheapest_over(
    levels: Iterable[Level],
    *,
    exclude: Set[int],
    over_price: Decimal,
    prefer_same_total: Optional[int] = None,
    prefer_exact_cardholders: Optional[int] = None,
    prefer_exact_guests: Optional[int] = None,
) -> Optional[Level]:
    """
    Cheapest candidate with price > over_price.
    """
    candidates = [l for l in levels if l.pk not in exclude and l.price > over_price]
    if not candidates:
        return None

    def key(l: Level) -> Tuple[int, int, int, Decimal, int]:
        same_total_rank = 0
        if prefer_same_total is not None:
            same_total_rank = (
                0 if _level_total_admissions(l) == prefer_same_total else 1
            )

        same_card_rank = 0
        if prefer_exact_cardholders is not None:
            same_card_rank = (
                0 if l.cardholders_included == prefer_exact_cardholders else 1
            )

        same_guest_rank = 0
        if prefer_exact_guests is not None:
            same_guest_rank = 0 if l.admissions_allowed == prefer_exact_guests else 1

        return (same_total_rank, same_card_rank, same_guest_rank, l.price, l.pk)

    return min(candidates, key=key)


def _pick_second_best_over(
    levels: Iterable[Level],
    *,
    exclude: Set[int],
    over_price: Decimal,
    prefer_same_total: Optional[int] = None,
    prefer_exact_cardholders: Optional[int] = None,
    prefer_exact_guests: Optional[int] = None,
) -> Optional[Level]:
    """
    Second-best candidate with price > over_price using the same ranking as _pick_cheapest_over.
    """
    candidates = [l for l in levels if l.pk not in exclude and l.price > over_price]
    if len(candidates) < 2:
        return None

    def key(l: Level) -> Tuple[int, int, int, Decimal, int]:
        same_total_rank = 0
        if prefer_same_total is not None:
            same_total_rank = (
                0 if _level_total_admissions(l) == prefer_same_total else 1
            )

        same_card_rank = 0
        if prefer_exact_cardholders is not None:
            same_card_rank = (
                0 if l.cardholders_included == prefer_exact_cardholders else 1
            )

        same_guest_rank = 0
        if prefer_exact_guests is not None:
            same_guest_rank = 0 if l.admissions_allowed == prefer_exact_guests else 1

        return (same_total_rank, same_card_rank, same_guest_rank, l.price, l.pk)

    candidates.sort(key=key)
    return candidates[1]


def _fill_downsells_with_closest_feasible(
    *,
    active: Sequence[Level],
    exclude: Set[int],
    highlighted: Level,
    requested_total: int,
    cardholders: int,
    guests: int,
    tickets: int,
    need: int,
) -> List[Level]:
    """
    Fill missing downsell slots using cheaper candidates closest to requested total admissions.
    Prefer same cardholders/guests and lower ticket allowance when possible.
    """
    if need <= 0:
        return []

    candidates = [
        l for l in active if l.pk not in exclude and l.price < highlighted.price
    ]
    if not candidates:
        return []

    def key(l: Level) -> Tuple[int, int, int, int, Decimal, int]:
        total_diff = abs(_level_total_admissions(l) - requested_total)
        same_card = 0 if l.cardholders_included == cardholders else 1
        same_guest = 0 if l.admissions_allowed == guests else 1

        # Prefer lower ticket allowance; strongest preference is "< requested tickets"
        if l.member_sale_ticket_allowance < tickets:
            ticket_rank = 0
        elif l.member_sale_ticket_allowance == tickets:
            ticket_rank = 1
        else:
            ticket_rank = 2

        return (total_diff, same_card, same_guest, ticket_rank, l.price, l.pk)

    candidates.sort(key=key)

    picked: List[Level] = []
    for l in candidates:
        if l.pk in exclude:
            continue
        picked.append(l)
        exclude.add(l.pk)
        if len(picked) >= need:
            break
    return picked


def _fill_upsells_with_closest_feasible(
    *,
    active: Sequence[Level],
    exclude: Set[int],
    highlighted: Level,
    requested_total: int,
    cardholders: int,
    guests: int,
    tickets: int,
    need: int,
) -> List[Level]:
    """
    Fill missing upsell slots using more-expensive candidates closest to requested total admissions.
    Prefer same cardholders/guests and higher ticket allowance when possible.
    """
    if need <= 0:
        return []

    candidates = [
        l for l in active if l.pk not in exclude and l.price > highlighted.price
    ]
    if not candidates:
        return []

    def key(l: Level) -> Tuple[int, int, int, int, Decimal, int]:
        total_diff = abs(_level_total_admissions(l) - requested_total)
        same_card = 0 if l.cardholders_included == cardholders else 1
        same_guest = 0 if l.admissions_allowed == guests else 1

        # Prefer higher ticket allowance; strongest preference is "> requested tickets"
        if l.member_sale_ticket_allowance > tickets:
            ticket_rank = 0
        elif l.member_sale_ticket_allowance == tickets:
            ticket_rank = 1
        else:
            ticket_rank = 2

        return (total_diff, same_card, same_guest, ticket_rank, l.price, l.pk)

    candidates.sort(key=key)

    picked: List[Level] = []
    for l in candidates:
        if l.pk in exclude:
            continue
        picked.append(l)
        exclude.add(l.pk)
        if len(picked) >= need:
            break
    return picked


def recommend_levels(
    *,
    levels: Sequence[Level],
    cardholders: int,
    guests: int,
    tickets: int,
) -> RecommendationResult:
    """
    Returns:
      - highlighted (Exact if possible else Best)
      - downsell_1/2 and upsell_1/2 (filled with fallbacks if ideal picks don't exist)
    """
    active = [l for l in levels if l.active]
    req_total = _total_admissions(cardholders, guests)

    next_tickets = _next_ticket_step(tickets)
    prev_tickets = _prev_ticket_step(tickets)

    # ---------- Highlighted ----------
    exact = _sorted_by_price(
        l
        for l in active
        if l.cardholders_included == cardholders
        and l.admissions_allowed == guests
        and l.member_sale_ticket_allowance == tickets
    )
    if exact:
        highlighted = exact[0]
        match_type = "Exact"
    else:
        eligible = [l for l in active if l.member_sale_ticket_allowance >= tickets]
        eligible.sort(
            key=lambda l: (
                0 if _level_total_admissions(l) == req_total else 1,
                l.member_sale_ticket_allowance,
                l.price,
                l.pk,
            )
        )
        highlighted = eligible[0] if eligible else None
        match_type = "Best" if highlighted else None

    if not highlighted:
        return RecommendationResult(None, None, None, None, None, None)

    exclude: Set[int] = {highlighted.pk}

    # Common pools by requested tickets
    same_tickets = [l for l in active if l.member_sale_ticket_allowance == tickets]
    exact_same_tickets = [
        l
        for l in same_tickets
        if l.cardholders_included == cardholders and l.admissions_allowed == guests
    ]
    same_total_same_tickets = [
        l for l in same_tickets if _level_total_admissions(l) == req_total
    ]
    same_tickets_sorted = _sorted_by_price(same_tickets)

    # Decrement ticket pool: exact cardholders+guests at previous ticket step
    dec_exact_pool: List[Level] = []
    if prev_tickets is not None:
        dec_exact_pool = _sorted_by_price(
            l
            for l in active
            if l.cardholders_included == cardholders
            and l.admissions_allowed == guests
            and l.member_sale_ticket_allowance == prev_tickets
        )

    # Next ticket pool (requested cardholders at next ticket step), prefer same guests
    next_step_pool: List[Level] = []
    if next_tickets is not None:
        next_step_pool = [
            l
            for l in active
            if l.cardholders_included == cardholders
            and l.member_sale_ticket_allowance == next_tickets
        ]
        next_step_pool.sort(
            key=lambda l: (0 if l.admissions_allowed == guests else 1, l.price, l.pk)
        )

    def nth_nearest_cheaper_same_ticket(n: int) -> Optional[Level]:
        cheaper = [
            l
            for l in same_tickets_sorted
            if l.pk not in exclude and l.price < highlighted.price
        ]
        cheaper.sort(key=lambda l: (l.price, l.pk))
        # nearest cheaper is last element, second nearest is second last, etc.
        return cheaper[-n] if len(cheaper) >= n else None

    # ---------- Downsells (attempt ideal picks first) ----------
    downsells: List[Level] = []

    # Downsell 1 priorities
    d1 = _pick_cheapest_under(
        exact_same_tickets,
        exclude=exclude,
        under_price=highlighted.price,
        prefer_same_total=req_total,
        prefer_exact_cardholders=cardholders,
        prefer_exact_guests=guests,
    )
    if not d1:
        d1 = _pick_cheapest_under(
            same_total_same_tickets,
            exclude=exclude,
            under_price=highlighted.price,
            prefer_same_total=req_total,
        )
    if not d1 and dec_exact_pool:
        d1 = _pick_cheapest_under(
            dec_exact_pool,
            exclude=exclude,
            under_price=highlighted.price,
            prefer_same_total=req_total,
            prefer_exact_cardholders=cardholders,
            prefer_exact_guests=guests,
        )

    if d1:
        downsells.append(d1)
        exclude.add(d1.pk)

    # Downsell 2 priorities
    d2 = _pick_cheapest_under(
        same_total_same_tickets,
        exclude=exclude,
        under_price=highlighted.price,
        prefer_same_total=req_total,
    )
    if not d2:
        d2 = nth_nearest_cheaper_same_ticket(1)
    if not d2:
        d2 = nth_nearest_cheaper_same_ticket(2)
    if not d2 and dec_exact_pool:
        d2 = _pick_cheapest_under(
            dec_exact_pool,
            exclude=exclude,
            under_price=highlighted.price,
            prefer_same_total=req_total,
            prefer_exact_cardholders=cardholders,
            prefer_exact_guests=guests,
        )

    if d2:
        downsells.append(d2)
        exclude.add(d2.pk)

    # Fill missing downsells with closest feasible cheaper options
    missing_down = 2 - len(downsells)
    if missing_down > 0:
        downsells.extend(
            _fill_downsells_with_closest_feasible(
                active=active,
                exclude=exclude,
                highlighted=highlighted,
                requested_total=req_total,
                cardholders=cardholders,
                guests=guests,
                tickets=tickets,
                need=missing_down,
            )
        )

    downsell_1 = downsells[0] if len(downsells) > 0 else None
    downsell_2 = downsells[1] if len(downsells) > 1 else None

    # ---------- Upsells (attempt ideal picks first) ----------
    upsells: List[Level] = []

    # Upsell 1 priorities
    u1 = _pick_cheapest_over(
        exact_same_tickets,
        exclude=exclude,
        over_price=highlighted.price,
        prefer_same_total=req_total,
        prefer_exact_cardholders=cardholders,
        prefer_exact_guests=guests,
    )
    if not u1 and next_step_pool:
        u1 = next((l for l in next_step_pool if l.pk not in exclude), None)
    if not u1:
        u1 = _pick_cheapest_over(
            same_tickets,
            exclude=exclude,
            over_price=highlighted.price,
            prefer_same_total=req_total,
        )

    if u1:
        upsells.append(u1)
        exclude.add(u1.pk)

    # Upsell 2 priorities
    u2 = None
    if next_step_pool:
        u2 = next((l for l in next_step_pool if l.pk not in exclude), None)

    if not u2:
        u2 = _pick_second_best_over(
            same_tickets,
            exclude=exclude,
            over_price=highlighted.price,
            prefer_same_total=req_total,
        )

    if not u2 and next_step_pool:
        remaining = [l for l in next_step_pool if l.pk not in exclude]
        u2 = remaining[1] if len(remaining) >= 2 else None

    if u2:
        upsells.append(u2)
        exclude.add(u2.pk)

    # Fill missing upsells with closest feasible more-expensive options
    missing_up = 2 - len(upsells)
    if missing_up > 0:
        upsells.extend(
            _fill_upsells_with_closest_feasible(
                active=active,
                exclude=exclude,
                highlighted=highlighted,
                requested_total=req_total,
                cardholders=cardholders,
                guests=guests,
                tickets=tickets,
                need=missing_up,
            )
        )

    upsell_1 = upsells[0] if len(upsells) > 0 else None
    upsell_2 = upsells[1] if len(upsells) > 1 else None

    return RecommendationResult(
        match_type=match_type,
        highlighted=highlighted,
        downsell_1=downsell_1,
        downsell_2=downsell_2,
        upsell_1=upsell_1,
        upsell_2=upsell_2,
    )
