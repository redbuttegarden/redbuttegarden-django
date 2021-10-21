from urllib.parse import urlencode

import json
from django.test import TestCase
from django.urls import reverse

from plants.tests.utils import get_collection


class PlantSearchViewTestCase(TestCase):
    def test_collection_search_by_garden_area(self):
        get_collection(ga_name='Garden One')
        params = {'garden_name': 'Garden One'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 1)
        self.assertEqual(json_response['features'][0]['properties']['garden_name'], 'Garden One')

        # Make another collection with same garden name. Other values arbitrary
        get_collection(latitude=41, longitude=-112, family_name='Two', genus_name='two', ga_name='Garden One',
                       code='unique', plant_id='2')

        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 2)
        self.assertEqual(json_response['features'][0]['properties']['garden_name'], 'Garden One')
        self.assertEqual(json_response['features'][1]['properties']['garden_name'], 'Garden One')
