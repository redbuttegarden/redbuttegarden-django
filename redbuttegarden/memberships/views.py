from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from .forms import MembershipSelectorForm
from .models import MembershipLevel


def _score_level(level, cardholders, admissions, tickets, w_card, w_adm, w_tix):
    """
    Returns a score; lower is better. Applies user-provided weights to shortfall
    penalties and over-capacity penalties.
    """

    score = 0.0

    # Shortfalls — heavy penalties
    if level.cardholders_included < cardholders:
        score += (cardholders - level.cardholders_included) * 1000 * max(1, w_card)
    if level.admissions_allowed < admissions:
        score += (admissions - level.admissions_allowed) * 1000 * max(1, w_adm)
    if level.member_sale_ticket_allowance < tickets:
        score += (tickets - level.member_sale_ticket_allowance) * 1000 * max(1, w_tix)

    # Over-capacity — mild penalties
    if level.cardholders_included > cardholders:
        score += (level.cardholders_included - cardholders) * 10 * max(1, w_card)
    if level.admissions_allowed > admissions:
        score += (level.admissions_allowed - admissions) * 8 * max(1, w_adm)
    if level.member_sale_ticket_allowance > tickets:
        score += (level.member_sale_ticket_allowance - tickets) * 5 * max(1, w_tix)

    # Price tiebreaker (small)
    score += float(level.price) / 100.0

    return score


@require_http_methods(["GET"])
def membership_selector_page(request):
    form = MembershipSelectorForm()
    return render(request, "memberships/membership_selector.html", {"form": form})


@require_http_methods(["POST"])
def membership_suggest(request):
    form = MembershipSelectorForm(request.POST)

    if not form.is_valid():
        return render(
            request, "memberships/partials/_suggestions.html", {"form": form, "results": []}
        )

    cardholders = form.cleaned_data["cardholders"]
    admissions = form.cleaned_data["admissions"]
    tickets = form.cleaned_data["member_tickets"]

    w_adm = form.cleaned_data["admissions_weight"]
    w_card = form.cleaned_data["cardholders_weight"]
    w_tix = form.cleaned_data["tickets_weight"]

    qs = MembershipLevel.objects.filter(active=True)

    scored = [
        (lvl, _score_level(lvl, cardholders, admissions, tickets, w_card, w_adm, w_tix))
        for lvl in qs
    ]
    scored.sort(key=lambda s: s[1])

    results = [lvl for lvl, _ in scored[:5]]

    return render(
        request,
        "memberships/partials/_suggestions.html",
        {
            "form": form,
            "results": results,
            "requested": {
                "cardholders": cardholders,
                "admissions": admissions,
                "tickets": tickets,
            },
            "weights": {
                "admissions": w_adm,
                "cardholders": w_card,
                "tickets": w_tix,
            },
        },
    )
