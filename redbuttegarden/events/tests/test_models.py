from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from events.models import EventIndexPage, EventPage, EventGeneralPage


class EventPageTests(WagtailPageTests):
    def test_can_create_event_index(self):
        self.assertCanCreateAt(Page, EventIndexPage)

    def test_cannot_create_event(self):
        """
        Event pages can only be created under EventIndexPages or GeneralIndexPages
        """
        self.assertCanNotCreateAt(Page, EventPage)

    def test_canot_create_event_general(self):
        """
        EventGeneral pages can only be created under EventIndexPages or GeneralIndexPages
        """
        self.assertCanNotCreateAt(Page, EventGeneralPage)