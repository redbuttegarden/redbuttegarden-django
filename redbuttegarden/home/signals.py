from wagtail.documents.signals import document_saved
from wagtail.contrib.frontend_cache.utils import purge_url
from django.dispatch import receiver


@receiver(document_saved)
def invalidate_document_cache(sender, instance, **kwargs):
    # Get the document's URL
    doc_url = instance.url

    # Purge the cache for this URL
    purge_url(doc_url)
