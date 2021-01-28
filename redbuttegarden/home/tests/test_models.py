from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import nested_form_data, streamfield, inline_formset, rich_text

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

    def test_can_create_general(self):
        self.assertCanCreate(self.home, GeneralPage, nested_form_data(
            {'title': 'General Test Page',
             'body': streamfield([
                 ('html', '<p>Testing!</p>')
             ])}
        ))

    def test_can_create_general_index(self):
        self.assertCanCreate(self.home, GeneralIndexPage, nested_form_data(
            {'title': 'General Index Test Page',
             'body': streamfield([])}
        ))

    def test_can_create_home(self):
        self.assertCanCreate(self.home, HomePage, nested_form_data(
            {'title': 'Home Test Page',
             'event_slides': inline_formset([])}
        ))

    def test_can_create_plant_collections(self):
        self.assertCanCreate(self.home, PlantCollectionsPage, nested_form_data(
            {'title': 'Plant Collections Test Page',
             'intro': rich_text('Testing!'),
             'more_info_modal': rich_text('Testing!'),
             'plant_collections': inline_formset([])}
        ))

    def test_can_create_two_col_general(self):
        self.assertCanCreate(self.home, TwoColumnGeneralPage, nested_form_data(
            {'title': 'Two Column General Test Page',
             'body': streamfield([])}
        ))
