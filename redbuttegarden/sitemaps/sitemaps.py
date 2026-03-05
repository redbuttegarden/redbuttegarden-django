from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from plants.models import Collection, Species


class PlantsStaticViewsSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5

    def items(self):
        return [
            "plants:plant-map",
            "plants:collection-search",
            "plants:top-trees",
        ]

    def location(self, item):
        return reverse(item)


class CollectionDetailSitemap(Sitemap):
    limit = 5000
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return Collection.objects.all().only("id", "last_modified").order_by("id")

    def location(self, obj):
        return reverse("plants:collection-detail", kwargs={"collection_id": obj.pk})

    def lastmod(self, obj):
        return obj.last_modified


class SpeciesDetailSitemap(Sitemap):
    limit = 5000
    changefreq = "monthly"
    priority = 0.6

    def items(self):
        return Species.objects.all().only("id").order_by("id")

    def location(self, obj):
        return reverse("plants:species-detail", kwargs={"species_id": obj.pk})
