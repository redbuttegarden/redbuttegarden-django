import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from wagtail.contrib.frontend_cache.utils import PurgeBatch

from .models import EventIndexPage, EventPage

logger = logging.getLogger(__name__)


def event_page_changed(event_page):
    logger.info('Checking for index pages containing {}'.format(event_page))
    # Find all the live EventIndexPages that contain this event_page
    batch = PurgeBatch()
    for event_index in EventIndexPage.objects.live():
        logger.info('Checking if event_page is in {}'.format(event_index))
        # The Paginator returns a list of Page class objects which won't match with our event_page object of class
        # EventPage, we need to get convert the list to EventPages by calling their specific attribute first
        pages = event_index.get_event_items().object_list
        event_items = [page.specific for page in pages]
        if event_page in event_items:
            logger.info(f'Adding {event_index} to purge list')
            batch.add_page(event_index)

    # Also purge event page category paths
    category_paths = [f"/events/e-cat/{category.slug}/" for category in event_page.event_categories.all()]
    batch.add_urls[category_paths]

    # Purge all the event indexes we found in a single request
    logger.info('Purging!')
    batch.purge()


def event_published_handler(sender, **kwargs):
    logger.info('event_published_handler triggered!')
    instance = kwargs['instance']
    event_page_changed(instance)


@receiver(pre_delete, sender=EventPage)
def event_deleted_handler(instance, **kwargs):
    event_page_changed(instance)
