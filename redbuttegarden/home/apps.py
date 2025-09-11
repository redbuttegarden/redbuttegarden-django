import logging

from django.apps import AppConfig

from wagtail.signals import page_published

logger = logging.getLogger(__name__)


class HomeConfig(AppConfig):
    name = 'home'

    def ready(self):
        from .handlers import general_published_handler, send_to_automate
        from .models import GeneralPage, TwoColumnGeneralPage
        # Implicitly register signals by importing them
        from . import signals

        page_published.connect(general_published_handler, sender=GeneralPage)
        page_published.connect(general_published_handler, sender=TwoColumnGeneralPage)
        logger.info('general_published_handler should be connected now')

        # Send_to_automate deals with all publish events; not restricted to just home app models
        page_published.connect(send_to_automate)
