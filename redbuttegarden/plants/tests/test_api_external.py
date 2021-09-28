from io import BytesIO

from django.contrib.auth.models import Group
from django.core.files.images import ImageFile
from django.urls import reverse
from PIL import Image
from rest_framework.authtoken.models import Token
from rest_framework.test import RequestsClient, APILiveServerTestCase

from plants.models import SpeciesImage
from .utils import get_custom_user, get_family, get_genus, get_species


class TestAPIFromExternalPerspective(APILiveServerTestCase):
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


    def test_posting_species_image(self):
        url = self.live_server_url + reverse('plants:api-set-species-image', kwargs={'pk': self.species.pk})
        img_one_file_obj = BytesIO()

        image_one = Image.new('RGB', size=(1, 1), color=(256, 0, 0))

        image_one.save(img_one_file_obj, 'jpeg')

        img_one_file_obj.seek(0)

        img_one = ImageFile(img_one_file_obj, name='1.jpg')
        test_copyright_info = 'Example Copyright Info'

        self.assertRaises(SpeciesImage.DoesNotExist, SpeciesImage.objects.get, species=self.species)

        r = self.client.post(url, data={'copyright_info': test_copyright_info}, files={'image': img_one})
        self.assertEquals(r.status_code, 200)

        species_image = SpeciesImage.objects.get(species=self.species)
        self.assertEqual(species_image.copyright, test_copyright_info)
