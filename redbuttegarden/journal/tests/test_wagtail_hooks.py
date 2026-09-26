from django.test import TestCase

from journal.models import JournalIndexPage, JournalPage
from journal.wagtail_hooks import (
    JournalPageFilterSet,
    JournalPageViewSet,
    register_journal_page_viewset,
)


class JournalPageViewSetTests(TestCase):
    """Verify the journal explorer customization stays narrowly scoped."""

    def test_viewset_configuration(self) -> None:
        viewset = register_journal_page_viewset()

        self.assertIsInstance(viewset, JournalPageViewSet)
        self.assertIs(viewset.model, JournalPage)
        self.assertEqual(viewset.parent_models, [JournalIndexPage])
        self.assertEqual(viewset.ordering, ("-date", "title"))
        self.assertIs(viewset.filterset_class, JournalPageFilterSet)
        self.assertEqual(viewset.columns[-1].name, "date")

    def test_filterset_exposes_category_and_date_range(self) -> None:
        filters = JournalPageFilterSet.base_filters

        self.assertIn("categories", filters)
        self.assertTrue(filters["categories"].distinct)
        self.assertIn("date", filters)
