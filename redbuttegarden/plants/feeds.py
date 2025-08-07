import logging

from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import BloomEvent

logger = logging.getLogger(__name__)


class GardenBloomFeed(Feed):
    title = "What's Blooming Now @ Red Butte Garden"
    link = "/whats-blooming-now/"
    description = "Bloom events to describe which plants are blooming at Red Butte Garden."

    def items(self):
        bloom_events = BloomEvent.objects.order_by('-created_on')[:25]

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
