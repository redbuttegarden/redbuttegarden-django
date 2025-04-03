import datetime

from concerts.models import Concert


def summarize_tickets(ticket_queryset, concert_queryset=None):
    """
    Return a dictionary summarizing a Ticket and optionally a Concert
    queryset by concert including a count of the total number of
    tickets for each concert.

    If a concert_queryset is not provided it will be calculated from
    the provided ticket_queryset.
    """
    if concert_queryset is None:
        concert_queryset = Concert.objects.filter(pk__in=ticket_queryset.values('concert').distinct())

    concert_tickets_summary_info = {}
    for concert in concert_queryset:
        concert_tickets_summary_info[concert.pk] = {
            'name': concert.name,
            'begin': concert.begin,
            'doors': concert.begin - datetime.timedelta(
                minutes=concert.doors_before_event_time_minutes),
            'image_url': concert.image_url,
            'ticket_count': ticket_queryset.filter(concert=concert).count(),
        }

    return concert_tickets_summary_info
