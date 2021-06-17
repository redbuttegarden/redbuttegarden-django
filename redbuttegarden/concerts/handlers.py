import logging

import datetime

from django.core.files import File
from ics import Calendar, Event

from .utils import strip_tags

logger = logging.getLogger(__name__)


def concert_page_changed(concert_page):
    c = Calendar()
    concerts = concert_page.sort_visible_concerts()

    for concert in concerts:
        e = Event()
        band_info_html = str(concert['band_info'])
        # Add spaces before HTML is stripped so text isn't mashed
        band_info = strip_tags(band_info_html.replace('><', '> <'))
        e.name = strip_tags(band_info)
        event_start = datetime.datetime(year=concert.soonest_date.year,
                              month=concert.soonest_date.month,
                              day=concert.soonest_date.day,
                              hour=concert['show_time'].hour,
                              minute=concert['show_time'].minute,
                              tzinfo=concert.soonest_date.tzinfo)
        e.begin = event_start
        e.end = event_start + datetime.timedelta(hours=3)
        c.events.add(e)

    with open(f'concert_calendar_{concert_page.slug}.ics', 'w') as cal_file:
        cal_file.writelines(c)


def concert_published_handler(sender, **kwargs):
    logger.info('concert_published_handler triggered!')
    instance = kwargs['instance']
    concert_page_changed(instance)
