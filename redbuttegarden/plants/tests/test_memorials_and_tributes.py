"""Public canonical URL and discovery coverage for memorials and tributes."""

import io
from pathlib import Path

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image as PILImage
from rest_framework.test import APIClient
from wagtail.images import get_image_model

from plants.feeds import GardenBloomFeed, GardenBloomICalFeed
from plants.filters import MemorialTributeFilter
from plants.models import BloomEvent, Collection, PlantImage, SpeciesImage
from sitemaps.sitemaps import (
    CollectionDetailSitemap,
    MemorialTributeDetailSitemap,
    SpeciesDetailSitemap,
)
from plants.tests.utils import (
    get_family,
    get_garden_area,
    get_genus,
    get_location,
    get_species,
)


def create_memorial_tribute() -> Collection:
    """Create a mapped collection classified in the memorial-and-tribute family."""

    family = get_family(name="Dedicataceae")
    genus = get_genus(family, name="Dedica")
    species = get_species(
        genus,
        name="honorata",
        full_name="Dedica honorata",
        vernacular_name="Memorial and tribute plant",
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
    """Build a small valid image for a memorial-and-tribute detail test."""

    buffer = io.BytesIO()
    PILImage.new("RGB", (20, 20)).save(buffer, format="JPEG")
    return SimpleUploadedFile("memorial_tribute.jpg", buffer.getvalue(), content_type="image/jpeg")


def test_memorial_tribute_map_javascript_uses_memorials_and_tributes_copy():
    """Keep map-rendered public copy aligned with the memorials terminology."""

    source = Path("plants/static/plants/js/memorial_tribute_map.js").read_text()

    assert "Memorial or tribute detail page" in source
    assert "Memorial or Tribute ID" in source
    assert "Unable to load memorials and tributes." in source
    assert '"/plants/api/memorials-and-tributes-geojson/"' in source
    assert 'properties.memorial_tribute_id' in source


@pytest.mark.django_db
def test_memorial_tribute_collection_uses_the_memorial_tribute_canonical_url(client):
    """Classified collections redirect from general discovery to the new canonical URL."""

    memorial_tribute = create_memorial_tribute()
    canonical_url = reverse("plants:memorial-tribute-detail", args=[memorial_tribute.pk])

    assert memorial_tribute.get_absolute_url() == canonical_url
    response = client.get(reverse("plants:collection-detail", args=[memorial_tribute.pk]))
    assert response.status_code == 301
    assert response["Location"] == canonical_url
@pytest.mark.django_db
def test_memorial_tribute_routes_resolve(client):
    """The memorials-and-tributes public map and GeoJSON routes resolve."""

    create_memorial_tribute()

    assert client.get("/plants/memorials-and-tributes-map/").status_code == 200
    assert client.get("/plants/api/memorials-and-tributes-geojson/").status_code == 200


@pytest.mark.django_db
def test_memorial_tribute_detail_escapes_multiline_text_and_hides_plant_metadata(client):
    """The memorial-or-tribute page renders only safe relevant details."""

    memorial_tribute = create_memorial_tribute()
    response = client.get(memorial_tribute.get_absolute_url())

    content = response.content.decode()
    assert response.status_code == 200
    assert "First line<br>" in content
    assert "&lt;script&gt;alert(&#x27;unsafe&#x27;)&lt;/script&gt;" in content
    assert "Family:" not in content
    assert "Date Planted:" not in content
    assert "Memorial or Tribute Detail" in content
    assert 'aria-label="Memorial or tribute details"' in content
    assert "Memorial or Tribute ID" in content
    assert "Memorial or Tribute</dt>" in content


@pytest.mark.django_db
def test_memorial_tribute_detail_handles_null_text_and_shows_plant_images(client):
    """Optional text stays absent while only its own imagery is displayed."""

    memorial_tribute = create_memorial_tribute()
    memorial_tribute.commemoration_text = None
    memorial_tribute.save(update_fields=["commemoration_text"])
    image = get_image_model().objects.create(title="Memorial tribute flower", file=make_image_file())
    PlantImage.objects.create(
        collection=memorial_tribute,
        image=image,
        caption="Flower for Ada",
        sort_order=0,
    )

    response = client.get(memorial_tribute.get_absolute_url())

    content = response.content.decode()
    assert response.status_code == 200
    assert "memorial-tribute-text" not in content
    assert "Flower for Ada" in content


@pytest.mark.django_db
def test_memorial_tribute_detail_renders_ordered_accessible_image_gallery(client):
    """Memorial-or-tribute images render as a primary image and ordered thumbnails."""

    memorial_tribute = create_memorial_tribute()
    first_image = get_image_model().objects.create(
        title="First memorial_tribute flower", file=make_image_file()
    )
    second_image = get_image_model().objects.create(
        title="Second memorial_tribute flower", file=make_image_file()
    )
    PlantImage.objects.create(
        collection=memorial_tribute,
        image=second_image,
        caption="Second flower",
        copyright="Garden photographer",
        sort_order=2,
    )
    PlantImage.objects.create(
        collection=memorial_tribute,
        image=first_image,
        sort_order=1,
    )

    response = client.get(memorial_tribute.get_absolute_url())

    content = response.content.decode()
    assert response.status_code == 200
    assert content.index("First memorial_tribute flower") < content.index("Second flower")
    assert 'class="memorial-tribute-gallery__primary"' in content
    assert 'class="memorial-tribute-gallery__thumbnail"' in content
    assert 'id="memorial-tribute-gallery-modal"' in content
    assert "max-1600x1200" in content
    assert "Garden photographer" in content
    assert 'data-gallery-index="0"' in content
    assert 'data-gallery-index="1"' in content


@pytest.mark.django_db
def test_memorial_tribute_detail_hides_shared_species_images(client):
    """A memorial or tribute never renders images attached only to its shared species."""

    memorial_tribute = create_memorial_tribute()
    image = get_image_model().objects.create(title="Shared species image", file=make_image_file())
    SpeciesImage.objects.create(
        species=memorial_tribute.species,
        image=image,
        caption="Wrong memorial_tribute image",
        sort_order=0,
    )

    response = client.get(memorial_tribute.get_absolute_url())

    assert response.status_code == 200
    assert "Wrong memorial_tribute image" not in response.content.decode()


@pytest.mark.django_db
def test_collection_detail_renders_its_own_plant_images(client, genus):
    """Ordinary plant collection pages render images owned by that collection."""

    species = get_species(genus, name="publica", full_name="Plantus publica")
    collection = Collection.objects.create(
        location=get_location(latitude=40.03, longitude=-111.03),
        garden=get_garden_area(code="PUB-IMAGES"),
        species=species,
        plant_id="PUB-IMAGE-1",
    )
    image = get_image_model().objects.create(title="Plant collection image", file=make_image_file())
    PlantImage.objects.create(
        collection=collection,
        image=image,
        caption="Plant image caption",
        sort_order=0,
    )

    response = client.get(collection.get_absolute_url())

    assert response.status_code == 200
    assert "Plant image caption" in response.content.decode()


@pytest.mark.django_db
def test_plant_images_are_ordered_and_deleted_with_their_collection(genus):
    """Collection-owned images retain order and do not outlive their collection."""

    species = get_species(genus, name="orderata", full_name="Plantus orderata")
    collection = Collection.objects.create(species=species, plant_id="PUB-IMAGE-ORDER")
    first_image = get_image_model().objects.create(title="First", file=make_image_file())
    second_image = get_image_model().objects.create(title="Second", file=make_image_file())
    later = PlantImage.objects.create(
        collection=collection,
        image=first_image,
        sort_order=2,
    )
    earlier = PlantImage.objects.create(
        collection=collection,
        image=second_image,
        sort_order=1,
    )

    assert list(collection.plant_images.values_list("pk", flat=True)) == [earlier.pk, later.pk]

    collection.delete()

    assert not PlantImage.objects.filter(pk__in=[earlier.pk, later.pk]).exists()


@pytest.mark.django_db
def test_memorial_tribute_map_and_geojson_are_scoped_to_memorials_and_tributes(client, genus):
    """Dedicated and public discovery endpoints keep their records separate."""

    memorial_tribute = create_memorial_tribute()
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

    map_response = client.get(reverse("plants:memorial-tribute-map"))
    assert map_response.status_code == 200
    map_content = map_response.content.decode()
    assert "Memorials and Tributes Map" in map_content
    assert "Filter visible memorials and tributes" in map_content
    assert "Select a memorial or tribute to open its detail page." in map_content
    assert map_response.context["filter"].form.fields["q"].label == "Search memorials and tributes"
    assert map_response.context["filter"].form.fields["q"].widget.attrs["placeholder"] == (
        "Name, garden, memorial, or tribute text"
    )
    assert ("Ada Lovelace", "Ada Lovelace") in map_response.context["filter"].form.fields[
        "commemoration_person"
    ].choices

    memorial_tribute_data = client.get(
        reverse("plants:api-memorials-and-tributes-geojson")
    ).json()
    public_data = client.get(reverse("plants:api-collections-geojson")).json()
    memorial_tribute_ids = {feature["properties"]["id"] for feature in memorial_tribute_data["features"]}
    public_ids = {feature["properties"]["id"] for feature in public_data["features"]}
    assert memorial_tribute_ids == {memorial_tribute.id}
    assert public_collection.id in public_ids
    assert memorial_tribute.id not in public_ids
    properties = memorial_tribute_data["features"][0]["properties"]
    assert set(properties) == {
        "id",
        "detail_url",
        "memorial_tribute_id",
        "honoree",
        "garden_name",
        "garden_area",
        "garden_code",
    }
    assert "species_id" not in properties
    assert "species_full_name" not in properties
    assert "plant_date" not in properties
    assert memorial_tribute.get_absolute_url() in map_response.content.decode()


@pytest.mark.django_db
def test_memorial_tribute_map_preloads_taxonomy_for_canonical_urls(client):
    """MemorialTribute map results preload taxonomy used by canonical URLs."""

    memorial_tribute = create_memorial_tribute()
    response = client.get(reverse("plants:memorial-tribute-map"))
    rendered_memorial_tribute = next(
        item
        for item in response.context["memorials_and_tributes"]
        if item.pk == memorial_tribute.pk
    )

    assert "genus" in rendered_memorial_tribute.species._state.fields_cache
    assert "family" in rendered_memorial_tribute.species.genus._state.fields_cache


@pytest.mark.django_db
@pytest.mark.parametrize(
    "query",
    [
        "Ada",
        "Children's Garden",
        "First line",
    ],
)
def test_memorial_tribute_map_searches_public_memorial_tribute_fields(client, query):
    """The memorial-or-tribute search matches only public discovery fields."""

    memorial_tribute = create_memorial_tribute()
    response = client.get(
        reverse("plants:api-memorials-and-tributes-geojson"), {"q": query}
    )

    assert response.status_code == 200
    assert [feature["properties"]["id"] for feature in response.json()["features"]] == [
        memorial_tribute.id
    ]


@pytest.mark.django_db
def test_memorial_tribute_search_rejects_queries_longer_than_200_characters():
    """Overlong public map searches are invalid and safely leave results unfiltered."""

    memorial_tribute = create_memorial_tribute()
    memorial_tribute_filter = MemorialTributeFilter(
        {"q": "a" * 201},
        queryset=Collection.objects.filter(pk=memorial_tribute.pk),
    )

    assert not memorial_tribute_filter.form.is_valid()
    assert memorial_tribute_filter.form.errors.as_data()["q"][0].code == "max_length"
    assert list(memorial_tribute_filter.qs) == [memorial_tribute]


@pytest.mark.django_db
def test_memorial_tribute_geojson_and_detail_handle_a_missing_garden(client):
    """Mapped memorials_and_tributes without a garden relation remain publicly renderable."""

    memorial_tribute = create_memorial_tribute()
    memorial_tribute.garden = None
    memorial_tribute.save(update_fields=["garden"])

    detail_response = client.get(memorial_tribute.get_absolute_url())
    geojson_response = client.get(
        reverse("plants:api-memorials-and-tributes-geojson")
    )

    assert detail_response.status_code == 200
    assert geojson_response.status_code == 200
    properties = geojson_response.json()["features"][0]["properties"]
    assert properties["garden_name"] is None
    assert properties["garden_area"] is None
    assert properties["garden_code"] is None


@pytest.mark.django_db
def test_sitemaps_keep_memorials_and_tributes_in_their_own_sections(genus):
    """Public sitemap inventory does not mix memorial-or-tribute and plant URLs."""

    memorial_tribute = create_memorial_tribute()
    species = get_species(genus, name="publica", full_name="Plantus publica")
    public_collection = Collection.objects.create(
        species=species,
        plant_id="PUB-SITEMAP-1",
    )

    collection_items = list(CollectionDetailSitemap().items())
    memorial_tribute_items = list(MemorialTributeDetailSitemap().items())
    species_items = list(SpeciesDetailSitemap().items())

    assert collection_items == [public_collection]
    assert memorial_tribute_items == [memorial_tribute]
    assert memorial_tribute.species not in species_items
    assert CollectionDetailSitemap().location(public_collection) == public_collection.get_absolute_url()
    assert MemorialTributeDetailSitemap().location(memorial_tribute) == memorial_tribute.get_absolute_url()


def test_sitemap_uses_the_memorials_and_tributes_section_name():
    """Expose the public sitemap section under the memorials-and-tributes URL."""

    from redbuttegarden.urls import SITEMAPS

    assert "memorials-and-tributes" in SITEMAPS
    assert "memorials_and_tributes" not in SITEMAPS


@pytest.mark.django_db
def test_bloom_feeds_exclude_memorial_tribute_events(genus):
    """General bloom feeds do not surface memorial-or-tribute records beside plants."""

    memorial_tribute = create_memorial_tribute()
    public_species = get_species(genus, name="publica", full_name="Plantus publica")
    public_event = BloomEvent.objects.create(title="Public bloom", species=public_species)
    memorial_tribute_event = BloomEvent.objects.create(
        title="MemorialTribute bloom", species=memorial_tribute.species
    )
    mixed_event = BloomEvent.objects.create(title="Mixed bloom")
    mixed_event.collections.add(memorial_tribute)

    assert list(GardenBloomFeed().items()) == [public_event]
    assert list(GardenBloomICalFeed().items()) == [public_event]
    assert memorial_tribute_event not in GardenBloomFeed().items()
    assert mixed_event not in GardenBloomICalFeed().items()


@pytest.mark.django_db
def test_internal_collection_api_remains_authenticated_while_memorial_tribute_map_is_public(client):
    """Dedicated public map data does not weaken the authenticated data API boundary."""

    create_memorial_tribute()

    assert APIClient().get(reverse("plants:api-collection-list")).status_code == 401
    assert client.get(
        reverse("plants:api-memorials-and-tributes-geojson")
    ).status_code == 200


@pytest.mark.django_db
def test_public_species_views_hide_memorial_tribute_pseudo_species(client):
    """Dedicataceae species are not available from public plant discovery URLs."""

    memorial_tribute = create_memorial_tribute()

    assert client.get(
        reverse("plants:species-detail", args=[memorial_tribute.species_id])
    ).status_code == 404
    assert client.get(
        reverse("plants:species-preview", args=[memorial_tribute.species_id])
    ).status_code == 404
