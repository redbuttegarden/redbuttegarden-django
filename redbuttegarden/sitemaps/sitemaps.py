from datetime import datetime

from django.contrib.sitemaps import Sitemap
from django.db.models import QuerySet
from django.urls import reverse

from plants.models import Collection, Species
from plants.selectors import memorial_tribute_collections, public_collections, public_species


class PlantsStaticViewsSitemap(Sitemap):
    """List public plant and memorial-and-tribute discovery pages."""

    changefreq = "weekly"
    priority = 0.5

    def items(self) -> list[str]:
        """Return named routes for public discovery landing pages."""

        return [
            "plants:plant-map",
            "plants:memorial-tribute-map",
            "plants:collection-search",
            "plants:top-trees",
        ]

    def location(self, item: str) -> str:
        """Return the URL for a named public discovery route."""

        return reverse(item)


class CollectionDetailSitemap(Sitemap):
    """List canonical detail pages for normal plant collections only."""

    limit = 5000
    changefreq = "weekly"
    priority = 0.7

    def items(self) -> QuerySet[Collection]:
        """Return normal plant collections without memorial-or-tribute records."""

        return public_collections().only("id", "last_modified").order_by("id")

    def location(self, obj: Collection) -> str:
        """Return a normal collection's canonical public URL."""

        return reverse("plants:collection-detail", kwargs={"collection_id": obj.pk})

    def lastmod(self, obj: Collection) -> datetime:
        """Return the most recent modification timestamp for a collection."""

        return obj.last_modified


class MemorialTributeDetailSitemap(Sitemap):
    """List canonical detail pages for public memorial-or-tribute records only."""

    limit = 5000
    changefreq = "weekly"
    priority = 0.7

    def items(self) -> QuerySet[Collection]:
        """Return memorial-or-tribute collections in a dedicated sitemap section."""

        return memorial_tribute_collections().only("id", "last_modified").order_by("id")

    def location(self, obj: Collection) -> str:
        """Return a memorial or tribute's canonical public URL."""

        return reverse("plants:memorial-tribute-detail", kwargs={"collection_id": obj.pk})

    def lastmod(self, obj: Collection) -> datetime:
        """Return the most recent modification timestamp for a memorial or tribute."""

        return obj.last_modified


class SpeciesDetailSitemap(Sitemap):
    """List normal plant species detail pages only."""

    limit = 5000
    changefreq = "monthly"
    priority = 0.6

    def items(self) -> QuerySet[Species]:
        """Return normal plant species without memorial-or-tribute pseudo-species."""

        return public_species().only("id").order_by("id")

    def location(self, obj: Species) -> str:
        """Return the canonical public URL for a plant species."""

        return reverse("plants:species-detail", kwargs={"species_id": obj.pk})
