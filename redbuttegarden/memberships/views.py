from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional

from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .decorators import basic_auth_required
from .forms import MembershipSelectorForm
from .models import MembershipLevel
from .widget_config import MembershipWidgetConfig
from .services.recommendations import Level, recommend_levels


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
            {
                "form": form,
                "cfg": cfg,
                "highlighted": None,
                "suggestions": [],
                "requested": {},
            },
        )

    cardholders = form.cleaned_data["cardholders"]
    guests = form.cleaned_data["admissions"]
    tickets = form.cleaned_data["member_tickets"]

    # Fetch all active levels because downsell/upsell rules can cross cardholder counts
    qs = (
        MembershipLevel.objects.filter(active=True)
        .select_related("labels")
        .only(
            "pk",
            "name",
            "cardholders_included",
            "admissions_allowed",
            "member_sale_ticket_allowance",
            "price",
            "charitable_gift_amount",
            "purchase_url",
            "active",
            "labels__cardholder_label",
            "labels__admissions_label",
            "labels__member_tickets_label",
            "description",
            "tooltip",
        )
    )
    db_levels: List[MembershipLevel] = list(qs)
    by_pk: Dict[int, MembershipLevel] = {m.pk: m for m in db_levels}

    level_inputs: List[Level] = [
        Level(
            pk=m.pk,
            name=m.name,
            cardholders_included=m.cardholders_included,
            admissions_allowed=m.admissions_allowed,
            member_sale_ticket_allowance=m.member_sale_ticket_allowance,
            price=m.price,
            active=m.active,
        )
        for m in db_levels
    ]

    rec = recommend_levels(
        levels=level_inputs,
        cardholders=cardholders,
        guests=guests,
        tickets=tickets,
    )

    highlighted: Optional[MembershipLevel] = (
        by_pk.get(rec.highlighted.pk) if rec.highlighted else None
    )
    if not highlighted:
        return render(
            request,
            "memberships/partials/_suggestions.html",
            {
                "cfg": cfg,
                "form": form,
                "highlighted": None,
                "suggestions": [],
                "match_type": None,
                "requested": {
                    "cardholders": cardholders,
                    "admissions": guests,
                    "tickets": tickets,
                },
            },
        )

    # Build ordered suggestions with stable badges (no index-shifting!)
    slots = [
        ("Downsell", rec.downsell_1),
        ("Downsell", rec.downsell_2),
        ("Upsell", rec.upsell_1),
        ("Upsell", rec.upsell_2),
    ]
    suggestions = []
    for badge, lvl in slots:
        if not lvl:
            continue
        m = by_pk.get(lvl.pk)
        if not m:
            continue
        suggestions.append({"level": m, "badge": badge})

    # -----------------------------
    # Auto-renewal pricing (Decimal)
    # -----------------------------
    renewal_discount: Decimal = cfg.auto_renewal_discount or Decimal("0.00")
    if renewal_discount < 0:
        renewal_discount = Decimal("0.00")

    def attach_auto_renew_price(level: MembershipLevel) -> None:
        price = level.price or Decimal("0.00")
        auto = price - renewal_discount
        if auto < 0:
            auto = Decimal("0.00")
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
            "match_type": rec.match_type,
            "suggestions": suggestions,
            "requested": {
                "cardholders": cardholders,
                "admissions": guests,
                "tickets": tickets,
            },
        },
    )
