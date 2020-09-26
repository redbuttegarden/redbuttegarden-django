import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from wagtail.contrib.frontend_cache.utils import PurgeBatch

from .models import JournalPage, JournalIndexPage

logger = logging.getLogger(__name__)


def journal_page_changed(journal_page):
    logger.info('Checking for index pages containing {}'.format(journal_page))
    # Find all the live JournalIndexPages that contain this journal_page
    batch = PurgeBatch()
    for journal_index in JournalIndexPage.objects.live():
        logger.info('Checking if journal_page is in {}'.format(journal_index))
        # The Paginator returns a list of Page class objects which won't match with our journal_page object of class
        # JournalPage so we need to get convert the list to JournalPages by calling their specific
        # attribute first
        pages = journal_index.get_journal_items().object_list
        journal_items = [page.specific for page in pages]
        if journal_page in journal_items:
            logger.info('Adding journal_index to purge list')
            batch.add_page(journal_index)

    # Purge all the event indexes we found in a single request
    logger.info('Purging!')
    batch.purge()


def journal_published_handler(sender, **kwargs):
    logger.info('journal_published_handler triggered!')
    instance = kwargs['instance']
    journal_page_changed(instance)


@receiver(pre_delete, sender=JournalPage)
def journal_deleted_handler(instance, **kwargs):
    journal_page_changed(instance)
