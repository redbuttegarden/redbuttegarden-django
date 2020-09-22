import logging

from django.apps import AppConfig

from wagtail.core.signals import page_published

logger = logging.getLogger(__name__)


class HomeConfig(AppConfig):
    name = 'home'

    def ready(self):
        from .handlers import general_published_handler
        from .models import GeneralPage, TwoColumnGeneralPage

        page_published.connect(general_published_handler, sender=GeneralPage)
        page_published.connect(general_published_handler, sender=TwoColumnGeneralPage)
        logger.info('general_published_handler should be connected now')
