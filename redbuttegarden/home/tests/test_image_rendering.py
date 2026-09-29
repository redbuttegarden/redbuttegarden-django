from django.test import TestCase
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file

from home.models import ImageCarousel, ImageLinkList, ImageListCardInfo, ImageListDropdownInfo
from memberships.blocks import LinkedCarouselBlock


class ImageBlockRenderingTests(TestCase):
    """Verify shared image blocks retain contextual alt text and bounded sources."""

    def setUp(self) -> None:
        self.image = get_image_model().objects.create(
            title="Library title",
            file=get_test_image_file(filename="shared-image.png"),
        )

    def image_value(self, alt_text: str, *, decorative: bool = False) -> dict:
        """Return the serialized value expected by Wagtail's ImageBlock."""

        return {
            "image": self.image.pk,
            "decorative": decorative,
            "alt_text": alt_text,
        }

    def test_dropdown_image_uses_contextual_alt_and_modern_formats(self) -> None:
        block = ImageListDropdownInfo()
        value = block.to_python(
            {
                "list_items": [
                    {
                        "image": self.image_value("Garden path in spring"),
                        "title": "Spring",
                        "text": "<p>Details</p>",
                    }
                ]
            }
        )

        html = block.render(value, context={"id": "dropdown"})

        self.assertIn('alt="Garden path in spring"', html)
        self.assertIn('<button type="button"', html)
        self.assertIn('data-bs-target="#dropdown-1"', html)
        self.assertNotIn('role="button"', html)
        self.assertIn('type="image/avif"', html)
        self.assertIn('type="image/webp"', html)
        self.assertLess(
            html.index('type="image/avif"'),
            html.index('type="image/webp"'),
        )
        button_html = html[html.index("<button") : html.index("</button>")]
        self.assertIn('<span class="eventinfo d-block">', button_html)
        self.assertNotIn("<div", button_html)
        self.assertNotIn(self.image.file.url, html)

    def test_card_image_retains_decorative_empty_alt(self) -> None:
        block = ImageListCardInfo()
        value = block.to_python(
            {
                "layout": "two_column",
                "auto_threshold": 400,
                "list_items": [
                    {
                        "image": self.image_value("", decorative=True),
                        "text": "<p>Details</p>",
                        "button_text": "",
                        "button_url": "",
                        "force_full_width": False,
                    }
                ],
            }
        )

        html = block.render(value)

        self.assertIn('alt=""', html)
        self.assertIn('width="200"', html)

    def test_image_carousel_uses_contextual_alt_text(self) -> None:
        block = ImageCarousel()
        value = block.to_python(
            {
                "images": [self.image_value("Carousel garden view")],
                "max_height": 500,
            }
        )

        html = block.render(value, context={"id": "carousel"})

        self.assertIn('alt="Carousel garden view"', html)
        self.assertNotIn('alt="Library title"', html)

    def test_image_link_list_uses_shared_linked_thumbnail_classes(self) -> None:
        block = ImageLinkList()
        value = block.to_python(
            {
                "list_items": [
                    {
                        "title": "Visit the garden",
                        "url": "https://example.com/visit/",
                        "url_title": "",
                        "image": self.image_value("", decorative=True),
                    }
                ]
            }
        )

        html = block.render(value, context={"id": "links"})

        self.assertIn("linked-thumbnail-grid", html)
        self.assertIn('class="linked-thumbnail-card mb-3"', html)
        self.assertIn('class="linked-thumbnail-link"', html)
        self.assertIn('class="img-link linked-thumbnail-media"', html)
        self.assertNotIn('class="img-link hover"', html)
        self.assertIn(
            '<div class="eventname">Visit the garden</div>',
            html,
        )
        self.assertNotIn("aria-label=", html)

    def test_titleless_image_link_uses_escaped_aria_label(self) -> None:
        block = ImageLinkList()
        value = block.to_python(
            {
                "list_items": [
                    {
                        "title": "",
                        "url": "https://example.com/visit/",
                        "url_title": 'Garden "hours" & tickets',
                        "image": self.image_value("", decorative=True),
                    }
                ]
            }
        )

        html = block.render(value, context={"id": "fallback-title"})

        self.assertIn(
            'aria-label="Garden &quot;hours&quot; &amp; tickets"',
            html,
        )
        self.assertNotIn('class="eventname"', html)

    def test_whitespace_image_link_title_uses_escaped_url_title(self) -> None:
        block = ImageLinkList()
        value = block.to_python(
            {
                "list_items": [
                    {
                        "title": "   ",
                        "url": "https://example.com/visit/",
                        "url_title": '  Garden "hours" & tickets  ',
                        "image": self.image_value("", decorative=True),
                    }
                ]
            }
        )

        html = block.render(
            value,
            context={"id": "whitespace-visible-title"},
        )

        self.assertIn(
            'aria-label="Garden &quot;hours&quot; &amp; tickets"',
            html,
        )
        self.assertNotIn('class="eventname"', html)

    def test_linked_carousel_is_bounded_and_preserves_explicit_alt(self) -> None:
        block = LinkedCarouselBlock()
        value = block.to_python(
            [
                {
                    "image": self.image.pk,
                    "alt_text": "Membership benefits",
                    "caption": "",
                    "link_page": None,
                    "link_url": "",
                    "open_in_new_tab": False,
                }
            ]
        )

        html = block.render(value, context={"id": "linked"})

        self.assertIn('alt="Membership benefits"', html)
        self.assertIn('width="640"', html)
        self.assertNotIn("original", html)
