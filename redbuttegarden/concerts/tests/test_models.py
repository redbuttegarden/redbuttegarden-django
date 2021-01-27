from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import inline_formset, nested_form_data, streamfield

from concerts.models import ConcertPage, DonorPackagePage


class ConcertPageTests(WagtailPageTests):
    def test_can_create_concert(self):
        self.assertCanCreateAt(Page, ConcertPage)

    def test_can_create_donor_package(self):
        self.assertCanCreateAt(Page, DonorPackagePage)


class ConcertPageInstanceTests(WagtailPageTests):
    def setUp(self):
        self.home = Page.objects.get(slug='home')
        self.user = get_user_model().objects.create_user('Test User', 'test@email.com', 'password')
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_can_create_concert(self):
        self.assertCanCreate(self.home, ConcertPage,
                             nested_form_data(
                                 {'title': 'Concert Test Page',
                                  'concerts': inline_formset([])  # Need to pass empty list to avoid ValidationError
                                  }
                             ))

    def test_can_create_donor_package(self):
        self.assertCanCreate(self.home, DonorPackagePage,
                             nested_form_data(
                                 {'title': 'Donor Package Test Page',
                                  'body': streamfield([
                                      ('html', '<p>Testing!</p>')
                                  ])}
                             ))
