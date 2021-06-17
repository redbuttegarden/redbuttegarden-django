import logging

from django.apps import AppConfig

from wagtail.core.signals import page_published

logger = logging.getLogger(__name__)


class ConcertsConfig(AppConfig):
    name = 'concerts'

    def ready(self):
        from .handlers import concert_published_handler
        from .models import ConcertPage

        page_published.connect(concert_published_handler, sender=ConcertPage)
        logger.info('concert_published_handler should be connected now')
