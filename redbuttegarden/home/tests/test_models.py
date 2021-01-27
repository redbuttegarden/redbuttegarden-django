from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

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