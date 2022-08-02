from io import BytesIO

from django.contrib.auth.models import Group
from django.core.files.images import ImageFile
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import RequestsClient, APILiveServerTestCase
from wagtail.core.models import Collection as WagtailCollection

from plants.models import SpeciesImage, Collection
from .utils import get_custom_user, get_family, get_genus, get_species


class TestSingleImageAPIFromExternalPerspective(APILiveServerTestCase):
    def setUp(self) -> None:
        self.user = get_custom_user(username='username', password='password')
        Token.objects.create(user=self.user)
        self.client = RequestsClient()

        api_group = Group.objects.create(name="API")

        self.user.groups.add(api_group)

        # Create wagtail collection used during image upload view
        root_coll = WagtailCollection.get_first_root_node()
        root_coll.add_child(name='BRAHMS Data')

        self.family = get_family()
        self.genus = get_genus(self.family)
        self.species = get_species(self.genus)

        token_url = self.live_server_url + reverse('plants:api-token')
        response = self.client.post(token_url, data={'username': 'username', 'password': 'password'})
        token = {'drf_token': response.json()['token']}
        self.client.headers.update({
            'Accept': 'application/json; q=1.0, */*',
            'Authorization': 'Token ' + token['drf_token']
        })

        self.img_file_obj = BytesIO()

        image_one = Image.new('RGB', size=(1, 1), color=(256, 0, 0))
        image_one.save(self.img_file_obj, 'jpeg')
        self.img_file_obj.seek(0)
        self.img_one = ImageFile(self.img_file_obj, name='1.jpg')

    def tearDown(self) -> None:
        self.img_file_obj.close()


    def test_posting_species_image(self):
        url = self.live_server_url + reverse('plants:api-set-species-image', kwargs={'pk': self.species.pk})

        test_copyright_info = 'Example Copyright Info'

        self.assertRaises(SpeciesImage.DoesNotExist, SpeciesImage.objects.get, species=self.species)

        r = self.client.post(url, data={'copyright_info': test_copyright_info}, files={'image': self.img_one})
        self.assertTrue(status.is_success(r.status_code))

        species_image = SpeciesImage.objects.get(species=self.species)
        self.assertEqual(species_image.copyright, test_copyright_info)


