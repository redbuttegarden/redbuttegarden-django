import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.images.tests.utils import Image, get_test_image_file
from wagtail.models import Page

from concerts.models import ConcertPage, PastConcertPage


class PastConcertDisclosureAccessibilityTests(TestCase):
    """Verify concert-poster disclosures use native keyboard controls."""

    def test_poster_disclosure_is_a_button(self) -> None:
        user = get_user_model().objects.create_user(
            "concert-editor", "concert@example.com", "password"
        )
        image = Image.objects.create(
            title="Concert poster", file=get_test_image_file()
        )
        concert_page = ConcertPage(owner=user, title="Concerts", slug="concerts")
        Page.objects.get(slug="home").add_child(instance=concert_page)
        past_page = PastConcertPage(
            owner=user,
            title="Past concerts",
            slug="past-concerts",
            lineups=json.dumps(
                [
                    {
                        "type": "lineup",
                        "value": {
                            "year": 2025,
                            "poster": {
                                "image": image.pk,
                                "decorative": False,
                                "alt_text": "2025 concert lineup poster",
                            },
                            "artists": "<p>Test artist</p>",
                        },
                    }
                ]
            ),
        )
        concert_page.add_child(instance=past_page)

        response = self.client.get(past_page.url)

        self.assertContains(
            response,
            '<button type="button" id="poster-outer-0"',
            html=False,
        )
        self.assertContains(response, 'data-bs-target="#', html=False)
        html = response.content.decode("utf-8")
        poster_button_start = html.index('<button type="button" id="poster-outer-0"')
        poster_button_tag = html[
            poster_button_start : html.index(">", poster_button_start)
        ]
        poster_button_html = html[
            poster_button_start : html.index("</button>", poster_button_start)
        ]
        self.assertNotIn('role="button"', poster_button_tag)
        self.assertIn('<span class="poster-inner d-block">', poster_button_html)
        self.assertNotIn("<div", poster_button_html)
