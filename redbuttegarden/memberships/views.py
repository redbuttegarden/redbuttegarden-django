from django.db.models import Min, Max
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .decorators import basic_auth_required
from .forms import MembershipSelectorForm
from .models import MembershipWidgetConfig, MembershipLevel


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
    form = MembershipSelectorForm(request.POST)

    if not form.is_valid():
        return render(
            request,
            "memberships/partials/_suggestions.html",
            {"form": form, "results": []},
        )

    cardholders = form.cleaned_data["cardholders"]
    admissions = form.cleaned_data["admissions"]
    tickets = form.cleaned_data["member_tickets"]

    # --- Exact matches (no scoring / weights) ---
    exact_qs = MembershipLevel.objects.filter(
        active=True,
        cardholders_included=cardholders,
        admissions_allowed=admissions,
        member_sale_ticket_allowance=tickets,
    ).order_by(
        "price", "pk"
    )  # deterministic order

    exact_list = list(exact_qs)  # all exact matches ordered by price

    # If we have exact matches, pick the cheapest as highlighted, keep the others in results
    highlighted = None
    results = []
    upsell = None
    downsell = None

    if exact_list:
        highlighted = exact_list[0]
        # other exact matches (if any) to show under "Best matches"
        results = exact_list[1:]  # could be empty; that's fine

        # Build an ordered pool for upsell/downsell decisions:
        # consider all active memberships that allow AT LEAST the requested ticket count
        candidate_qs = MembershipLevel.objects.filter(
            active=True, member_sale_ticket_allowance__gte=tickets
        ).order_by("price", "pk")
        candidates = list(candidate_qs)

        # locate highlighted in the candidate list (match by PK)
        idx = None
        for i, c in enumerate(candidates):
            if c.pk == highlighted.pk:
                idx = i
                break

        # If highlighted isn't in candidates (unlikely since exact match has member_sale_ticket_allowance==tickets),
        # we still pick upsell/downsell by finding nearby price points relative to highlighted.price.
        if idx is not None:
            if idx > 0:
                downsell = candidates[idx - 1]
            if idx < len(candidates) - 1:
                upsell = candidates[idx + 1]
        else:
            # fallback: find nearest cheaper and more expensive by price
            hp = highlighted.price
            cheaper = [c for c in candidates if c.price < hp]
            moreexp = [c for c in candidates if c.price > hp]
            downsell = cheaper[-1] if cheaper else None
            upsell = moreexp[0] if moreexp else None

        return render(
            request,
            "memberships/partials/_suggestions.html",
            {
                "form": form,
                "results": results,
                "highlighted": highlighted,
                "upsell": upsell,
                "downsell": downsell,
                "requested": {
                    "cardholders": cardholders,
                    "admissions": admissions,
                    "tickets": tickets,
                },
            },
        )

    # --- No exact matches: produce guidance (we never recommend reducing tickets) ---
    active_levels = MembershipLevel.objects.filter(active=True)
    agg = active_levels.aggregate(max_tickets=Max("member_sale_ticket_allowance"))
    max_tickets = agg["max_tickets"] or 0

    if tickets > max_tickets:
        form.add_error(
            None,
            (
                f"No active membership offers {tickets} member-sale tickets; the maximum available is {max_tickets}. "
                "Because you requested that many tickets, there are no matching memberships. "
                "If you believe you need more tickets than our published memberships allow, please contact support."
            ),
        )
        return render(
            request,
            "memberships/partials/_suggestions.html",
            {
                "form": form,
                "results": [],
                "highlighted": None,
                "upsell": None,
                "downsell": None,
                "requested": {
                    "cardholders": cardholders,
                    "admissions": admissions,
                    "tickets": tickets,
                },
            },
        )

    candidate_qs = active_levels.filter(member_sale_ticket_allowance__gte=tickets)
    candidate_agg = candidate_qs.aggregate(
        min_admissions=Min("admissions_allowed"),
        min_cardholders=Min("cardholders_included"),
    )
    min_admissions = candidate_agg["min_admissions"] or 0
    min_cardholders = candidate_agg["min_cardholders"] or 0

    suggestions = []
    if admissions < min_admissions:
        suggestions.append(
            (
                f"To purchase {tickets} concert tickets, you must select a membership that allows at least "
                f"{min_admissions} admissions per visit. "
                f"You selected {admissions} admissions per visit. "
                f"Increase the Admissions value to {min_admissions} or more to see matching memberships."
            )
        )

    if cardholders < min_cardholders:
        suggestions.append(
            (
                f"Some memberships that allow {tickets} tickets require at least {min_cardholders} named cardholder(s). "
                f"You selected {cardholders}. Consider increasing the number of named cardholders to {min_cardholders}."
            )
        )

    if not suggestions:
        example = candidate_qs.order_by("price").first()
        if example:
            suggestions.append(
                (
                    f"There are memberships that allow {tickets} tickets. For example, the '{example.name}' level "
                    f"allows {example.admissions_allowed} admissions and {example.cardholders_included} named cardholder(s). "
                    "Adjust your selections to match one of the available membership combinations (increase admissions or named cardholders)."
                )
            )
        else:
            suggestions.append(
                "No exact membership matched your selections. Try increasing admissions (guests + cardholders) or the number of named cardholders."
            )

    form.add_error(None, " ".join(suggestions))

    return render(
        request,
        "memberships/partials/_suggestions.html",
        {
            "form": form,
            "results": [],
            "highlighted": None,
            "upsell": None,
            "downsell": None,
            "requested": {
                "cardholders": cardholders,
                "admissions": admissions,
                "tickets": tickets,
            },
        },
    )
