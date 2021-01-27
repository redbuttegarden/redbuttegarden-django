from wagtail.core.models import Page
from wagtail.tests.utils import WagtailPageTests

from journal.models import JournalPage, JournalIndexPage


class JournalPageTests(WagtailPageTests):
    def test_cannot_create_journal(self):
        """
        JournalPage can only be created under JournalIndexPage.
        """
        self.assertCanNotCreateAt(Page, JournalPage)

    def test_can_create_journal_index(self):
        self.assertCanCreateAt(Page, JournalIndexPage)