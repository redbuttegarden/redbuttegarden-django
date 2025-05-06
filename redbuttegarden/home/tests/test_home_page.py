import json
from django.contrib.auth.models import Group
from wagtail.models import Page
from wagtail.images import get_image_model
from wagtail.images.tests.utils import get_test_image_file
from wagtail.test.utils import WagtailPageTests, get_user_model
from wagtail.test.utils.form_data import nested_form_data, rich_text

from home.models import HomePage


class TestHomePage(WagtailPageTests):
    def setUpTestData(cls):
        cls.root_page = Page.objects.first()
        cls.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        cls.user.groups.add(Group.objects.get(name="Moderators"))
        cls.client.force_login(cls.user)

        cls.image = get_image_model().objects.create(title='Test image', file=get_test_image_file())

    def test_can_create_home_page(self):
        self.assertCanCreate(self.root_page, HomePage, nested_form_data({
            'title': 'Home Test Page',
            'hours_section_text': rich_text('<p>Example hours section text.</p>'),
        }))

    def test_home_page(self):
        home_page = HomePage(owner=self.user,
                             title='Home Test Page',
                             hours_section_text=rich_text('<p>Example hours section text.</p>')
                             )
        self.root_page.add_child(instance=home_page)
        home_page.save_revision().publish()
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf8')
        self.assertIn('<p>Example hours section text.</p>', html)
