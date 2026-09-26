from django.test import RequestFactory, SimpleTestCase
from wagtail.admin.userbar import ContentCheckerItem

from home.wagtail_hooks import (
    RBGContentCheckerItem,
    customise_content_checker,
)


class RBGContentCheckerTests(SimpleTestCase):
    """Verify native checks are preserved when adding RBG guidance."""

    def setUp(self) -> None:
        self.request = RequestFactory().get("/")

    def test_configuration_extends_native_checker(self) -> None:
        checker = RBGContentCheckerItem()
        configuration = checker.get_axe_configuration(self.request)

        self.assertIn("empty-meta-description", configuration["options"]["runOnly"])
        self.assertIn("rbg-link-text-quality", configuration["options"]["runOnly"])
        self.assertTrue(
            any(
                rule["id"] == "rbg-link-text-quality"
                for rule in configuration["spec"]["rules"]
            )
        )
        custom_check = next(
            check
            for check in configuration["spec"]["checks"]
            if check["id"] == "check-rbg-link-text"
        )
        self.assertEqual(
            custom_check["options"]["antipattern"],
            r"^(?:click here|here|more)$",
        )

    def test_replacement_preserves_editor_mode(self) -> None:
        items = [ContentCheckerItem(in_editor=True)]

        customise_content_checker(self.request, items, page=None)

        self.assertIsInstance(items[0], RBGContentCheckerItem)
        self.assertTrue(items[0].in_editor)
