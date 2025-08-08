import logging

from django.contrib.syndication.views import Feed
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

from concerts.models import ConcertPage

logger = logging.getLogger(__name__)


class ConcertsFeed(Feed):
    title = "Red Butte Garden Concert Series"
    link = "/concerts/"
    description = "Red Butte Garden Concert Series"

    def items(self):
        try:
            concert_page = ConcertPage.objects.live().filter(slug='concerts').first()
        except ConcertPage.DoesNotExist:
            return None

        # Get the concerts from the ConcertPage body stream field
        concerts = concert_page.get_visible_concerts()

        return concert_page.sort_concerts(concerts)

    def item_title(self, item):
        return item['band_name'] or 'Example Band Name'

    def item_description(self, item):
        # Render the concert details using a template
        return mark_safe(render_to_string('feeds/concert_description.html',
                                          {'band_info': item['band_info']}))

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        return item['ticket_url']
