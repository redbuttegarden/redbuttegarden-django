from urllib.parse import urlencode

import json
from django.test import TestCase
from django.urls import reverse

from plants.models import Collection
from plants.tests.utils import get_collection


class PlantSearchViewTestCase(TestCase):
    def test_collection_search_by_scientific_name(self):
        """
        Search by scientific name should filter collections by species full name.
        """
        get_collection(plant_id='1', family_name='1', genus_name='Geranium',
                       full_name="Geranium 'Johnson's Blue'", cultivar="Johnson's Blue")
        get_collection(plant_id='2', family_name='2',
                       genus_name='Cercis', species_name='canadensis',
                       full_name='Cercis canadensis')
        get_collection(plant_id='3', family_name='3',
                       genus_name='Cytisus', species_name='praecox',
                       full_name="Cytisus × praecox 'Allgold'")
        get_collection(plant_id='4', family_name='Rosaceae',
                       genus_name='Crataegus', species_name='crus-galli', variety='inermis',
                       full_name="Crataegus crus-galli var. inermis")
        get_collection(plant_id='5', family_name='Rosaceae', genus_name='Crataegus',
                       species_name='crus-galli', variety='inermis',
                       full_name="Crataegus crus-galli var. inermis")
        get_collection(plant_id='6', family_name='5', genus_name='Hydrangea',
                       species_name='anomala', subspecies='petiolaris',
                       full_name="Hydrangea anomala subsp. petiolaris")
        get_collection(plant_id='7', family_name='Rosaceae', genus_name='Rosa',
                       species_name='sericea', subspecies='omeiensis', forma='pteracantha',
                       full_name='Rosa sericea subsp. omeiensis f. pteracantha')

        params = {'scientific_name': 'Geranium'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 1)
        self.assertEqual(json_response['features'][0]['properties']['species_full_name'], "Geranium 'Johnson's Blue'")

        params = {'scientific_name': 'Allgold'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 1)
        self.assertEqual(json_response['features'][0]['properties']['species_full_name'], "Cytisus × praecox 'Allgold'")

        params = {'scientific_name': 'inermis'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 2)
        self.assertEqual(json_response['features'][0]['properties']['species_full_name'],
                         "Crataegus crus-galli var. inermis")

        params = {'scientific_name': 'subsp. petiolaris'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 1)
        self.assertEqual(json_response['features'][0]['properties']['species_full_name'],
                         "Hydrangea anomala subsp. petiolaris")


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

    def test_collection_search_by_flower_color(self):
        get_collection(plant_id='1', family_name='1', genus_name='1', flower_color='Purple, Blue')
        get_collection(plant_id='2', family_name='2', genus_name='2', flower_color='Purple, Red')

        params = {'flower_colors': 'Purple'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 2)
        feature_one_id = json_response['features'][0]['properties']['id']
        feature_two_id = json_response['features'][1]['properties']['id']
        self.assertEqual(Collection.objects.get(id=feature_one_id).species.flower_color, 'Purple, Red')
        self.assertEqual(Collection.objects.get(id=feature_two_id).species.flower_color, 'Purple, Blue')

    def test_collection_search_by_scientific_name_and_vernacular_name(self):
        get_collection(plant_id='1', family_name='Grossulariaceae', genus_name='Ribes', species_name='rubrum',
                       cultivar='Red Lake', full_name="Ribes rubrum 'Red Lake'", vernacular_name='Red Lake Currant')
        get_collection(plant_id='2', family_name='Grossulariaceae', genus_name='Ribes', species_name='rubrum',
                       cultivar='Red Lake', full_name="Ribes rubrum 'Red Lake'", vernacular_name='Red Lake Currant')
        get_collection(plant_id='3', family_name='Pinaceae', genus_name='Pinus', species_name='resinosa',
                       cultivar='Don Smith', full_name="Pinus resinosa 'Don Smith'",
                       vernacular_name='Don Smith Red Pine')

        params = {'scientific_name': 'Ribes rubrum',
                  'common_name': 'Red'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 2)
        self.assertEqual(json_response['features'][0]['properties']['species_full_name'], "Ribes rubrum 'Red Lake'")
        self.assertEqual(json_response['features'][1]['properties']['species_full_name'], "Ribes rubrum 'Red Lake'")

    def test_collection_search_by_commemoration_person(self):
        get_collection(commemoration_person='Test Name')

        params = {'memorial_person': 'Test Name'}
        url = reverse('plants:plant-map') + '?' + urlencode(params)
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        json_response = json.loads(response.json())
        self.assertEqual(len(json_response['features']), 1)
