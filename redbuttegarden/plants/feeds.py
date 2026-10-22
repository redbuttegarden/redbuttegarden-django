import logging

from django.contrib.syndication.views import Feed
from django.db.models import QuerySet
from django.urls import reverse
from django_ical.views import ICalFeed

from .constants import DEDICATION_FAMILY_NAME
from .models import BloomEvent

logger = logging.getLogger(__name__)


def public_bloom_events() -> QuerySet[BloomEvent]:
    """Return bloom events that do not include dedication-only collection records."""

    return (
        BloomEvent.objects.exclude(species__genus__family__name=DEDICATION_FAMILY_NAME)
        .exclude(collections__species__genus__family__name=DEDICATION_FAMILY_NAME)
        .distinct()
    )


class GardenBloomFeed(Feed):
    """RSS feed for public blooming plant events."""

    title = "What's Blooming Now @ Red Butte Garden"
    link = "/whats-blooming-now/"
    description = "Bloom events to describe which plants are blooming at Red Butte Garden."

    def items(self) -> QuerySet[BloomEvent]:
        """Return only bloom events that belong in general plant discovery."""

        bloom_events = public_bloom_events().order_by('-bloom_start', '-created_on')[:25]

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

        if len(description) > 2000:
            return description[:1997] + '...'
        else:
            return description

    # item_link is only needed if NewsItem has no get_absolute_url method.
    def item_link(self, item):
        if (
            item.species
            and item.species.genus.family.name != DEDICATION_FAMILY_NAME
        ):
            return reverse('plants:species-detail', args=[item.species.id])
        collection = item.collections.first()
        if collection:
            return collection.get_absolute_url()
        return reverse('plants:plant-map')


class GardenBloomICalFeed(ICalFeed):
    """
    iCal version of the Garden Bloom Feed.
    """
    product_id = '-//redbuttegarden.org//BloomEvents//EN'
    timezone = 'MST'
    file_name = "bloom_events.ics"

    def items(self) -> QuerySet[BloomEvent]:
        """Return only bloom events that belong in general plant discovery."""

        return public_bloom_events().order_by('-bloom_start', '-created_on')

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        description = item.description

        if item.bloom_start:
            description += f"\nBloom Start: {item.bloom_start.strftime('%B %d, %Y')}"
        if item.bloom_end:
            description += f"\nBloom End: {item.bloom_end.strftime('%B %d, %Y')}"
        if item.url:
            description += f"\nMore Info: {item.url}"
        if item.description is None:
            return "No description available for this bloom event."

        if len(description) > 2000:
            return description[:1997] + '...'
        else:
            return description

    def item_start_datetime(self, item):
        return item.bloom_start

    def item_end_datetime(self, item):
        return item.bloom_end

    def item_link(self, item):
        if (
            item.species
            and item.species.genus.family.name != DEDICATION_FAMILY_NAME
        ):
            return reverse('plants:species-detail', args=[item.species.id])
        # Prioritize a collection with a location so the link matches geolocation.
        collections = item.collections.all()
        collection = next(
            (candidate for candidate in collections if candidate.location),
            collections.first(),
        )
        if collection:
            return collection.get_absolute_url()
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