class TestCollectionsAPIFromExternalPerspective(APILiveServerTestCase):
    """
    Separating from above class since these tests seemed to make the
    image related ones fail for reasons that remain unclear to me.
    """
    def setUp(self) -> None:
        self.user = get_custom_user(username='username', password='password')
        Token.objects.create(user=self.user)
        self.client = RequestsClient()

        api_group = Group.objects.create(name="API")

        self.user.groups.add(api_group)

        self.family = get_family()
        self.genus = get_genus(self.family)
        self.species = get_species(self.genus)

        token_url = self.live_server_url + reverse('plants:api-token')
        response = self.client.post(token_url, data={'username': 'username', 'password': 'password'})
        token = {'drf_token': response.json()['token']}
        self.client.headers.update({
            'Accept': 'application/json; q=1.0, */*',
            'Authorization': 'Token ' + token['drf_token']
        })

    def test_posting_multiple_collections_same_species(self):
        url = self.live_server_url + reverse('plants:api-collection-list')
        payloads = [
            {'species': {
                'genus': {
                    'family': {
                        'name': 'Cactaceae',
                        'vernacular_name': 'Cactus'
                    },
                    'name': 'Opuntia'
                },
                'name': 'polyacantha',
                'full_name': 'Opuntia polyacantha',
                'subspecies': '',
                'variety': '',
                'subvariety': '',
                'forma': '',
                'subforma': '',
                'cultivar': '',
                'vernacular_name': 'Plains Pricklypear',
                'habit': 'Succulent',
                'hardiness': [7, 8, 9, 10],
                'water_regime': 'Very Low',
                'exposure': 'Full Sun',
                'bloom_time': ['May', 'June'],
                'plant_size': '8" h x 36" w',
                'flower_color': 'Yellow, Pink, Orange, Red, Magenta',
                'utah_native': True,
                'plant_select': False,
                'deer_resist': True,
                'rabbit_resist': True,
                'bee_friend': True,
                'high_elevation': False
            },
                'garden': {
                    'area': 'Sprout House',
                    'name': "Children's Garden",
                    'code': 'CG-25'
                },
                'location': {
                    'latitude': 40.7666,
                    'longitude': -111.823326
            },
                'plant_date': '2009-5-19',
                'plant_id': '2010-0428*1',
                'commemoration_category': '',
                'commemoration_person': ''
            },

            {'species':
                 {'genus': {
                     'family': {
                         'name': 'Cactaceae',
                         'vernacular_name': 'Cactus'
                     },
                     'name': 'Opuntia'
                 },
                     'name': 'polyacantha',
                     'full_name': 'Opuntia polyacantha var. trichophora',
                     'subspecies': '',
                     'variety': 'trichophora',
                     'subvariety': '',
                     'forma': '',
                     'subforma': '',
                     'cultivar': '',
                     'vernacular_name': 'Threadspine Pricklypear',
                     'habit': 'Succulent',
                     'hardiness': [7, 8, 9, 10, 11],
                     'water_regime': 'Very Low',
                     'exposure': 'Full Sun',
                     'bloom_time': [],
                     'plant_size': '15"h x 3\'w',
                     'flower_color': 'Yellow',
                     'utah_native': True,
                     'plant_select': False,
                     'deer_resist': True,
                     'rabbit_resist': True,
                     'bee_friend': True,
                     'high_elevation': False
                 },
                'garden': {
                    'area': 'Adaptive Beauty',
                    'name': 'Water Conservation Garden',
                    'code': 'WCG-09'
                },
                'location': {
                    'latitude': 40.767433,
                    'longitude': -111.823954
                },
                'plant_date': '2016-1-10',
                'plant_id': '2015-0308*3',
                'commemoration_category': '',
                'commemoration_person': ''
            },
        ]

        self.assertEqual(Collection.objects.all().count(), 0)

        first_response = self.client.post(url, json=payloads[0])
        self.assertTrue(status.is_success(first_response.status_code))

        self.assertEqual(Collection.objects.all().count(), 1)

        second_response = self.client.post(url, json=payloads[1])
        self.assertTrue(status.is_success(second_response.status_code))

        self.assertEqual(Collection.objects.all().count(), 2)

    def test_posting_same_collection_with_modified_flower_color(self):
        url = self.live_server_url + reverse('plants:api-collection-list')
        payloads = [
            {'species':
                {'genus': {
                    'family': {
                        'name': 'Cactaceae',
                        'vernacular_name': 'Cactus'
                    },
                    'name': 'Opuntia'
                },
                    'name': 'polyacantha',
                    'full_name': 'Opuntia polyacantha var. trichophora',
                    'subspecies': '',
                    'variety': 'trichophora',
                    'subvariety': '',
                    'forma': '',
                    'subforma': '',
                    'cultivar': '',
                    'vernacular_name': 'Threadspine Pricklypear',
                    'habit': 'Succulent',
                    'hardiness': [7, 8, 9, 10, 11],
                    'water_regime': 'Very Low',
                    'exposure': 'Full Sun',
                    'bloom_time': [],
                    'plant_size': '15"h x 3\'w',
                    'flower_color': 'Yellow',
                    'utah_native': True,
                    'plant_select': False,
                    'deer_resist': True,
                    'rabbit_resist': True,
                    'bee_friend': True,
                    'high_elevation': False
                },
                'garden': {
                    'area': 'Adaptive Beauty',
                    'name': 'Water Conservation Garden',
                    'code': 'WCG-09'
                },
                'location': {
                    'latitude': 40.767433,
                    'longitude': -111.823954
                },
                'plant_date': '2016-1-10',
                'plant_id': '2015-0308*3',
                'commemoration_category': '',
                'commemoration_person': ''
            },

            {'species':
                {'genus': {
                    'family': {
                        'name': 'Cactaceae',
                        'vernacular_name': 'Cactus'
                    },
                    'name': 'Opuntia'
                },
                    'name': 'polyacantha',
                    'full_name': 'Opuntia polyacantha var. trichophora',
                    'subspecies': '',
                    'variety': 'trichophora',
                    'subvariety': '',
                    'forma': '',
                    'subforma': '',
                    'cultivar': '',
                    'vernacular_name': 'Threadspine Pricklypear',
                    'habit': 'Succulent',
                    'hardiness': [7, 8, 9, 10, 11],
                    'water_regime': 'Very Low',
                    'exposure': 'Full Sun',
                    'bloom_time': [],
                    'plant_size': '15"h x 3\'w',
                    'flower_color': 'White',
                    'utah_native': True,
                    'plant_select': False,
                    'deer_resist': True,
                    'rabbit_resist': True,
                    'bee_friend': True,
                    'high_elevation': False
                },
                'garden': {
                    'area': 'Adaptive Beauty',
                    'name': 'Water Conservation Garden',
                    'code': 'WCG-09'
                },
                'location': {
                    'latitude': 40.767433,
                    'longitude': -111.823954
                },
                'plant_date': '2016-1-10',
                'plant_id': '2015-0308*3',
                'commemoration_category': '',
                'commemoration_person': ''
            },
        ]

        self.assertEqual(Collection.objects.all().count(), 0)

        first_response = self.client.post(url, json=payloads[0])
        self.assertTrue(status.is_success(first_response.status_code))

        self.assertEqual(Collection.objects.all().count(), 1)

        self.assertEqual(Collection.objects.first().species.flower_color, 'Yellow')

        second_response = self.client.post(url, json=payloads[1])
        print(second_response.content)
        self.assertTrue(status.is_success(second_response.status_code))

        self.assertEqual(Collection.objects.all().count(), 1)

        self.assertEqual(Collection.objects.first().species.flower_color, 'White')

    def test_query_species_api(self):
        """
        If you query for just 'Genus species', while other fields are specified as empty strings,
        it should not return Species objects with subspecies, cultivars, etc.
        """
        species_one = get_species(self.genus, name='species_one', full_name='Genus species_one',
                                subspecies='', variety='', subvariety='', forma='', subforma='', cultivar='',
                                vernacular_name='Species One')
        species_subspecies = get_species(self.genus, name='species_one', full_name='Genus species_one subsp. subspecies',
                                subspecies='subspecies', variety='', subvariety='', forma='', subforma='', cultivar='',
                                vernacular_name='Subspecies One')
        
        search_payload = {'genus': 'Genus', 'name': 'species_one', 'subspecies': '', 'variety': '', 'subvariety': '', 'forma': '', 'subforma': '', 'cultivar': ''}

        url = url = self.live_server_url + reverse('plants:api-species-list')
        resp = self.client.get(url, params=search_payload)
        content = resp.json()

        self.assertEqual(content['count'], 1)
