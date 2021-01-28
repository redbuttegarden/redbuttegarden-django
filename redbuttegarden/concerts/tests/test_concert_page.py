from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.core.models import Page

from concerts.models import ConcertPage


class TestConcert(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        concert_page = ConcertPage(owner=self.user,
                                   slug='concert-test-page',
                                   title='Concert Test Page')
        Page.objects.get(slug='home').add_child(instance=concert_page)
        concert_page.save_revision().publish()

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