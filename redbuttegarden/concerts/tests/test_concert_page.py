import datetime
import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from wagtail.core.models import Page
from wagtail.images.tests.utils import Image, get_test_image_file

from concerts.models import ConcertPage
from concerts.utils import live_in_the_past


class TestConcert(TestCase):
    def setUp(self):
        """
        Concert data can be created like so:
        body=json.dumps([
                        {"type": "concerts",
                         "value": {"band_img": 773,
                                   "virtual": False,
                                   "canceled": False,
                                   "postponed": False,
                                   "sold_out": False,
                                   "available_until": None,
                                   "band_info": "<h4><b>Nathaniel Rateliff</b></h4>",
                                   "concert_dates": ["2021-03-11T19:00:00-07:00",
                                                     "2021-03-12T14:00:00-07:00"],
                                   "gates_time": "14:00:00",
                                   "show_time": "19:00:00",
                                   "member_price": "BandsInTown Plus Subscription",
                                   "public_price": "BandsInTown Plus Subscription",
                                   "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                                   }}
                         ])
        """
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
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
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": ["2021-03-11T19:00:00-07:00",
                                         "2021-03-12T14:00:00-07:00"],
                       "gates_time": "14:00:00",
                       "show_time": "19:00:00",
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }}
        ])
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
        concert_past_date = timezone.now() - datetime.timedelta(days=1)
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": [concert_past_date.isoformat()],
                       "gates_time": "14:00:00",
                       "show_time": "19:00:00",
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }}
        ])
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertContains(response, '<div class="infowrapper past">')
        # Emulate the behavior of ConcertPage.get_context to test live_in_the_past util
        concert_stream_block = self.concert_page.body[0]
        concert_block_value = concert_stream_block.value
        self.assertTrue(live_in_the_past(concert_block_value))

    def test_single_present_concert_date_template_logic(self):
        """
        Concert with date of today should not have the 'past' class
        """
        # If don't add a small timedelta, the concert date will be in the past by the time we load the page
        concert_present_date = timezone.now() + datetime.timedelta(minutes=5)
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": [concert_present_date.isoformat()],
                       "gates_time": "14:00:00",
                       "show_time": "19:00:00",
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }}
        ])
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        # Emulate the behavior of ConcertPage.get_context to test live_in_the_past util
        concert_stream_block = self.concert_page.body[0]
        concert_block_value = concert_stream_block.value
        self.assertFalse(live_in_the_past(concert_block_value))

    def test_single_future_concert_date_template_logic(self):
        """
        Concert with date in the future should not have the 'past' class
        """
        concert_future_date = timezone.now() + datetime.timedelta(days=1)
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": [concert_future_date.isoformat()],
                       "gates_time": "14:00:00",
                       "show_time": "19:00:00",
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }}
        ])
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        # Emulate the behavior of ConcertPage.get_context to test live_in_the_past util
        concert_stream_block = self.concert_page.body[0]
        concert_block_value = concert_stream_block.value
        self.assertFalse(live_in_the_past(concert_block_value))

    def test_past_present_concert_date_template_logic(self):
        """
        Concert with date in the past and date of today should not have the 'past' class
        """
        concert_past_date = timezone.now() - datetime.timedelta(days=1)
        # If don't add a small timedelta, the concert date will be in the past by the time we load the page
        concert_present_date = timezone.now() + datetime.timedelta(minutes=5)
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": [concert_past_date.isoformat(),
                                         concert_present_date.isoformat()],
                       "gates_time": "14:00:00",
                       "show_time": "19:00:00",
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }}
        ])
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        self.assertNotContains(response, '<div class="infowrapper past">')
        # Emulate the behavior of ConcertPage.get_context to test live_in_the_past util
        concert_stream_block = self.concert_page.body[0]
        concert_block_value = concert_stream_block.value
        self.assertFalse(live_in_the_past(concert_block_value))

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
