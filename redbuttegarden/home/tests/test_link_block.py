from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from home.blocks import LinkBlock


class LinkBlockDeferredValidationTests(SimpleTestCase):
    """Verify draft-only relaxation of LinkBlock completeness rules."""

    def setUp(self) -> None:
        self.block = LinkBlock()

    def value(self, **overrides):
        """Build a LinkBlock value with stable defaults."""

        data = {
            "label": "Example",
            "description": "",
            "open_in_new_tab": False,
            "internal_page": None,
            "external_url": "",
            "named_url": "",
            "routable_page": None,
            "route_name": "",
            "route_args_json": "",
            "route_kwargs_json": "",
        }
        data.update(overrides)
        return self.block.to_python(data)

    def test_deferred_validation_allows_missing_destination(self) -> None:
        self.block.clean_deferred(self.value())

    def test_publication_validation_rejects_missing_destination(self) -> None:
        with self.assertRaises(ValidationError):
            self.block.clean(self.value())

    def test_deferred_validation_rejects_conflicting_destinations(self) -> None:
        with self.assertRaises(ValidationError):
            self.block.clean_deferred(
                self.value(external_url="https://example.com", named_url="home")
            )

    def test_deferred_validation_allows_incomplete_routable_destination(self) -> None:
        cleaned = self.block.clean_deferred(self.value(route_name="event_detail"))

        self.assertEqual(cleaned["route_name"], "event_detail")

    def test_deferred_validation_still_rejects_invalid_route_json(self) -> None:
        with self.assertRaises(ValidationError):
            self.block.clean_deferred(
                self.value(route_name="event_detail", route_args_json="not json")
            )
