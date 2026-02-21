from pprint import pprint

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, AnonymousUser
from django.test import TestCase, RequestFactory
from django.urls import reverse
from wagtail.models import Site, Page, PageViewRestriction

from search.views import search


class SearchTestCase(TestCase):
    def setUp(self) -> None:
        self.user = get_user_model().objects.create_user(
            "Test User", "test@email.com", "password"
        )
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        self.default_site = Site.objects.get(id=1)
        self.root_page = Page.objects.get(id=1)
        self.training_root_page = Page(owner=self.user, slug="Test", title="Test")
        self.root_page.add_sibling(instance=self.training_root_page)
        PageViewRestriction.objects.create(
            page=self.training_root_page,
            restriction_type="password",
            password="password123",
        )
        self.training_root_page.save_revision().publish()
        self.training_site = Site(
            hostname="localhost",
            port="8000",
            site_name="Training",
            root_page=self.training_root_page,
        )
        self.training_site.save()

        self.factory = RequestFactory()

    def test_search_does_not_return_training_pages(self):
        """
        Searches should not return results from the Wagtail "Training" Site.
        """
        request = self.factory.get(reverse("search"), {"query": "Test"})
        request.user = AnonymousUser()

        response = search(request)

        self.assertNotContains(
            response, '<h4><a href="http://localhost:8000/">Test</a></h4>'
        )

    def test_search_with_null_byte(self):
        response = self.client.get("/search/?page=1&q=True%00")
        assert response.status_code == 200
