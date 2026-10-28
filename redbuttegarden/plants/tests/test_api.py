from copy import deepcopy
from io import BytesIO
import json
from unittest.mock import patch

import pytest

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.db import DatabaseError
from django.urls import reverse
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from wagtail.models import Collection as WagtailCollection

from plants.models import Collection, PlantImage
from plants.tests.utils import get_collection


@pytest.mark.django_db
class APITestSetup:
    def __init__(self):
        user = self.user()

        # Create wagtail collection used during image upload view
        root_coll = WagtailCollection.get_first_root_node()
        if root_coll is None:
            root_coll = WagtailCollection.add_root(name="Root")
        root_coll.add_child(name='BRAHMS Data')

        self.auth_user = self.authenticated_client(user)

    def user(self):
        user = get_user_model().objects.create(username='username', password='password')
        return user

    def authenticated_client(self, user):
        token = Token.objects.create(user=user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return client


@pytest.fixture
def species_api_collections():
    """Create collections used to exercise species-list filtering."""
    matching_collection = get_collection(
        plant_id="LC-1001",
        family_name="Matched Family",
        genus_name="MatchedGenus",
        species_name="matched",
        full_name="MatchedGenus matched",
    )
    get_collection(
        plant_id="LC-1002",
        family_name="Matched Family",
        genus_name="MatchedGenus",
        species_name="matched",
        full_name="MatchedGenus matched",
    )
    other_collection = get_collection(
        plant_id="LC-2001",
        family_name="Other Family",
        genus_name="OtherGenus",
        species_name="other",
        full_name="OtherGenus other",
    )
    return matching_collection, other_collection


@pytest.mark.django_db
def test_species_list_filters_by_exact_plant_id(species_api_collections):
    """A known living-collection ID returns its linked species once."""
    matching_collection, _ = species_api_collections
    api_client = APITestSetup()

    response = api_client.auth_user.get(
        "/plants/api/species/", {"plant_id": matching_collection.plant_id}
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert [result["id"] for result in response.data["results"]] == [
        matching_collection.species_id
    ]


@pytest.mark.django_db
def test_species_list_plant_id_returns_no_results_for_unknown_or_partial_id(
    species_api_collections,
):
    """Plant ID lookup is exact and unknown values return an empty page."""
    matching_collection, _ = species_api_collections
    api_client = APITestSetup()

    for plant_id in ("LC-9999", matching_collection.plant_id[:-1]):
        response = api_client.auth_user.get("/plants/api/species/", {"plant_id": plant_id})

        assert response.status_code == 200
        assert response.data["count"] == 0
        assert response.data["results"] == []


@pytest.mark.django_db
def test_species_list_plant_id_deduplicates_species_with_multiple_collections(
    species_api_collections,
):
    """A species with multiple collections is serialized only once."""
    matching_collection, _ = species_api_collections
    api_client = APITestSetup()

    response = api_client.auth_user.get(
        "/plants/api/species/", {"plant_id": matching_collection.plant_id}
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert len(response.data["results"]) == 1


@pytest.mark.django_db
def test_species_list_taxonomy_lookup_remains_unchanged(species_api_collections):
    """Existing taxonomy filtering continues to return matching species."""
    matching_collection, _ = species_api_collections
    api_client = APITestSetup()

    response = api_client.auth_user.get(
        "/plants/api/species/", {"genus": matching_collection.species.genus.name}
    )

    assert response.status_code == 200
    assert response.data["count"] == 1
    assert response.data["results"][0]["id"] == matching_collection.species_id


@pytest.mark.django_db
def test_species_list_plant_id_and_taxonomy_filters_use_and_semantics(
    species_api_collections,
):
    """Contradictory plant ID and taxonomy filters produce no results."""
    matching_collection, other_collection = species_api_collections
    api_client = APITestSetup()

    response = api_client.auth_user.get(
        "/plants/api/species/",
        {
            "plant_id": matching_collection.plant_id,
            "genus": other_collection.species.genus.name,
        },
    )

    assert response.status_code == 200
    assert response.data["count"] == 0
    assert response.data["results"] == []


@pytest.fixture
def collections_same_species_different_cultivars():
    payloads = [
        {
            "species": {
                "genus": {
                    "family": {
                        "name": "Family",
                        "vernacular_name": "Family Name"
                    },
                    "name": "Genus"
                },
                "name": "species",
                "full_name": "Genus species",
                "subspecies": "",
                "variety": "",
                "subvariety": "",
                "forma": "",
                "subforma": "",
                "cultivar": "cultivar-one",
                "vernacular_name": "Cultivar One Name",
                "habit": "Habit",
                "hardiness": None,
                "water_regime": None,
                "exposure": None,
                "bloom_time": None,
                "plant_size": None,
                "flower_color": None,
                "label_range_text": None,
                "utah_native": False,
                "plant_select": False,
                "deer_resist": False,
                "rabbit_resist": False,
                "bee_friend": False,
                "high_elevation": False,
                "arborist_rec": False
            },
            "garden": {
                "area": "Garden Area",
                "name": "Garden Name",
                "code": "Garden-Code"
            },
            "location": {
                "latitude": 40.766367,
                "longitude": -111.823807,
            },
            "plant_date": "1111-1-1",
            "plant_id": "0001-0001*1",
            "commemoration_category": "Available",
            "commemoration_person": "Person Name"
        },
        {
            "species": {
                "genus": {
                    "family": {
                        "name": "Family",
                        "vernacular_name": "Family Name"
                    },
                    "name": "Genus"
                },
                "name": "species",
                "full_name": "Genus species",
                "subspecies": "",
                "variety": "",
                "subvariety": "",
                "forma": "",
                "subforma": "",
                "cultivar": "cultivar-two",
                "vernacular_name": "Cultivar Two Name",
                "habit": "Habit",
                "hardiness": None,
                "water_regime": None,
                "exposure": None,
                "bloom_time": None,
                "plant_size": None,
                "flower_color": None,
                "label_range_text": None,
                "utah_native": False,
                "plant_select": False,
                "deer_resist": False,
                "rabbit_resist": False,
                "bee_friend": False,
                "high_elevation": False,
                "arborist_rec": False
            },
            "garden": {
                "area": "Garden Area",
                "name": "Garden Name",
                "code": "Garden-Code"
            },
            "location": {
                "latitude": 40.766367,
                "longitude": -111.823807,
            },
            "plant_date": "1111-1-1",
            "plant_id": "0001-0001*1",
            "commemoration_category": "Available",
            "commemoration_person": "Person Name"
        }
    ]

    return payloads


@pytest.mark.django_db
def test_collection_creation_api_two_cultivars(collections_same_species_different_cultivars):
    """
    Attempt to post collection with same plant_id should not create another collection
    """
    api_client = APITestSetup()

    collection_one_payload = collections_same_species_different_cultivars[0]
    collection_two_payload = collections_same_species_different_cultivars[1]

    api_client.auth_user.post('/plants/api/collections/', collection_one_payload, format='json')
    api_client.auth_user.post('/plants/api/collections/', collection_two_payload, format='json')

    assert Collection.objects.all().count() == 1


@pytest.mark.django_db
def test_collection_commemoration_text_api(
    collections_same_species_different_cultivars,
):
    """Collection upserts persist optional multiline commemoration text."""
    api_client = APITestSetup()
    create_payload = deepcopy(collections_same_species_different_cultivars[0])
    create_payload["commemoration_text"] = "In memory of Ada Lovelace\nA lasting gift"

    response = api_client.auth_user.post(
        "/plants/api/collections/", create_payload, format="json"
    )

    assert response.status_code == 201
    assert response.data["commemoration_text"] == "In memory of Ada Lovelace\nA lasting gift"
    collection = Collection.objects.get(plant_id=create_payload["plant_id"])
    assert collection.commemoration_text == "In memory of Ada Lovelace\nA lasting gift"
    assert collection.commemoration_category == "Available"
    assert collection.commemoration_person == "Person Name"

    update_payload = deepcopy(create_payload)
    update_payload["commemoration_text"] = "Dedicated to Ada\nWith gratitude"
    response = api_client.auth_user.post(
        "/plants/api/collections/", update_payload, format="json"
    )

    assert response.status_code == 201
    collection.refresh_from_db()
    assert collection.commemoration_text == "Dedicated to Ada\nWith gratitude"
    assert collection.commemoration_category == "Available"
    assert collection.commemoration_person == "Person Name"


@pytest.mark.django_db
def test_collection_commemoration_text_is_optional(
    collections_same_species_different_cultivars,
):
    """Legacy collection payloads without commemoration text remain valid."""
    api_client = APITestSetup()
    payload = deepcopy(collections_same_species_different_cultivars[0])
    payload["plant_id"] = "0001-0002*1"

    response = api_client.auth_user.post(
        "/plants/api/collections/", payload, format="json"
    )

    assert response.status_code == 201
    assert response.data["commemoration_text"] is None
    collection = Collection.objects.get(plant_id=payload["plant_id"])
    assert collection.commemoration_text is None
    assert collection.commemoration_category == "Available"
    assert collection.commemoration_person == "Person Name"


@pytest.mark.django_db
def test_species_image_setting(species):
    api_client = APITestSetup()

    img_one_file_obj = BytesIO()
    img_two_file_obj = BytesIO()
    image_one = Image.new('RGB', size=(1, 1), color=(256, 0, 0))
    image_two = Image.new('RGB', size=(1, 1), color=(256, 0, 0))
    image_one.save(img_one_file_obj, 'jpeg')
    image_two.save(img_two_file_obj, 'jpeg')
    img_one_file_obj.seek(0)
    img_two_file_obj.seek(0)
    img_one = ImageFile(img_one_file_obj, name='1.jpg')
    img_two = ImageFile(img_two_file_obj, name='2.jpg')

    resp = api_client.auth_user.post(f'/plants/api/species/{species.pk}/set-image/', {'image': img_one})
    assert resp.status_code == 200

    assert species.species_images.all().count() == 1

    resp = api_client.auth_user.post(f'/plants/api/species/{species.pk}/set-image/', {'image': img_two})
    assert resp.status_code == 200

    assert species.species_images.all().count() == 2


@pytest.mark.django_db
def test_plant_image_setting_uses_exact_dedication_plant_id():
    """The plant-image endpoint attaches an upload to one dedication only."""
    api_client = APITestSetup()
    first_dedication = get_collection(
        plant_id="2026-0295*70",
        family_name="Dedicataceae",
        genus_name="Dedica",
        species_name="bench",
        full_name="Dedica bench",
    )
    second_dedication = get_collection(
        plant_id="2026-0295*71",
        family_name="Dedicataceae",
        genus_name="Dedica",
        species_name="bench",
        full_name="Dedica bench",
    )
    image_file_obj = BytesIO()
    Image.new("RGB", size=(1, 1), color=(256, 0, 0)).save(image_file_obj, "jpeg")
    image_file_obj.seek(0)

    response = api_client.auth_user.post(
        reverse("plants:api-set-plant-image", kwargs={"plant_id": first_dedication.plant_id}),
        {"image": ImageFile(image_file_obj, name="dedication.jpg")},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert first_dedication.plant_images.count() == 1
    assert second_dedication.plant_images.count() == 0
    assert PlantImage.objects.get(collection=first_dedication).image.tags.filter(
        name="BRAHMS"
    ).exists()


@pytest.mark.django_db
def test_plant_image_setting_supports_non_dedication_collections():
    """The plant-image endpoint accepts ordinary living-collection records."""
    api_client = APITestSetup()
    collection = get_collection(plant_id="2026-0400*1", family_name="Rosaceae")
    image_file_obj = BytesIO()
    Image.new("RGB", size=(1, 1), color=(256, 0, 0)).save(image_file_obj, "jpeg")
    image_file_obj.seek(0)

    response = api_client.auth_user.post(
        reverse("plants:api-set-plant-image", kwargs={"plant_id": collection.plant_id}),
        {"image": ImageFile(image_file_obj, name="plant.jpg")},
    )

    assert response.status_code == 200
    assert response.json()["plant_image_created"] is True
    assert collection.plant_images.count() == 1


@pytest.mark.django_db
def test_plant_image_setting_rejects_unknown_ids_missing_images_and_unauthenticated_requests():
    """Invalid plant-image uploads do not create collection image relationships."""
    api_client = APITestSetup()
    collection = get_collection(plant_id="2026-0400*2")
    endpoint = reverse("plants:api-set-plant-image", kwargs={"plant_id": collection.plant_id})

    missing_image_response = api_client.auth_user.post(endpoint, {})
    unknown_id_response = api_client.auth_user.post(
        reverse("plants:api-set-plant-image", kwargs={"plant_id": "unknown"}), {}
    )
    unauthenticated_response = APIClient().post(endpoint, {})

    assert missing_image_response.status_code == 400
    assert unknown_id_response.status_code == 404
    assert unauthenticated_response.status_code in (200, 401, 403)
    if unauthenticated_response.status_code == 200:
        assert unauthenticated_response.json()["status"] == "failure"
    assert collection.plant_images.count() == 0


def _bulk_upload(name):
    """Build a minimal JPEG upload for multipart bulk image requests."""

    file_obj = BytesIO()
    Image.new("RGB", size=(1, 1), color=(255, 0, 0)).save(file_obj, "jpeg")
    file_obj.seek(0)
    return ImageFile(file_obj, name=name)


def _species_target(species):
    """Return the exact taxonomy manifest target for a species."""

    return {
        "genus": species.genus.name,
        "name": species.name,
        "subspecies": species.subspecies,
        "variety": species.variety,
        "subvariety": species.subvariety,
        "forma": species.forma,
        "subforma": species.subforma,
        "cultivar": species.cultivar,
    }


@pytest.mark.django_db
def test_bulk_collections_create_update_and_isolate_invalid_records(
    collections_same_species_different_cultivars,
):
    """Bulk collection records retain the single-record upsert semantics."""
    api_client = APITestSetup()
    first = deepcopy(collections_same_species_different_cultivars[0])
    second = deepcopy(collections_same_species_different_cultivars[1])
    second["plant_id"] = "bulk-2"
    invalid = {"plant_id": "missing-nested-data"}

    response = api_client.auth_user.post(
        reverse("plants:api-collections-bulk"),
        {"collections": [first, invalid, second]},
        format="json",
    )

    assert response.status_code == 200
    assert [item["status"] for item in response.data["results"]] == [
        "success", "error", "success"
    ]
    assert Collection.objects.filter(plant_id=first["plant_id"]).count() == 1
    assert Collection.objects.filter(plant_id=second["plant_id"]).count() == 1

    first["commemoration_person"] = "Updated Person"
    retry = api_client.auth_user.post(
        reverse("plants:api-collections-bulk"), {"collections": [first]}, format="json"
    )
    assert retry.data["results"][0]["created"] is False
    assert Collection.objects.get(plant_id=first["plant_id"]).commemoration_person == "Updated Person"


@pytest.mark.django_db
def test_bulk_collections_rejects_invalid_envelopes_and_batch_sizes(
    collections_same_species_different_cultivars,
):
    """Collection batch limits are enforced before any records are processed."""
    api_client = APITestSetup()
    endpoint = reverse("plants:api-collections-bulk")
    assert api_client.auth_user.post(endpoint, {}, format="json").status_code == 400
    payload = collections_same_species_different_cultivars[0]
    response = api_client.auth_user.post(
        endpoint, {"collections": [payload] * 101}, format="json"
    )
    assert response.status_code == 400
    assert Collection.objects.count() == 0


@pytest.mark.django_db
def test_bulk_images_supports_plant_and_species_targets_and_retries():
    """Both bulk target kinds retain BRAHMS association idempotency."""
    api_client = APITestSetup()
    plant = get_collection(plant_id="bulk-plant")
    endpoint = reverse("plants:api-images-bulk")
    manifest = [
        {
            "client_id": "plant",
            "file_field": "plant_file",
            "copyright_info": "RBG",
            "plant_id": plant.plant_id,
        },
        {
            "client_id": "species",
            "file_field": "species_file",
            "copyright_info": "RBG",
            "species": _species_target(plant.species),
        },
    ]
    response = api_client.auth_user.post(
        endpoint,
        {"manifest": json.dumps(manifest), "plant_file": _bulk_upload("bulk-plant.jpg"), "species_file": _bulk_upload("bulk-species.jpg")},
    )
    assert response.status_code == 200
    assert response.json()["results"] == [
        {"client_id": "plant", "status": "success", "created": True},
        {"client_id": "species", "status": "success", "created": True},
    ]
    assert plant.plant_images.count() == 1
    assert plant.species.species_images.count() == 1

    retry_manifest = [
        {
            "client_id": "retry",
            "file_field": "plant_file",
            "copyright_info": "RBG",
            "plant_id": plant.plant_id,
        }
    ]
    retry = api_client.auth_user.post(
        endpoint, {"manifest": json.dumps(retry_manifest), "plant_file": _bulk_upload("bulk-plant.jpg")}
    )
    assert retry.json()["results"][0]["created"] is False
    assert plant.plant_images.count() == 1


@pytest.mark.django_db
def test_bulk_images_returns_independent_target_and_file_errors():
    """A bad manifest item does not prevent a later valid image upload."""
    api_client = APITestSetup()
    plant = get_collection(plant_id="bulk-errors")
    endpoint = reverse("plants:api-images-bulk")
    ambiguous = get_collection(
        plant_id="bulk-ambiguous", family_name="Other", genus_name=plant.species.genus.name,
        species_name=plant.species.name, full_name="Other same species", cultivar=plant.species.cultivar,
    )
    assert ambiguous.species_id != plant.species_id
    manifest = [
        {"client_id": "missing", "file_field": "not_sent", "copyright_info": "", "plant_id": plant.plant_id},
        {"client_id": "unknown", "file_field": "known", "copyright_info": "", "plant_id": "nope"},
        {"client_id": "not-found", "file_field": "known", "copyright_info": "", "species": {**_species_target(plant.species), "name": "not-here"}},
        {"client_id": "ambiguous", "file_field": "known", "copyright_info": "", "species": _species_target(plant.species)},
        {"client_id": "bad-target", "file_field": "known", "copyright_info": "", "plant_id": plant.plant_id, "species": _species_target(plant.species)},
        {"client_id": "valid", "file_field": "known", "copyright_info": "", "plant_id": plant.plant_id},
    ]
    response = api_client.auth_user.post(
        endpoint, {"manifest": json.dumps(manifest), "known": _bulk_upload("valid.jpg")}
    )
    assert response.status_code == 200
    assert [item["code"] if item["status"] == "error" else "success" for item in response.json()["results"]] == [
        "missing_file", "plant_not_found", "species_not_found", "species_ambiguous", "invalid_target", "success"
    ]
    assert plant.plant_images.count() == 1


@pytest.mark.django_db
def test_bulk_images_rejects_invalid_manifest_and_batch_size():
    """Only malformed or oversized manifest envelopes receive HTTP 400."""
    api_client = APITestSetup()
    endpoint = reverse("plants:api-images-bulk")
    assert api_client.auth_user.post(endpoint, {"manifest": "not-json"}).status_code == 400
    response = api_client.auth_user.post(endpoint, {"manifest": json.dumps([{}] * 21)})
    assert response.status_code == 400


@pytest.mark.django_db
def test_bulk_images_returns_database_errors_per_item():
    """A database failure is reported without changing the valid envelope status."""
    api_client = APITestSetup()
    plant = get_collection(plant_id="bulk-database-error")
    manifest = [
        {
            "client_id": "database-error",
            "file_field": "image",
            "copyright_info": "",
            "plant_id": plant.plant_id,
        }
    ]

    with patch(
        "plants.views.create_brahms_image_association", side_effect=DatabaseError()
    ):
        response = api_client.auth_user.post(
            reverse("plants:api-images-bulk"),
            {"manifest": json.dumps(manifest), "image": _bulk_upload("failure.jpg")},
        )

    assert response.status_code == 200
    assert response.json()["results"] == [
        {
            "client_id": "database-error",
            "status": "error",
            "code": "database_error",
            "detail": "The image association could not be saved.",
        }
    ]
