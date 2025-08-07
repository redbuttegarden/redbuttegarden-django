import logging

from django.contrib.syndication.views import Feed
from django.urls import reverse
from django_ical.views import ICalFeed

from .models import BloomEvent

logger = logging.getLogger(__name__)


class GardenBloomFeed(Feed):
    title = "What's Blooming Now @ Red Butte Garden"
    link = "/whats-blooming-now/"
    description = "Bloom events to describe which plants are blooming at Red Butte Garden."

    def items(self):
        bloom_events = BloomEvent.objects.order_by('-bloom_start', '-created_on')[:25]

        return bloom_events

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        description = item.description

        if item.bloom_start:
            description += f"<br><strong>Bloom Start:</strong> {item.bloom_start.strftime('%B %d, %Y')}"
        if item.bloom_end:
            description += f"<br><strong>Bloom End:</strong> {item.bloom_end.strftime('%B %d, %Y')}"
        if item.description is None:
            return "No description available for this bloom event."

        if len(description) > 200:
            return description[:200] + '...'
        else:
            return description

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        if item.species:
            return reverse('plants:species-detail', args=[item.species.id])
        elif item.collections:
            return reverse('plants:collection-detail', args=[item.collections[0].id])
        else:
            return reverse('plants:plant-map')


class GardenBloomICalFeed(ICalFeed):
    """
    iCal version of the Garden Bloom Feed.
    """
    product_id = '-//redbuttegarden.org//BloomEvents//EN'
    timezone = 'MST'
    file_name = "bloom_events.ics"

    def items(self):
        return BloomEvent.objects.all().order_by('-bloom_start', '-created_on')

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.description

    def item_start_datetime(self, item):
        return item.bloom_start

    def item_end_datetime(self, item):
        return item.bloom_end

    def item_link(self, item):
        if item.species:
            return reverse('plants:species-detail', args=[item.species.id])
        elif item.collections:
            # Prioritize returning the first collection with a location the link matches up with the geolocation.
            collection_to_link = None
            for collection in item.collections.all():
                if collection.location:
                    collection_to_link = collection
                    break

            if collection_to_link:
                return reverse('plants:collection-detail', args=[collection_to_link.id])
            else:
                return reverse('plants:collection-detail', args=[item.collections[0].id])
        else:
            return reverse('plants:plant-map')

    def item_location(self, item):
        if item.area and item.area.name:
            return "Red Butte Garden " + item.area.name

        return "Red Butte Garden"

    def item_geolocation(self, item):
        """
        If the item has collections with a location, return the first latitude and longitude it finds.
        """
        if item.collections:
            for collection in item.collections.all():
                if collection.location:
                    return collection.location.latitude, collection.location.longitude
