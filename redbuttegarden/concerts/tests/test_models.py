from django.contrib.auth.models import Group
from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests, get_user_model
from wagtail.tests.utils.form_data import nested_form_data, streamfield

from concerts.models import ConcertPage, DonorPackagePage, DonorSchedulePage


class ConcertPageTests(WagtailPageTests):
    def test_can_create_concert(self):
        self.assertCanCreateAt(Page, ConcertPage)

    def test_can_create_donor_package(self):
        self.assertCanCreateAt(Page, DonorPackagePage)

    def test_can_create_donor_schedule(self):
        self.assertCanCreateAt(Page, DonorSchedulePage)


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
                                  'body': streamfield([])  # Need to pass empty list to avoid ValidationError
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

    def test_can_create_donor_schedule(self):
        self.assertCanCreate(self.home, DonorSchedulePage,
                             nested_form_data(
                                 {'title': 'Donor Schedule Test Page',
                                  'body': streamfield([
                                      ('table', '{\"data\": [[\"ARTIST\", \"FULL PACKAGE\", \"OPENER A\", \"OPENER B\"], [\"BELA FLECK AND THE FLECKTONES WITH BILLY STRINGS\", \"YES\", \"NO\", \"YES\"], [\"LITTLE FEAT\", \"YES\", \"YES\", \"NO\"]], \"cell\": [], \"first_row_is_table_header\": true, \"first_col_is_header\": false, \"table_caption\": \"2019 Donor Season Ticket Packages\"}'),
                                  ])}
                             ))
