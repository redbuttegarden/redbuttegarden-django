"""Public canonical URL and discovery coverage for dedication collections."""

import io

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image as PILImage
from rest_framework.test import APIClient
from wagtail.images import get_image_model

from plants.feeds import GardenBloomFeed, GardenBloomICalFeed
from plants.models import BloomEvent, Collection, SpeciesImage
from sitemaps.sitemaps import (
    CollectionDetailSitemap,
    DedicationDetailSitemap,
    SpeciesDetailSitemap,
)
from plants.tests.utils import (
    get_family,
    get_garden_area,
    get_genus,
    get_location,
    get_species,
)


def create_dedication() -> Collection:
    """Create a mapped collection classified in the dedication family."""

    family = get_family(name="Dedicataceae")
    genus = get_genus(family, name="Dedica")
    species = get_species(
        genus,
        name="honorata",
        full_name="Dedica honorata",
        vernacular_name="Dedication plant",
    )
    return Collection.objects.create(
        location=get_location(latitude=40.01, longitude=-111.01),
        garden=get_garden_area(code="DED-1"),
        species=species,
        plant_id="DED-1",
        commemoration_person="Ada Lovelace",
        commemoration_text="First line\n<script>alert('unsafe')</script>",
    )


def make_image_file() -> SimpleUploadedFile:
    """Build a small valid image for a dedication detail rendering test."""

    buffer = io.BytesIO()
    PILImage.new("RGB", (20, 20)).save(buffer, format="JPEG")
    return SimpleUploadedFile("dedication.jpg", buffer.getvalue(), content_type="image/jpeg")


@pytest.mark.django_db
def test_dedication_collection_uses_canonical_url_and_legacy_redirect(client):
    """Legacy collection paths permanently redirect classified dedications."""

    dedication = create_dedication()
    canonical_url = reverse("plants:dedication-detail", args=[dedication.pk])

    assert dedication.get_absolute_url() == canonical_url
    response = client.get(reverse("plants:collection-detail", args=[dedication.pk]))
    assert response.status_code == 301
    assert response["Location"] == canonical_url


@pytest.mark.django_db
def test_dedication_detail_escapes_multiline_text_and_hides_plant_metadata(client):
    """The dedicated page renders only safe dedication-oriented details."""

    dedication = create_dedication()
    response = client.get(dedication.get_absolute_url())

    content = response.content.decode()
    assert response.status_code == 200
    assert "First line<br>" in content
    assert "&lt;script&gt;alert(&#x27;unsafe&#x27;)&lt;/script&gt;" in content
    assert "Family:" not in content
    assert "Date Planted:" not in content


@pytest.mark.django_db
def test_dedication_detail_handles_null_text_and_shows_species_images(client):
    """Optional text stays absent while the related species imagery is displayed."""

    dedication = create_dedication()
    dedication.commemoration_text = None
    dedication.save(update_fields=["commemoration_text"])
    image = get_image_model().objects.create(title="Dedication flower", file=make_image_file())
    SpeciesImage.objects.create(
        species=dedication.species,
        image=image,
        caption="Flower for Ada",
        sort_order=0,
    )

    response = client.get(dedication.get_absolute_url())

    content = response.content.decode()
    assert response.status_code == 200
    assert "dedication-text" not in content
    assert "Flower for Ada" in content


@pytest.mark.django_db
def test_dedication_map_and_geojson_are_scoped_to_dedications(client, genus):
    """Dedicated and public discovery endpoints keep their records separate."""

    dedication = create_dedication()
    public_species = get_species(
        genus,
        name="publica",
        full_name="Plantus publica",
        vernacular_name="Public plant",
    )
    public_collection = Collection.objects.create(
        location=get_location(latitude=40.02, longitude=-111.02),
        garden=get_garden_area(code="PUB-1"),
        species=public_species,
        plant_id="PUB-1",
    )

    map_response = client.get(reverse("plants:dedication-map"))
    assert map_response.status_code == 200
    assert ("Ada Lovelace", "Ada Lovelace") in map_response.context["filter"].form.fields[
        "commemoration_person"
    ].choices

    dedication_data = client.get(reverse("plants:api-dedications-geojson")).json()
    public_data = client.get(reverse("plants:api-collections-geojson")).json()
    dedication_ids = {feature["properties"]["id"] for feature in dedication_data["features"]}
    public_ids = {feature["properties"]["id"] for feature in public_data["features"]}
    assert dedication_ids == {dedication.id}
    assert public_collection.id in public_ids
    assert dedication.id not in public_ids
    properties = dedication_data["features"][0]["properties"]
    assert set(properties) == {
        "id",
        "detail_url",
        "dedication_id",
        "honoree",
        "garden_name",
        "garden_area",
        "garden_code",
    }
    assert "species_id" not in properties
    assert "species_full_name" not in properties
    assert "plant_date" not in properties
    assert dedication.get_absolute_url() in map_response.content.decode()


