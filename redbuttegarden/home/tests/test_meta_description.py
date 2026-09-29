from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase
from wagtail.models import Page


class MetaDescriptionTemplateTests(TestCase):
    """Verify preview and live metadata expose the intended description."""

    def setUp(self) -> None:
        self.page = Page.objects.get(slug="home")
        self.page.title = "Fallback page title"
        self.page.search_description = ""
        self.factory = RequestFactory()

    def render(self, template_name: str, *, is_preview: bool) -> str:
        """Render a base template with a preview-aware request."""

        request = self.factory.get("/")
        request.is_preview = is_preview
        return render_to_string(
            template_name,
            {"page": self.page, "self": self.page},
            request=request,
        )

    def test_main_preview_keeps_empty_description(self) -> None:
        html = self.render("base.html", is_preview=True)

        self.assertIn('name="description"\n          content=""', html)

    def test_main_live_page_falls_back_to_title(self) -> None:
        html = self.render("base.html", is_preview=False)

        self.assertIn('content="Fallback page title"', html)

    def test_shop_preview_keeps_empty_description(self) -> None:
        html = self.render("shop/base_shop.html", is_preview=True)

        self.assertIn('<meta name="description" content="">', html)

    def test_shop_live_page_falls_back_to_title(self) -> None:
        html = self.render("shop/base_shop.html", is_preview=False)

        self.assertIn(
            '<meta name="description" content="Fallback page title">',
            html,
        )

    def test_populated_description_is_unchanged(self) -> None:
        self.page.search_description = "A concise description"

        html = self.render("base.html", is_preview=False)

        self.assertIn('content="A concise description"', html)

    def test_base_has_one_skip_link_and_focusable_main_target(self) -> None:
        html = self.render("base.html", is_preview=False)

        self.assertEqual(
            html.count('<a class="skip-main" href="#main">Skip to main content</a>'),
            1,
        )
        self.assertIn('<main id="main" tabindex="-1">', html)
        self.assertLess(html.index("<body"), html.index('class="skip-main"'))
        self.assertLess(html.index('class="skip-main"'), html.index('id="rbg-nav"'))

    def test_noscript_nav_does_not_duplicate_skip_link(self) -> None:
        html = render_to_string("includes/navbar_noscript.html")

        self.assertNotIn('class="skip-main"', html)
