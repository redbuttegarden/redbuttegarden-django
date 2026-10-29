import logging

from django.apps import AppConfig

from wagtail.signals import page_published

logger = logging.getLogger(__name__)


class HomeConfig(AppConfig):
    name = 'home'

    def ready(self):
        from .handlers import general_published_handler, send_to_automate
        from .models import GeneralPage, TwoColumnGeneralPage
        from wagtail.images.models import Image
        # Implicitly register signals by importing them
        from . import signals
        from . import nav_settings

        # Override the help_text on the description field
        description_field = Image._meta.get_field('description')
        description_field.help_text = "Enter a detailed description for accessibility (ALT text)."

        page_published.connect(general_published_handler, sender=GeneralPage)
        page_published.connect(general_published_handler, sender=TwoColumnGeneralPage)
        logger.info('general_published_handler should be connected now')

        # Send_to_automate deals with all publish events; not restricted to just home app models
        page_published.connect(send_to_automate)
