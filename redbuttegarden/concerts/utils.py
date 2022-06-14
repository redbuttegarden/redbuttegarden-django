from abc import ABC
from html.parser import HTMLParser
from io import StringIO

from django.utils import timezone

"""
HTML Stripping Credit:
https://stackoverflow.com/a/925630
"""
class MLStripper(HTMLParser, ABC):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.text = StringIO()
    def handle_data(self, d):
        self.text.write(d)
    def get_data(self):
        return self.text.getvalue()

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def live_in_the_past(concert_block_value):
    """
    Boolean indicating if the concert's live performance has already occurred.
    """
    # Concert dates should already be sorted from the ConcertPage get_context method
    return timezone.now() > concert_block_value['concert_dates'][-1]


def on_demand_expired(concert_block_value):
    """
    Boolean indicating if the on-demand performance is still available.

    Returns True if concert is virtual but does not offer on-demand.
    """
    if concert_block_value['available_until']:
        return timezone.now() > concert_block_value['available_until']
    elif concert_block_value['virtual'] and concert_block_value['available_until'] is None:
        return True
