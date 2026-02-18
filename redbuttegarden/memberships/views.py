from decimal import Decimal
from typing import Dict, List, Optional

from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .decorators import basic_auth_required
from .forms import MembershipSelectorForm
from .models import MembershipLevel
from .services.recommendations import Level, recommend_levels
from .widget_config import MembershipWidgetConfig

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

    # Pull all active levels once (we'll convert to dataclasses for the recommender,
    # then map back to ORM instances for rendering).
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

    # Convert ORM objects -> Level dataclasses (the recommender works on these)
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
        suggestion_slots=SUGGESTION_SLOTS,
    )

    # Map dataclass PKs back -> ORM instances (preserves labels/purchase_url/etc.)
    by_pk: Dict[int, MembershipLevel] = {m.pk: m for m in db_levels}

    highlighted: Optional[MembershipLevel] = (
        by_pk.get(rec.highlighted.pk) if rec.highlighted else None
    )

    suggestion_models: List[MembershipLevel] = [
        by_pk[s.pk] for s in rec.suggestions if s.pk in by_pk
    ]

    # Build template-friendly shape: [{"level": ..., "badge": ...}, ...]
    # (you can change "Suggested" to whatever you prefer)
    suggestions = [{"level": m, "badge": "Suggested"} for m in suggestion_models]

    # If no highlighted, keep your current behavior (template will show “No active membership…”)
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
            "match_type": rec.match_type,  # "Exact" / "Best" / None
            "suggestions": suggestions,  # list of dicts for your include
            "requested": {
                "cardholders": cardholders,
                "admissions": guests,
                "tickets": tickets,
            },
        },
    )