@pytest.mark.django_db
def test_dedication_map_preloads_taxonomy_for_canonical_urls(client):
    """Dedication map results preload taxonomy used by canonical URLs."""

    dedication = create_dedication()
    response = client.get(reverse("plants:dedication-map"))
    rendered_dedication = next(
        item
        for item in response.context["dedications"]
        if item.pk == dedication.pk
    )

    assert "genus" in rendered_dedication.species._state.fields_cache
    assert "family" in rendered_dedication.species.genus._state.fields_cache


@pytest.mark.django_db
def test_dedication_geojson_and_detail_handle_a_missing_garden(client):
    """Mapped dedications without a garden relation remain publicly renderable."""

    dedication = create_dedication()
    dedication.garden = None
    dedication.save(update_fields=["garden"])

    detail_response = client.get(dedication.get_absolute_url())
    geojson_response = client.get(reverse("plants:api-dedications-geojson"))

    assert detail_response.status_code == 200
    assert geojson_response.status_code == 200
    properties = geojson_response.json()["features"][0]["properties"]
    assert properties["garden_name"] is None
    assert properties["garden_area"] is None
    assert properties["garden_code"] is None


@pytest.mark.django_db
def test_sitemaps_keep_dedications_in_their_own_sections(genus):
    """Public sitemap inventory does not mix dedication and plant detail URLs."""

    dedication = create_dedication()
    species = get_species(genus, name="publica", full_name="Plantus publica")
    public_collection = Collection.objects.create(
        species=species,
        plant_id="PUB-SITEMAP-1",
    )

    collection_items = list(CollectionDetailSitemap().items())
    dedication_items = list(DedicationDetailSitemap().items())
    species_items = list(SpeciesDetailSitemap().items())

    assert collection_items == [public_collection]
    assert dedication_items == [dedication]
    assert dedication.species not in species_items
    assert CollectionDetailSitemap().location(public_collection) == public_collection.get_absolute_url()
    assert DedicationDetailSitemap().location(dedication) == dedication.get_absolute_url()


@pytest.mark.django_db
def test_bloom_feeds_exclude_dedication_events(genus):
    """General bloom feeds do not surface dedication records beside plant content."""

    dedication = create_dedication()
    public_species = get_species(genus, name="publica", full_name="Plantus publica")
    public_event = BloomEvent.objects.create(title="Public bloom", species=public_species)
    dedication_event = BloomEvent.objects.create(
        title="Dedication bloom", species=dedication.species
    )
    mixed_event = BloomEvent.objects.create(title="Mixed bloom")
    mixed_event.collections.add(dedication)

    assert list(GardenBloomFeed().items()) == [public_event]
    assert list(GardenBloomICalFeed().items()) == [public_event]
    assert dedication_event not in GardenBloomFeed().items()
    assert mixed_event not in GardenBloomICalFeed().items()


@pytest.mark.django_db
def test_internal_collection_api_remains_authenticated_while_dedication_map_is_public(client):
    """Dedicated public map data does not weaken the authenticated data API boundary."""

    create_dedication()

    assert APIClient().get(reverse("plants:api-collection-list")).status_code == 401
    assert client.get(reverse("plants:api-dedications-geojson")).status_code == 200


@pytest.mark.django_db
def test_public_species_views_hide_dedication_pseudo_species(client):
    """Dedicataceae species are not available from public plant discovery URLs."""

    dedication = create_dedication()

    assert client.get(
        reverse("plants:species-detail", args=[dedication.species_id])
    ).status_code == 404
    assert client.get(
        reverse("plants:species-preview", args=[dedication.species_id])
    ).status_code == 404
