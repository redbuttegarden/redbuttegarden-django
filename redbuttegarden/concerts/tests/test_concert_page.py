from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.core.models import Page
from wagtail.images.tests.utils import Image
from wagtail.tests.utils.form_data import rich_text

from concerts.models import ConcertPage, Concert


class TestConcert(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.concert_page = ConcertPage(owner=self.user,
                                        slug='concert-test-page',
                                        title='Concert Test Page')
        Page.objects.get(slug='home').add_child(instance=self.concert_page)
        self.concert_page.save_revision().publish()

    def test_concert_view_without_concerts(self):
        response = self.client.get('/concert-test-page', follow=True)
        html = response.content.decode('utf8')
        self.assertTrue(html.startswith('\n\n<!DOCTYPE html>'))
        self.assertIn('<title>Concert Test Page', html)
        self.assertTrue(html.endswith('</html>'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Available On Demand")
        self.assertNotContains(response, "Gates at")
        self.assertNotContains(response, "Show at")

    def test_concert_view_default_concert(self):
        band_img = Image()
        concert = Concert(page=self.concert_page,
                          band_img=band_img,
                          band_info=rich_text('<h1>Band Info Test</h1>'),
                          concert_date=date.today())
        self.concert_page.concerts.add(concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, "Available On Demand")
        self.assertContains(response, "Gates at")
        self.assertContains(response, "Show at")
        self.assertContains(response, "Band Info Test")
