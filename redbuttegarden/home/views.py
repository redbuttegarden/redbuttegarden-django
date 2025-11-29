import logging

from django.conf import settings
from django.http import JsonResponse, HttpResponse, Http404
from wagtail.snippets.views.snippets import SnippetViewSet

from home.models import CurrentWeather, RBGHours, HomePage

logger = logging.getLogger(__name__)


class RBGHoursViewSet(SnippetViewSet):
    model = RBGHours
    icon = "time"
    inspect_view_enabled = True
    search_fields = (
        "name",
        "additional_message",
        "additional_emphatic_mesg",
        "garden_open_message",
        "garden_closed_message",
    )


def latest_weather(request):
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        weather = CurrentWeather.objects.first()
        if weather:
            return JsonResponse(
                {
                    "condition": weather.condition,
                    "temperature": weather.temperature,
                }
            )

    return HttpResponse(status=204)


def get_hours(request, page_id: int):
    """
    Get the RGGHours objects associated with the given page ID.
    """
    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        try:
            page = HomePage.objects.get(id=page_id)
        except HomePage.DoesNotExist:
            return HttpResponse(status=404)

        hours_orderables = page.rbg_hours
        if hours_orderables.all().exists():
            json_response = {}
            for idx, rbg_hours_orderable in enumerate(hours_orderables.all()):
                json_response[idx] = {
                    "name": rbg_hours_orderable.hours.name,
                    "garden_open": (
                        rbg_hours_orderable.hours.garden_open.strftime("%-H:%M")
                        if rbg_hours_orderable.hours.garden_open
                        else None
                    ),
                    "garden_close": (
                        rbg_hours_orderable.hours.garden_close.strftime("%-H:%M")
                        if rbg_hours_orderable.hours.garden_close
                        else None
                    ),
                    "open_message": rbg_hours_orderable.hours.garden_open_message,
                    "closed_message": rbg_hours_orderable.hours.garden_closed_message,
                    "additional_message": rbg_hours_orderable.hours.additional_message,
                    "additional_emphatic_mesg": rbg_hours_orderable.hours.additional_emphatic_mesg,
                    "days_of_week": rbg_hours_orderable.hours.days_of_week,
                    "months_of_year": rbg_hours_orderable.hours.months_of_year,
                }
            return JsonResponse(json_response)
        else:
            logger.warning(
                f"Page with ID {page_id} does not have any RBGHours associated with it."
            )

    return HttpResponse(status=204)


def robots_txt(request):
    lines = [
        # Allow major search engine bots
        "User-agent: Googlebot",
        "Allow: /",
        "User-agent: Bingbot",
        "Allow: /",
        "User-agent: Slurp",
        "Allow: /",
        "User-agent: DuckDuckBot",
        "Allow: /",
        "User-agent: Baiduspider",
        "Allow: /",
        "User-agent: Yandex",
        "Allow: /",
        # Disallow known AI training bots,
        "User-agent: GPTBot",
        "Disallow: /",
        "User-agent: ChatGPT-User",
        "Disallow: /",
        "User-agent: CCBot",
        "Disallow: /",
        "User-agent: anthropic-ai",
        "Disallow: /",
        "User-agent: ClaudeBot",
        "Disallow: /",
        "User-agent: facebookexternalhit",
        "Disallow: /",
        "User-agent: Bytespider",
        "Disallow: /",
        "User-agent: Amazonbot",
        "Disallow: /",
        "User-agent: *",
        "Disallow: /admin/",
        "Disallow: /accounts/",
        "Disallow: /api/",
        "Disallow: /*/api/",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def indexnow_key_file(request):
    key = getattr(settings, "INDEXNOW_KEY", "")
    if not key:
        # Optional: hide misconfig instead of serving blank
        raise Http404("IndexNow key not configured")

    return HttpResponse(key, content_type="text/plain")
