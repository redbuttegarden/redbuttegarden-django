from io import BytesIO

import pytest

from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from wagtail.core.models import Collection as WagtailCollection

from plants.models import Collection
from .utils import family, genus, species


@pytest.mark.django_db
class TestAPI:
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
                "utah_native": False,
                "plant_select": False,
                "deer_resist": False,
                "rabbit_resist": False,
                "bee_friend": False,
                "high_elevation": False,
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
                "utah_native": False,
                "plant_select": False,
                "deer_resist": False,
                "rabbit_resist": False,
                "bee_friend": False,
                "high_elevation": False,
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
    api_client = TestAPI()

    collection_one_payload = collections_same_species_different_cultivars[0]
    collection_two_payload = collections_same_species_different_cultivars[1]

    api_client.auth_user.post('/plants/api/collections/', collection_one_payload, format='json')
    api_client.auth_user.post('/plants/api/collections/', collection_two_payload, format='json')

    assert Collection.objects.all().count() == 1

@pytest.mark.django_db
def test_species_image_setting(species):
    api_client = TestAPI()

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
