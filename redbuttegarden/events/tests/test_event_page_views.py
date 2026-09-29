from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.models import Page
from wagtail.images.tests.utils import Image, get_test_image_file

from events.models import EventGeneralPage, EventIndexPage, EventPage


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

        event_page = EventPage(
            owner=self.user,
            slug='linked-event-page',
            title='Linked Event Page',
            location='Red Butte Garden',
            event_dates='December 10th',
            thumbnail=self.image,
        )
        event_index.add_child(instance=event_page)
        event_page.save_revision().publish()
        event_index.body = [('page_link', event_page)]
        event_index.save_revision().publish()

        response = self.client.get('/event-index-page', follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf8')
        self.assertEqual(html.count('linked-thumbnail-grid'), 2)
        self.assertEqual(html.count('linked-thumbnail-card'), 2)
        self.assertEqual(html.count('linked-thumbnail-link'), 2)
        self.assertEqual(html.count('linked-thumbnail-media'), 2)


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
        self.assertContains(response, '<h1 class="event-page-title mt-5 mt-md-3">Event Page</h1>')


class TestEventGeneralPage(TestCase):
    """Verify event general pages use the shared optional banner markup."""

    def setUp(self) -> None:
        self.root_page = Page.objects.get(id=2)
        self.user = get_user_model().objects.create_user(
            "Event editor",
            "event-editor@example.com",
            "password",
        )
        self.event_index = EventIndexPage(
            owner=self.user,
            slug="general-event-index",
            title="General Event Index",
        )
        self.root_page.add_child(instance=self.event_index)
        self.event_index.save_revision().publish()

    def _create_event_general_page(
        self,
        *,
        banner: Image | None = None,
    ) -> EventGeneralPage:
        """Create and publish an event general page with an optional banner."""

        page = EventGeneralPage(
            owner=self.user,
            slug="event-general-page",
            title="Event General Page",
            event_dates="December 10th",
            banner=banner,
        )
        self.event_index.add_child(instance=page)
        page.save_revision().publish()
        return page

    def test_page_with_banner_uses_shared_responsive_markup(self) -> None:
        banner = Image.objects.create(
            title="Event banner",
            file=get_test_image_file(filename="event-banner.png"),
        )
        page = self._create_event_general_page(banner=banner)

        response = self.client.get(page.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<div class="row text-center my-3">')
        self.assertContains(response, 'class="img-fluid"')

    def test_page_without_banner_renders_successfully(self) -> None:
        page = self._create_event_general_page()

        response = self.client.get(page.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Event General Page")
