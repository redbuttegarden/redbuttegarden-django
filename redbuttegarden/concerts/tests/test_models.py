from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from concerts.models import ConcertPage


class ConcertPageTests(WagtailPageTests):
    def test_can_create_concert(self):
        self.assertCanCreateAt(Page, ConcertPage)