import pytest

from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from plants.models import Collection

@pytest.mark.django_db
class TestAPI:
    def __init__(self):
        user = self.user()
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
                "bee_friend": False
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
            "plant_date": "1-1-1111",
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
                "bee_friend": False
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
            "plant_date": "1-1-1111",
            "plant_id": "0001-0001*1",
            "commemoration_category": "Available",
            "commemoration_person": "Person Name"
        }
    ]

    return payloads

@pytest.mark.django_db
def test_collection_creation_api_two_cultivars(collections_same_species_different_cultivars):
    api_client = TestAPI()

    collection_one_payload = collections_same_species_different_cultivars[0]
    collection_two_payload = collections_same_species_different_cultivars[1]

    api_client.auth_user.post('/plants/api/collections/', collection_one_payload, format='json')
    api_client.auth_user.post('/plants/api/collections/', collection_two_payload, format='json')

    assert Collection.objects.all().count() == 2
