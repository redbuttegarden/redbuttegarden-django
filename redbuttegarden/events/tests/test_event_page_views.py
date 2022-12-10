from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.models import Page
from wagtail.images.tests.utils import Image, get_test_image_file

from events.models import EventIndexPage, EventPage


class TestEventIndex(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')

    def test_event_index_page(self):
        event_index = EventIndexPage(owner=self.user,
                                     slug='event-index-page',
                                     title='Event Index Page')
        self.root_page.add_child(instance=event_index)
        event_index.save_revision().publish()

        response = self.client.get('/event-index-page', follow=True)
        self.assertEqual(response.status_code, 200)


class TestEventPage(TestCase):
    def setUp(self):
        self.root_page = Page.objects.get(id=2)
        self.image = Image.objects.create(title='Test image', file=get_test_image_file())
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.event_index = EventIndexPage(owner=self.user,
                                          slug='event-index-page',
                                          title='Event Index Page')
        self.root_page.add_child(instance=self.event_index)
        self.event_index.save_revision().publish()

    def test_event_page(self):
        event_page = EventPage(owner=self.user,
                               slug='event-page',
                               title='Event Page')
        event_page.location = "Red Butte Garden"
        event_page.event_dates = "December 10th"
        self.event_index.add_child(instance=event_page)
        event_page.save_revision().publish()

        response = self.client.get(event_page.url, follow=True)
        self.assertEqual(response.status_code, 200)
