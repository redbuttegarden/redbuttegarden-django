from decimal import Decimal
from typing import List

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .decorators import basic_auth_required
from .forms import MembershipSelectorForm
from .models import MembershipWidgetConfig, MembershipLevel

SUGGESTION_SLOTS = 4  # how many non-highlighted cards to show


@basic_auth_required
@require_http_methods(["GET"])
def membership_selector_page(request):
    cfg = MembershipWidgetConfig.get_solo()
    form = MembershipSelectorForm(cfg=cfg)
    
    return render(
        request, "memberships/membership_selector.html", {"cfg": cfg, "form": form}
    )


@basic_auth_required
@require_http_methods(["POST"])
def membership_suggest(request):
    cfg = MembershipWidgetConfig.get_solo()
    form = MembershipSelectorForm(request.POST, cfg=cfg)

    if not form.is_valid():
        return render(
            request,
            "memberships/partials/_suggestions.html",
            {"form": form, "cfg": cfg, "highlighted": None, "suggestions": [], "requested": {}},
        )

    cardholders = form.cleaned_data["cardholders"]
    guests = form.cleaned_data["admissions"]
    tickets = form.cleaned_data["member_tickets"]

    pool_qs = MembershipLevel.objects.filter(
        active=True,
        cardholders_included=cardholders,
    ).order_by("price", "pk")
    pool = list(pool_qs)

    # --- Pick highlighted: Exact first, else Best ---
    highlighted = (
        pool_qs.filter(admissions_allowed=guests, member_sale_ticket_allowance=tickets)
        .order_by("price", "pk")
        .first()
    )
    match_type = "Exact" if highlighted else None

    if not highlighted:
        highlighted = (
            pool_qs.filter(admissions_allowed=guests, member_sale_ticket_allowance__gte=tickets)
            .order_by("member_sale_ticket_allowance", "price", "pk")
            .first()
        )
        match_type = "Best" if highlighted else None

    # If still nothing, your “no match” behavior can stay. (Spreadsheet doesn’t cover these.)
    if not highlighted:

        return render(
            request,
            "memberships/partials/_suggestions.html",
            {
                "cfg": cfg,
                "form": form,
                "highlighted": None,
                "suggestions": [],
                "requested": {"cardholders": cardholders, "admissions": guests, "tickets": tickets},
            },
        )

    # --- Build SUGGESTION_SLOTS additional suggestions from the same pool ---
    idx = next((i for i, m in enumerate(pool) if m.pk == highlighted.pk), None)

    picks: List[MembershipLevel] = []
    if idx is not None:
        # 1) up to 2 cheaper
        cheaper = pool[max(idx - 2, 0) : idx]
        picks.extend(cheaper)

        # 2) if fewer than 2 cheaper, fill from after highlighted
        needed = 2 - len(cheaper)
        after_cursor = idx + 1
        if needed > 0:
            picks.extend(pool[after_cursor : after_cursor + needed])
            after_cursor += needed

        # 3) fill remaining slots continuing forward
        remaining = SUGGESTION_SLOTS - len(picks)
        if remaining > 0:
            picks.extend(pool[after_cursor : after_cursor + remaining])
    else:
        # very unlikely, but don’t crash
        picks = [m for m in pool if m.pk != highlighted.pk][:SUGGESTION_SLOTS]

    # Ensure we never include highlighted in suggestions and never duplicate
    seen = {highlighted.pk}
    unique_picks = []
    for m in picks:
        if m.pk in seen:
            continue
        seen.add(m.pk)
        unique_picks.append(m)

    suggestions = [{"level": m, "badge": "Suggested"} for m in unique_picks]

    # -----------------------------
    # Auto-renewal pricing (Decimal)
    # -----------------------------
    renewal_discount: Decimal = cfg.auto_renewal_discount or Decimal("0.00")
    # Treat <= 0 as "disabled"
    if renewal_discount < 0:
        renewal_discount = Decimal("0.00")

    def attach_auto_renew_price(level: MembershipLevel) -> None:
        """
        Add computed fields onto the model instance for template use.
        Assumes level.price is a Decimal (or Decimal-like).
        """
        price = level.price or Decimal("0.00")
        auto = price - renewal_discount
        if auto < 0:
            auto = Decimal("0.00")

        # Attach attributes the template can read
        level.auto_renew_price = auto
        level.has_auto_renew_discount = renewal_discount > 0

    attach_auto_renew_price(highlighted)
    for item in suggestions:
        attach_auto_renew_price(item["level"])

    return render(
        request,
        "memberships/partials/_suggestions.html",
        {
            "cfg": cfg,
            "form": form,
            "highlighted": highlighted,
            "match_type": match_type,  # "Exact" or "Best"
            "suggestions": suggestions,  # list of dicts
            "requested": {"cardholders": cardholders, "admissions": guests, "tickets": tickets},
        },
    )
