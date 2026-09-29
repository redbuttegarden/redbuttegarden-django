from django.contrib.auth import get_user_model
from django.test import TestCase
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Page

from home.models import GeneralIndexPage, GeneralPage


class GeneralIndexLinkedThumbnailTests(TestCase):
    def test_child_uses_shared_linked_thumbnail_classes(self) -> None:
        root_page = Page.objects.get(id=2)
        user = get_user_model().objects.create_user(
            "thumbnail-test-user",
            "thumbnail@example.com",
            "password",
        )
        image = get_image_model().objects.create(
            title="Thumbnail",
            file=get_test_image_file(filename="general-thumbnail.png"),
        )
        index_page = GeneralIndexPage(
            owner=user,
            slug="thumbnail-index",
            title="Thumbnail Index",
        )
        root_page.add_child(instance=index_page)
        index_page.save_revision().publish()
        child_page = GeneralPage(
            owner=user,
            slug="thumbnail-child",
            title="Thumbnail Child",
            thumbnail=image,
        )
        index_page.add_child(instance=child_page)
        child_page.save_revision().publish()

        response = self.client.get(index_page.url)

        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf8")
        self.assertIn("linked-thumbnail-grid", html)
        self.assertIn("index-tile linked-thumbnail-card", html)
        self.assertIn('class="linked-thumbnail-link"', html)
        self.assertIn("index-thumbnail linked-thumbnail-media", html)
