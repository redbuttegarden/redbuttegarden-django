from django.utils import timezone


def live_in_the_past(concert_block):
    """
    Boolean indicating if the concert's live performance has already occurred.
    """
    # Concert dates should already be sorted from the ConcertPage get_context method
    return timezone.now() > concert_block['concert_dates'][-1]


def on_demand_expired(concert_block):
    """
    Boolean indicating if the on-demand performance is still available.

    Returns True if concert is virtual but does not offer on-demand.
    """
    if concert_block['available_until']:
        return timezone.now() > concert_block['available_until']
    elif concert_block['virtual'] and concert_block['available_until'] is None:
        return True