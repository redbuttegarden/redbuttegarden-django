import logging

from django.contrib.postgres.search import SearchVector
from django.core.exceptions import ValidationError
from django.db.models import QuerySet
from django.http import QueryDict
from django.urls import reverse
from geojson import FeatureCollection, Feature, Point

from .models import Collection

logger = logging.getLogger(__name__)


TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}


def get_feature_collection(collections: QuerySet[Collection]) -> FeatureCollection:
    """Return GeoJSON properties required by the general plant map."""

    features = []
    for collection in collections:
        plant_date = (
            collection.plant_date.strftime("%m/%d/%Y")
            if collection.plant_date
            else None
        )

        feature = Feature(
            geometry=Point(
                (collection.location.longitude, collection.location.latitude)
            ),
            properties={
                "id": collection.id,
                "species_id": collection.species.id,
                "family_name": collection.species.genus.family.name,
                "genus_name": collection.species.genus.name,
                "species_name": collection.species.name,
                "species_full_name": collection.species.full_name,
                "vernacular_name": collection.species.vernacular_name,
                "habit": collection.species.habit,  # this is your icon key
                "hardiness": collection.species.hardiness,
                "water_regime": collection.species.water_regime,
                "exposure": collection.species.exposure,
                "bloom_time": collection.species.bloom_time,
                "plant_size": collection.species.plant_size,
                "garden_area": collection.garden.area if collection.garden else None,
                "garden_name": collection.garden.name if collection.garden else None,
                "garden_code": collection.garden.code if collection.garden else None,
                "planted_on": plant_date,
                "url": collection.get_absolute_url(),
            },
        )
        features.append(feature)

    return FeatureCollection(features)


def get_memorial_tribute_feature_collection(
    memorials_and_tributes: QuerySet[Collection],
) -> FeatureCollection:
    """Return GeoJSON with only the fields needed by the public memorial-and-tribute map."""

    features = []
    for memorial_tribute in memorials_and_tributes:
        features.append(
            Feature(
                geometry=Point(
                    (memorial_tribute.location.longitude, memorial_tribute.location.latitude)
                ),
                properties={
                    "id": memorial_tribute.id,
                    "detail_url": memorial_tribute.get_absolute_url(),
                    "memorial_tribute_id": memorial_tribute.plant_id,
                    "honoree": memorial_tribute.commemoration_person,
                    "garden_name": memorial_tribute.garden.name if memorial_tribute.garden else None,
                    "garden_area": memorial_tribute.garden.area if memorial_tribute.garden else None,
                    "garden_code": memorial_tribute.garden.code if memorial_tribute.garden else None,
                },
            )
        )

    return FeatureCollection(features)


def style_message(request, species, collection, original_message):
    if species:
        url = request.build_absolute_uri(
            reverse("plants:species-detail", args=[species.id])
        )
    elif collection:
        url = request.build_absolute_uri(collection.get_absolute_url())
    else:
        logger.error("No species or collection provided")
        raise ValueError("No species or collection provided")

    return f"""The following feedback has been provided for this page: {url}
    
Be wary of the message contents since it's possible it could contain malicious content.

Message Contents:
    
    {original_message}"""


def clean_querydict(qd: QueryDict) -> QueryDict:
    """
    Normalize query params:
    - drop empty values
    - normalize checkbox truthiness to "true"
    - preserve multi-valued params
    """
    if not qd:
        return qd

    cleaned = QueryDict(mutable=True)

    for key in qd.keys():
        values = qd.getlist(key)
        for v in values:
            if v in ("", None):
                continue

            if isinstance(v, str):
                sv = v.strip()
                if sv == "":
                    continue

                # normalize booleans to "true" only when truthy
                if sv.lower() in TRUE_VALUES:
                    cleaned.appendlist(key, "true")
                else:
                    cleaned.appendlist(key, sv)
            else:
                cleaned.appendlist(key, v)

    return cleaned
