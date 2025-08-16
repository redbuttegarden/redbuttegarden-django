import datetime
import logging

from django.conf import settings
from django.core.files.storage import default_storage
from ics import Calendar, Event

from .utils.utils import strip_tags

logger = logging.getLogger(__name__)


def concert_page_changed(concert_page):
    logger.debug('Generating new iCal file with concerts from %s...', concert_page.title)
    c = Calendar()
    concerts = concert_page.sort_concerts(concert_page.get_visible_concerts())

    for concert in concerts:
        for concert_date in concert['concert_dates']:
            e = Event()
            e.uid = f"{concert_page.slug}-{concert_date.strftime('%Y%m%d')}@redbuttegarden.org"
            band_info_html = str(concert['band_info'])
            # Add spaces before HTML is stripped so text isn't mashed
            band_info = strip_tags(band_info_html.replace('><', '> <'))
            e.name = concert['band_name'] or band_info
            description = band_info
            description += f"\nBuy Link: {concert['ticket_url']}"
            if concert['gates_time']:
                description += f"\nGates Open: {concert['gates_time'].strftime('%-I:%M %p')}"
            if concert['show_time']:
                description += f"\nShow Time: {concert['show_time'].strftime('%-I:%M %p')}"

            e.location = 'Red Butte Garden Amphitheatre'
            e.url = concert['ticket_url']

            if concert['show_time']:
                event_start = datetime.datetime(year=concert_date.year,
                                                month=concert_date.month,
                                                day=concert_date.day,
                                                hour=concert['show_time'].hour,
                                                minute=concert['show_time'].minute,
                                                tzinfo=concert_date.tzinfo)
                e.begin = event_start
                e.end = event_start + datetime.timedelta(hours=3)  # Assuming concerts last 3 hours
            else:
                # Start time to be determined
                event_start = datetime.datetime(year=concert_date.year,
                                                month=concert_date.month,
                                                day=concert_date.day,
                                                hour=0,
                                                minute=0,
                                                tzinfo=concert_date.tzinfo)
                e.begin = event_start
                e.end = event_start + datetime.timedelta(hours=24)
                description += '\nConcert Time TBD. Check back soon.'

            if len(description) > 2000:
                description = description[:1997] + '...'
            e.description = description

            c.events.add(e)

    with default_storage.open(f'concert_calendar_{concert_page.slug}.ics', mode='w') as cal_file:
        if settings.STORAGES['default']['BACKEND'] == 'home.custom_storages.MediaStorage':
            # S3 Storage seems to require bytes regardless of write mode
            for line in c:
                cal_file.write(line.encode('utf-8'))
        else:
            cal_file.writelines(c)

    logger.debug('iCal file generated successfully: %s', f'concert_calendar_{concert_page.slug}.ics')


def concert_published_handler(sender, **kwargs):
    logger.info('concert_published_handler triggered!')
    instance = kwargs['instance']
    concert_page_changed(instance)
