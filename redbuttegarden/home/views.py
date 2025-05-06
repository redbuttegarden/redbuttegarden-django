import logging

from django.http import JsonResponse, HttpResponse
from wagtail.snippets.views.snippets import SnippetViewSet

from home.models import CurrentWeather, RBGHours, HomePage


logger = logging.getLogger(__name__)


class RBGHoursViewSet(SnippetViewSet):
    model = RBGHours
    icon = 'time'
    inspect_view_enabled = True
    search_fields = ('name', 'additional_message', 'additional_emphatic_mesg', 'garden_open_message', 'garden_closed_message')


def latest_weather(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        weather = CurrentWeather.objects.first()
        if weather:
            return JsonResponse({
                'condition': weather.condition,
                'temperature': weather.temperature,
            })

    return HttpResponse(status=204)

def get_hours(request, page_id: int):
    """
    Get the RGGHours objects associated with the given page ID.
    """
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            page = HomePage.objects.get(id=page_id)
        except HomePage.DoesNotExist:
            return HttpResponse(status=404)

        hours_orderables = page.rbg_hours
        if hours_orderables.all().exists():
            json_response = {}
            for idx, rbg_hours_orderable in enumerate(hours_orderables.all()):
                json_response[idx] = {
                    'name': rbg_hours_orderable.hours.name,
                    'garden_open': rbg_hours_orderable.hours.garden_open.strftime('%-H:%M'),
                    'garden_close': rbg_hours_orderable.hours.garden_close.strftime('%-H:%M'),
                    'open_message': rbg_hours_orderable.hours.garden_open_message,
                    'closed_message': rbg_hours_orderable.hours.garden_closed_message,
                    'additional_message': rbg_hours_orderable.hours.additional_message,
                    'additional_emphatic_mesg': rbg_hours_orderable.hours.additional_emphatic_mesg,
                    'days_of_week': rbg_hours_orderable.hours.days_of_week,
                    'months_of_year': rbg_hours_orderable.hours.months_of_year,
                }
            return JsonResponse(json_response)
        else:
            logger.warning(f"Page with ID {page_id} does not have any RBGHours associated with it.")

    return HttpResponse(status=204)
