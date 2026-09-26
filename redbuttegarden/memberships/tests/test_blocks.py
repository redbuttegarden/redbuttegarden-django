from django.core.exceptions import ValidationError
from django.test import TestCase
from wagtail.blocks import StructBlockValidationError
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page

from memberships.blocks import LinkedCarouselSlideBlock, PricingCardCTA


class LinkedCarouselSlideBlockValidationTests(TestCase):
    """Verify linked-image alt text is required only at publication time."""

    def setUp(self) -> None:
        self.block = LinkedCarouselSlideBlock()
        self.image = get_image_model().objects.create(
            title="Test image",
            file=get_test_image_file(),
        )
        self.internal_page = Page.objects.get(slug="home")

    def value(self, **overrides):
        """Build a slide value without database access."""

        data = {
            "image": self.image.pk,
            "alt_text": "",
            "caption": "",
            "link_page": None,
            "link_url": "https://example.com",
            "open_in_new_tab": False,
        }
        data.update(overrides)
        return self.block.to_python(data)

    def test_linked_slide_requires_alt_text_for_publication(self) -> None:
        with self.assertRaises(StructBlockValidationError) as error:
            self.block.clean(self.value())

        self.assertIn("alt_text", error.exception.block_errors)

    def test_linked_slide_may_remain_incomplete_in_a_draft(self) -> None:
        self.block.clean_deferred(self.value())

    def test_linked_slide_with_alt_text_is_valid(self) -> None:
        cleaned = self.block.clean(self.value(alt_text="Membership options"))

        self.assertEqual(cleaned["alt_text"], "Membership options")

    def test_unlinked_slide_may_be_decorative(self) -> None:
        cleaned = self.block.clean(self.value(link_url=""))

        self.assertEqual(cleaned["alt_text"], "")

    def test_multiple_link_destinations_remain_invalid_in_drafts(self) -> None:
        with self.assertRaises(StructBlockValidationError) as error:
            self.block.clean_deferred(
                self.value(link_page=self.internal_page.pk)
            )

        self.assertIn("link_url", error.exception.block_errors)


class PricingCardCTADeferredValidationTests(TestCase):
    """Verify CTA completeness is enforced only for publication validation."""

    def setUp(self) -> None:
        self.block = PricingCardCTA()
        self.internal_page = Page.objects.get(slug="home")

    def value(self, **overrides):
        """Build a PricingCardCTA value with stable defaults."""

        data = {
            "text": "",
            "page": None,
            "url": "",
            "style": "primary",
            "full_width": False,
            "new_tab": False,
        }
        data.update(overrides)
        return self.block.to_python(data)

    def test_deferred_validation_allows_text_without_destination(self) -> None:
        cleaned = self.block.clean_deferred(self.value(text="Join now"))

        self.assertEqual(cleaned["text"], "Join now")

    def test_publication_validation_rejects_text_without_destination(self) -> None:
        with self.assertRaises(ValidationError):
            self.block.clean(self.value(text="Join now"))

    def test_deferred_validation_still_rejects_malformed_url(self) -> None:
        with self.assertRaises(ValidationError):
            self.block.clean_deferred(self.value(text="Join", url="not a URL"))

    def test_deferred_validation_rejects_conflicting_destinations(self) -> None:
        with self.assertRaises(ValidationError) as error:
            self.block.clean_deferred(
                self.value(
                    text="Join now",
                    page=self.internal_page.pk,
                    url="https://example.com",
                )
            )

        self.assertIn("url", error.exception.error_dict)
