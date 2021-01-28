from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import nested_form_data, streamfield

from home.models import FAQPage, GeneralPage, GeneralIndexPage, HomePage, PlantCollectionsPage, TwoColumnGeneralPage


class HomePageTests(WagtailPageTests):
    def test_can_create_FAQ(self):
        self.assertCanCreateAt(Page, FAQPage)

    def test_can_create_general(self):
        self.assertCanCreateAt(Page, GeneralPage)

    def test_can_create_general_index(self):
        self.assertCanCreateAt(Page, GeneralIndexPage)

    def test_can_create_home(self):
        self.assertCanCreateAt(Page, HomePage)

    def test_can_create_plant_collections(self):
        self.assertCanCreateAt(Page, PlantCollectionsPage)

    def test_can_create_two_col_general(self):
        self.assertCanCreateAt(Page, TwoColumnGeneralPage)


class HomePageInstanceTests(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_can_create_FAQ(self):
        self.assertCanCreate(self.home, FAQPage, nested_form_data(
            {'title': 'FAQ Test Page',
             'body': streamfield([
                 ('heading', 'Testing!')
             ])}
        ))