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
        body=json.dumps([{"type": "concerts",
                         "value": {"band_img": 773,
                                   "hidden": True,
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
                                   }
                          }])
        """
        self.root_page = Page.objects.get(id=2)
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.concert_page = ConcertPage(owner=self.user,
                                        slug='concert-test-page',
                                        title='Concert Test Page')
        self.root_page.add_child(instance=self.concert_page)
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
        """Default concert with the exception of hidden set to false."""
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
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

    def test_multiple_concert_view_default_concert(self):
        """Default concerts with the exception of hidden set to false."""
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>First Concert</b></h4>",
                       "concert_dates": ["2021-03-11T19:00:00-07:00",
                                         "2021-03-12T14:00:00-07:00"],
                       "gates_time": "14:00:00",
                       "show_time": "19:00:00",
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }},
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Second Concert</b></h4>",
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
        self.assertContains(response, "First Concert")
        self.assertContains(response, "Second Concert")

    def test_single_past_concert_date_template_logic(self):
        """
        Concert with date in the past should have the 'past' class
        """
        concert_past_date = timezone.now() - datetime.timedelta(days=1)
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
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
                       "hidden": False,
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
                       "hidden": False,
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
                       "hidden": False,
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
        concert_past_date = timezone.now() - datetime.timedelta(days=1)
        concert_future_date = timezone.now() + datetime.timedelta(days=1)
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": [concert_past_date.isoformat(),
                                         concert_future_date.isoformat()],
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

    def test_hidden_concerts(self):
        """
        Create two concerts; one with hidden set to false and the other true.
        Only concert with hidden set to False should be visible.
        """
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
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
                       }},
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": True,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Hidden Band Info Test</b></h4>",
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
        self.assertNotContains(response, "Hidden Band Info Test")

    def test_concert_not_on_sale(self):
        """
        If on_sale is False, buy button should use different alt tag
        and be surrounded by a div rather than an anchor tag.
        """
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
                       "on_sale": False,
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
        # Looks for alt tags of buy button used in the template
        self.assertContains(response, 'alt="Not yet on sale"')
        self.assertContains(response, '<div class="disable-buy">')
        self.assertNotContains(response, 'alt="Buy ticket button"')
        self.assertNotContains(response, '<img class="responsive con-button hover"')

    def test_concert_times_tbd(self):
        """
        When Show Time and Gate Time are left blank, a message
        indicating times are still to be determined should be
        displayed in their place.
        """
        self.concert_page.body = json.dumps([
            {"type": "concerts",
             "value": {"band_img": 773,
                       "hidden": False,
                       "on_sale": True,
                       "virtual": False,
                       "canceled": False,
                       "postponed": False,
                       "sold_out": False,
                       "available_until": None,
                       "band_info": "<h4><b>Band Info Test</b></h4>",
                       "concert_dates": ["2021-03-11T19:00:00-07:00",
                                         "2021-03-12T14:00:00-07:00"],
                       "gates_time": None,
                       "show_time": None,
                       "member_price": "BandsInTown Plus Subscription",
                       "public_price": "BandsInTown Plus Subscription",
                       "ticket_url": "https://www.awin1.com/cread.php?awinmid=19610&awinaffid=846015&ued="
                       }}
        ])
        self.concert_page.save_revision().publish()

        response = self.client.get('/concert-test-page', follow=True)
        # Looks for alt tags of buy button used in the template
        self.assertContains(response, "Gate & Show Times TBD")
