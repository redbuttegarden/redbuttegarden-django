from copy import deepcopy
from io import BytesIO

import pytest

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
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
