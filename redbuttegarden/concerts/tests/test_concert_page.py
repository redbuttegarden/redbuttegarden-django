import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.core.models import Page
from wagtail.images.tests.utils import Image, get_test_image_file
from wagtail.tests.utils.form_data import rich_text

from concerts.models import ConcertPage


class TestConcert(TestCase):
    def setUp(self):
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.concert_page = ConcertPage(owner=self.user,
                                        slug='concert-test-page',
                                        title='Concert Test Page',
                                        body=json.dumps([
                                            # Type ConcertStreamBlock
                                            {'type': 'concerts',
                                             #
                                             'value': {
                                                'concerts': [

                                                ]
                                            }}
                                        ]))
        self.concert = Concert(page=self.concert_page,
                               band_img=self.image,
                               band_info=rich_text('<h1>Band Info Test</h1>'))
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
        concert_date = ConcertDate(date=datetime.date.today())
        self.concert.concert_dates.add(concert_date)
        self.concert.save()
        self.concert_page.concerts.add(self.concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, "Available On Demand")
        self.assertContains(response, "Gates at")
        self.assertContains(response, "Show at")
        self.assertContains(response, "Band Info Test")

    def test_single_past_concert_date_template_logic(self):
        """
        Concert with date in the past should have the 'past' class
        """
        concert_past_date = ConcertDate(date=datetime.date.today() - datetime.timedelta(days=1))
        self.concert.concert_dates.add(concert_past_date)
        self.concert.save()
        self.concert_page.concerts.add(self.concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertContains(response, '<div class="infowrapper past">')
        self.assertTrue(self.concert.live_in_the_past())

    def test_single_present_concert_date_template_logic(self):
        """
        Concert with date of today should not have the 'past' class
        """
        concert_present_date = ConcertDate(date=datetime.date.today())
        self.concert.concert_dates.add(concert_present_date)
        self.concert.save()
        self.concert_page.concerts.add(self.concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        self.assertFalse(self.concert.live_in_the_past())

    def test_single_future_concert_date_template_logic(self):
        """
        Concert with date in the future should not have the 'past' class
        """
        concert_future_date = ConcertDate(date=datetime.date.today() + datetime.timedelta(days=1))
        self.concert.concert_dates.add(concert_future_date)
        self.concert.save()
        self.concert_page.concerts.add(self.concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        self.assertFalse(self.concert.live_in_the_past())

    def test_past_present_concert_date_template_logic(self):
        """
        Concert with date in the past and date of today should not have the 'past' class
        """
        concert_past_date = ConcertDate(date=datetime.date.today() - datetime.timedelta(days=1))
        concert_present_date = ConcertDate(date=datetime.date.today())
        self.concert.concert_dates.add(concert_past_date)
        self.concert.concert_dates.add(concert_present_date)
        self.concert.save()
        self.concert_page.concerts.add(self.concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        self.assertFalse(self.concert.live_in_the_past())

    def test_past_future_concert_date_template_logic(self):
        """
        Concert with dates in the past and future should not have the 'past' class
        """
        concert_past_date = ConcertDate(date=datetime.date.today() - datetime.timedelta(days=1))
        concert_future_date = ConcertDate(date=datetime.date.today() + datetime.timedelta(days=1))
        self.concert.concert_dates.add(concert_past_date)
        self.concert.concert_dates.add(concert_future_date)
        self.concert.save()
        self.concert_page.concerts.add(self.concert)
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        self.assertFalse(self.concert.live_in_the_past())
