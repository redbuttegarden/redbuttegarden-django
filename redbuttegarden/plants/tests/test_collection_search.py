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

    def test_collection_search_by_bloom_time(self):
        get_collection(plant_id='1', bloom_time=['January'])
        get_collection(plant_id='2', bloom_time=['Early January'], latitude=41, longitude=-112,
                       family_name='2', genus_name='2', code='2')
        get_collection(plant_id='3', bloom_time=['Late January'], latitude=42, longitude=-113,
                       family_name='3', genus_name='3', code='3')
        get_collection(plant_id='4', bloom_time=['Late February'], latitude=43, longitude=-114,
                       family_name='4', genus_name='4', code='4')
        get_collection(plant_id='5', bloom_time=['March', 'Mid April'], latitude=44, longitude=-115,
                       family_name='5', genus_name='5', code='5')
        get_collection(plant_id='6', bloom_time=['Late March', 'Early April', 'May'], latitude=45,
                       longitude=-116, family_name='6', genus_name='6', code='6')

        params = {'bloom_months': 'January'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 3)
        self.assertEqual(json_response['features'][0]['properties']['bloom_time'], ['Late January'])
        self.assertEqual(json_response['features'][1]['properties']['bloom_time'], ['Early January'])
        self.assertEqual(json_response['features'][2]['properties']['bloom_time'], ['January'])

        params = {'bloom_months': 'April'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 2)
        self.assertEqual(json_response['features'][0]['properties']['bloom_time'], ['Late March', 'Early April', 'May'])
        self.assertEqual(json_response['features'][1]['properties']['bloom_time'], ['March', 'Mid April'])
