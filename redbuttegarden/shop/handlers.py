import logging

from django.db.models.signals import pre_delete
from django.dispatch import receiver

from wagtail.contrib.frontend_cache.utils import PurgeBatch

from .models import Product, ShopIndexPage

logger = logging.getLogger(__name__)


def product_page_changed(product_page):
    logger.info('Checking for shop index pages containing {}'.format(product_page))
    # Find all the live ShopIndexPages that contain this product_page
    batch = PurgeBatch()
    for shop_index in ShopIndexPage.objects.live():
        logger.info('Checking if product_page is in {}'.format(shop_index))
        # The Paginator returns a list of Page class objects which won't match with our product_page object of class
        # Product so we need to get convert the list to Products by calling their specific
        # attribute first
        pages = shop_index.get_product_items().object_list
        product_items = [page.specific for page in pages]
        if product_page in product_items:
            logger.info('Adding shop_index to purge list')
            batch.add_page(shop_index)

    # Purge all the shop indexes we found in a single request
    logger.info('Purging!')
    batch.purge()


def product_published_handler(sender, **kwargs):
    logger.info('product_published_handler triggered!')
    instance = kwargs['instance']
    product_page_changed(instance)


@receiver(pre_delete, sender=Product)
def product_deleted_handler(instance, **kwargs):
    product_page_changed(instance)
