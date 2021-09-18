from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from rest_framework.test import APITransactionTestCase

from plants.models import Species

class SpeciesAPITest(APITransactionTestCase):
    def setUp(self) -> None:
        self.example_payloads = [
            {'species': {'genus': {'family': {'name': 'Geraniaceae', 'vernacular_name': 'Geranium'}, 'name': 'Geranium'}, 'name': '', 'cultivar': "Johnson's Blue", 'vernacular_name': "Johnson's Blue Geranium", 'habit': 'Perennial', 'hardiness': [4, 5, 6, 7, 8], 'water_regime': 'Average', 'exposure': 'Full Sun to Part Shade', 'bloom_time': ['May', 'June', 'July'], 'plant_size': '12"h x 24"w', 'flower_color': 'Purple, Blue', 'utah_native': False, 'plant_select': False, 'deer_resist': True, 'rabbit_resist': True, 'bee_friend': False}, 'garden': {'area': 'Lower Pond', 'name': 'Water Pavilion Garden', 'code': 'WP-01'}, 'location': {'latitude': 40.766775, 'longitude': -111.825342}, 'plant_date': '19-5-2005', 'plant_id': '2003-0085*1', 'commemoration_category': '', 'commemoration_person': ''},
            {'species': {'genus': {'family': {'name': 'Geraniaceae', 'vernacular_name': 'Geranium'}, 'name': 'Geranium'}, 'name': '', 'cultivar': "Johnson's Red", 'vernacular_name': "Johnson's Red Geranium", 'habit': 'Perennial', 'hardiness': [4, 5, 6, 7, 8], 'water_regime': 'Average', 'exposure': 'Full Sun to Part Shade', 'bloom_time': ['May', 'June', 'July'], 'plant_size': '12"h x 24"w', 'flower_color': 'Purple, Blue', 'utah_native': False, 'plant_select': False, 'deer_resist': True, 'rabbit_resist': True, 'bee_friend': False}, 'garden': {'area': 'Lower Pond', 'name': 'Water Pavilion Garden', 'code': 'WP-01'}, 'location': {'latitude': 40.766775, 'longitude': -111.825342}, 'plant_date': '19-5-2005', 'plant_id': '2003-0086*1', 'commemoration_category': '', 'commemoration_person': ''}
        ]
        self.user = get_user_model().objects.create_user(
            username='test', email='test@email.com', password='secret'
        )
        self.token, created = Token.objects.get_or_create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_multiple_species_with_empty_string_names_can_be_created(self):
        """Multiple species with empty string names but with different cultivar names should be considered unique"""
        request_one = self.client.post('/plants/api/collections/', self.example_payloads[0], format='json')
        request_two = self.client.post('/plants/api/collections/', self.example_payloads[1], format='json')
        assert Species.objects.count() == 2

