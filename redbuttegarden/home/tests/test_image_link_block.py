from django.core.exceptions import ValidationError
from django.test import TestCase
from wagtail import blocks
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file

from home.models import ImageLink


class ImageLinkBlockTests(TestCase):
    """Verify accessible-name validation for linked images."""

    def setUp(self) -> None:
        self.block = ImageLink()
        self.image = get_image_model().objects.create(
            title="Garden image",
            file=get_test_image_file(filename="image-link.png"),
        )

    def _value(self, **overrides: object) -> blocks.StructValue:
        """Build an ImageLink value with stable valid defaults."""

        data = {
            "title": "",
            "url": "https://example.com/visit/",
            "url_title": "",
            "image": {
                "image": self.image.pk,
                "decorative": True,
                "alt_text": "",
            },
        }
        data.update(overrides)
        return self.block.to_python(data)

    def test_visible_title_provides_accessible_name(self) -> None:
        cleaned = self.block.clean(self._value(title="Visit the garden"))

        self.assertEqual(cleaned["title"], "Visit the garden")

    def test_url_title_provides_accessible_name_without_visible_title(self) -> None:
        cleaned = self.block.clean(self._value(url_title="Visit the garden"))

        self.assertEqual(cleaned["url_title"], "Visit the garden")

    def test_publication_validation_normalizes_accessible_names(self) -> None:
        cleaned = self.block.clean(
            self._value(title="  Visit the garden  ", url_title="  Visit link  ")
        )

        self.assertEqual(cleaned["title"], "Visit the garden")
        self.assertEqual(cleaned["url_title"], "Visit link")

    def test_deferred_validation_normalizes_accessible_names(self) -> None:
        cleaned = self.block.clean_deferred(self._value(title="  Draft title  "))

        self.assertEqual(cleaned["title"], "Draft title")
        self.assertEqual(cleaned["url_title"], "")

    def test_publication_validation_rejects_missing_accessible_name(self) -> None:
        with self.assertRaises(ValidationError) as raised:
            self.block.clean(self._value())

        self.assertIn("url_title", raised.exception.block_errors)

    def test_publication_validation_rejects_whitespace_accessible_names(
        self,
    ) -> None:
        with self.assertRaises(ValidationError) as raised:
            self.block.clean(self._value(title="   ", url_title="   "))

        self.assertIn("url_title", raised.exception.block_errors)

    def test_deferred_validation_allows_missing_accessible_name(self) -> None:
        self.block.clean_deferred(self._value())

    def test_deferred_validation_still_rejects_malformed_url(self) -> None:
        with self.assertRaises(ValidationError):
            self.block.clean_deferred(self._value(url="not a URL"))
