import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from wagtail.contrib.frontend_cache.utils import PurgeBatch

from .models import GeneralIndexPage, GeneralPage, TwoColumnGeneralPage

logger = logging.getLogger(__name__)


def general_page_changed(general_page):
    logger.info('Checking for index pages containing {}'.format(general_page))
    # Find all the live GeneralIndexPages that contain this general_page
    batch = PurgeBatch()
    for general_index in GeneralIndexPage.objects.live():
        logger.info('Checking if general_page is in {}'.format(general_index))
        # The Paginator returns a list of Page class objects which won't match with our general_page object of class
        # GeneralPage or TwoColumnGeneralPage, we need to get convert the list to EventPages by calling their specific
        # attribute first
        pages = general_index.get_general_items().object_list
        general_items = [page.specific for page in pages]
        if general_page in general_items:
            logger.info('Adding general_index to purge list')
            batch.add_page(general_index)

    # Purge all the event indexes we found in a single request
    logger.info('Purging!')
    batch.purge()


def general_published_handler(sender, **kwargs):
    logger.info('general_published_handler triggered!')
    instance = kwargs['instance']
    general_page_changed(instance)


@receiver(pre_delete, sender=GeneralPage)
def general_deleted_handler(instance, **kwargs):
    general_page_changed(instance)


@receiver(pre_delete, sender=TwoColumnGeneralPage)
def tc_general_deleted_handler(instance, **kwargs):
    general_page_changed(instance)
