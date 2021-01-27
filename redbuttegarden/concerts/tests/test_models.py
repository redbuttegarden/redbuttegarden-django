from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from concerts.models import ConcertPage, DonorPackagePage


class ConcertPageTests(WagtailPageTests):
    def test_can_create_concert(self):
        self.assertCanCreateAt(Page, ConcertPage)

    def test_can_create_donor_package(self):
        self.assertCanCreateAt(Page, DonorPackagePage)