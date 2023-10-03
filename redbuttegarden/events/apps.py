import logging

from django.apps import AppConfig

from wagtail.signals import page_published

logger = logging.getLogger(__name__)


class EventsConfig(AppConfig):
    name = 'events'

    def ready(self):
        from .handlers import event_published_handler
        from .models import EventPage, EventGeneralPage

        page_published.connect(event_published_handler, sender=EventPage)
        page_published.connect(event_published_handler, sender=EventGeneralPage)
        logger.info('event_published_handler should be connected now')
