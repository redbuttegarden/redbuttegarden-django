import logging

from django.apps import AppConfig

from wagtail.signals import page_published

logger = logging.getLogger(__name__)


class ShopConfig(AppConfig):
    name = 'shop'

    def ready(self):
        from .handlers import product_published_handler
        from .models import Product

        page_published.connect(product_published_handler, sender=Product)
        logger.info('product_published_handler should be connected now')
