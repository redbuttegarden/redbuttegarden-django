import logging

from django.apps import AppConfig

from wagtail.signals import page_published

logger = logging.getLogger(__name__)


class JournalConfig(AppConfig):
    name = 'journal'

    def ready(self):
        from .handlers import journal_published_handler
        from .models import JournalPage

        page_published.connect(journal_published_handler, sender=JournalPage)
        logger.info('journal_published_handler should be connected now')
