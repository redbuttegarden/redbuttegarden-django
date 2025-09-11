from django.db.models.signals import post_save
from django.dispatch import receiver
from wagtail.contrib.frontend_cache.utils import PurgeBatch
from wagtail.documents.models import Document
from wagtail.images.models import Image


@receiver(post_save, sender=Document)
def invalidate_document_cache(sender, instance, **kwargs):
    # Get the document's URL
    doc_url = instance.url

    # Purge the cache for this URL
    batch = PurgeBatch()
    batch.add_url(doc_url)
    batch.purge()


@receiver(post_save, sender=Image)
def invalidate_image_cache(sender, instance, **kwargs):
    # Get the image's URL
    image_url = instance.file.url

    # Purge the cache for this URL
    batch = PurgeBatch()
    batch.add_url(image_url)
    batch.purge()
