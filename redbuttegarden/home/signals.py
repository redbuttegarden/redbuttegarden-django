from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.urls import reverse
from wagtail.contrib.frontend_cache.utils import PurgeBatch
from wagtail.documents.models import Document
from wagtail.images.models import Image
from wagtail.models import Site

from .nav_settings import NavigationSettings


@receiver(post_save, sender=Document)
def invalidate_document_cache_on_save(sender, instance, **kwargs):
    # Get the document's URL
    doc_url = instance.url

    # Purge the cache for this URL
    batch = PurgeBatch()
    batch.add_url(doc_url)
    batch.purge()


@receiver(post_save, sender=Image)
def invalidate_image_cache_on_save(sender, instance, **kwargs):
    # Get the image's URL
    image_url = instance.file.url

    # Purge the cache for this URL
    batch = PurgeBatch()
    batch.add_url(image_url)
    batch.purge()


@receiver(post_delete, sender=Document)
def invalidate_document_cache_on_delete(sender, instance, **kwargs):
    # Get the document's URL
    doc_url = instance.url

    # Purge the cache for this URL
    batch = PurgeBatch()
    batch.add_url(doc_url)
    batch.purge()


@receiver(post_delete, sender=Image)
def invalidate_image_cache_on_delete(sender, instance, **kwargs):
    # Get the image's URL
    image_url = instance.file.url

    # Purge the cache for this URL
    batch = PurgeBatch()
    batch.add_url(image_url)
    batch.purge()


def _nav_fragment_url_for_site(site: Site) -> str:
    """
    Build an absolute URL to the nav fragment endpoint for a given Site.
    If you only need the path, return reverse(...) instead.
    """
    path = reverse("nav-fragment")  # <-- ensure your nav_fragment view has this name
    root_url = site.root_url or ""  # e.g. https://example.com
    return f"{root_url}{path}" if root_url else path


def purge_navigation_fragment(site: Site) -> None:
    batch = PurgeBatch()
    batch.add_url(_nav_fragment_url_for_site(site))
    batch.purge()


@receiver(post_save, sender=NavigationSettings)
def invalidate_nav_cache_on_save(sender, instance: NavigationSettings, **kwargs):
    # instance.site is a FK on BaseSiteSetting
    site = instance.site
    if site:
        purge_navigation_fragment(site)


@receiver(post_delete, sender=NavigationSettings)
def invalidate_nav_cache_on_delete(sender, instance: NavigationSettings, **kwargs):
    site = instance.site
    if site:
        purge_navigation_fragment(site)
