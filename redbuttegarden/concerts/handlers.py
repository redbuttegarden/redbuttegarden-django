import datetime
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from ics import Calendar, Event

from .utils import strip_tags

logger = logging.getLogger(__name__)


def concert_page_changed(concert_page):
    logger.info('Generating new iCal file with concerts from %s...', concert_page.title)
    c = Calendar()
    concerts = concert_page.sort_concerts(concert_page.get_visible_concerts())

    for concert in concerts:
        e = Event()
        band_info_html = str(concert['band_info'])
        # Add spaces before HTML is stripped so text isn't mashed
        band_info = strip_tags(band_info_html.replace('><', '> <'))
        e.name = strip_tags(band_info)
        if concert['show_time']:
            event_start = datetime.datetime(year=concert.soonest_date.year,
                                  month=concert.soonest_date.month,
                                  day=concert.soonest_date.day,
                                  hour=concert['show_time'].hour,
                                  minute=concert['show_time'].minute,
                                  tzinfo=concert.soonest_date.tzinfo)
            e.begin = event_start
            e.end = event_start + datetime.timedelta(hours=3)
        else:
            # Start time to be determined
            event_start = datetime.datetime(year=concert.soonest_date.year,
                                            month=concert.soonest_date.month,
                                            day=concert.soonest_date.day,
                                            hour=0,
                                            minute=0,
                                            tzinfo=concert.soonest_date.tzinfo)
            e.begin = event_start
            e.end = event_start + datetime.timedelta(hours=24)
            e.description = 'Concert Time TBD. Check back soon.'
        c.events.add(e)

    with default_storage.open(f'concert_calendar_{concert_page.slug}.ics', mode='w') as cal_file:
        if settings.DEFAULT_FILE_STORAGE == 'home.custom_storages.MediaStorage':
            # S3 Storage seems to require bytes regardless of write mode
            for line in c:
                cal_file.write(line.encode('utf-8'))
        else:
            cal_file.writelines(c)



def concert_published_handler(sender, **kwargs):
    logger.info('concert_published_handler triggered!')
    instance = kwargs['instance']
    concert_page_changed(instance)
