from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from wagtail.contrib.search_promotions.models import Query
from wagtail.models import Page, PageViewRestriction, Site


class SearchTestCase(TestCase):
    """Exercise public search scoping, correctness, and response formats."""

    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            username="search-editor",
            email="search@example.com",
            password="test-password",
        )
        self.site = Site.objects.get(is_default_site=True)
        self.site_root = self.site.root_page

    def create_page(self, title: str, slug: str, parent: Page | None = None) -> Page:
        """Create and publish a generic searchable page beneath the selected parent."""

        page = Page(title=title, slug=slug, owner=self.user)
        (parent or self.site_root).add_child(instance=page)
        page.save_revision(user=self.user).publish()
        return page

    def test_search_retains_distinct_pages_with_the_same_title(self) -> None:
        self.create_page("Search Twin", "search-twin-one")
        self.create_page("Search Twin", "search-twin-two")

        response = self.client.get(reverse("search"), {"q": "Search Twin"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_results"].paginator.count, 2)

    def test_search_excludes_other_sites_aliases_and_private_pages(self) -> None:
        visible = self.create_page("Scoped Result", "scoped-result")
        alias = visible.create_alias(
            parent=self.site_root,
            update_slug="scoped-result-alias",
            update_locale=None,
        )
        self.assertIsNotNone(alias.alias_of_id)

        private = self.create_page("Scoped Result Private", "scoped-result-private")
        PageViewRestriction.objects.create(
            page=private,
            restriction_type=PageViewRestriction.PASSWORD,
            password="test-password",
        )

        other_root = Page(title="Other site", slug="other-site", owner=self.user)
        Page.get_first_root_node().add_child(instance=other_root)
        self.create_page("Scoped Result Elsewhere", "scoped-result-elsewhere", other_root)
        Site.objects.create(
            hostname="other.example.com",
            site_name="Other",
            root_page=other_root,
        )

        response = self.client.get(reverse("search"), {"q": "Scoped Result"})
        results = list(response.context["search_results"].object_list)

        self.assertEqual([page.pk for page in results], [visible.pk])

    def test_empty_normalized_query_records_no_hit(self) -> None:
        response = self.client.get(reverse("search"), {"q": " \x00\x1f "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_results"].paginator.count, 0)
        self.assertFalse(Query.objects.exists())

    def test_ajax_uses_the_same_scoped_results(self) -> None:
        page = self.create_page("AJAX Result", "ajax-result")

        response = self.client.get(
            reverse("search"),
            {"q": "AJAX Result"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "results": [{"title": page.title, "url": page.url}],
                "page": 1,
                "pages": 1,
            },
        )

    def test_control_characters_are_removed_from_query(self) -> None:
        self.create_page("True Result", "true-result")

        response = self.client.get(reverse("search"), {"q": "True\x00"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["search_query"], "True")
