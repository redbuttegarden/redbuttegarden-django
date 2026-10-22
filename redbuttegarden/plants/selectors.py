"""Query selectors that keep dedications separate from public plant discovery."""

from django.db.models import QuerySet

from .constants import DEDICATION_FAMILY_NAME
from .models import Collection, Species


def dedication_collections() -> QuerySet[Collection]:
    """Return collections explicitly classified as dedications."""

    return Collection.objects.filter(
        species__genus__family__name=DEDICATION_FAMILY_NAME
    )


def public_collections() -> QuerySet[Collection]:
    """Return collections that belong in general plant discovery."""

    return Collection.objects.exclude(
        species__genus__family__name=DEDICATION_FAMILY_NAME
    )


def public_species() -> QuerySet[Species]:
    """Return species that belong in general plant discovery."""

    return Species.objects.exclude(genus__family__name=DEDICATION_FAMILY_NAME)
