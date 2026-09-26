"""Wagtail admin customizations for journal pages."""

from __future__ import annotations

import django_filters
from wagtail import hooks
from wagtail.admin.ui.tables import DateColumn
from wagtail.admin.viewsets.pages import PageViewSet

from journal.models import JournalCategory, JournalIndexPage, JournalPage


class JournalPageFilterSet(PageViewSet.filterset_class):
    """Provide category and publication-date filters for journal pages."""

    categories = django_filters.ModelMultipleChoiceFilter(
        field_name="categories",
        queryset=JournalCategory.objects.all(),
        distinct=True,
        label="Categories",
    )
    date = django_filters.DateTimeFromToRangeFilter(label="Post date")

    class Meta:
        model = JournalPage
        fields = ["categories", "date"]


class JournalPageViewSet(PageViewSet):
    """Customize the page explorer beneath journal index pages."""

    model = JournalPage
    parent_models = [JournalIndexPage]
    columns = PageViewSet.columns + [
        DateColumn("date", label="Post date", sort_key="date"),
    ]
    filterset_class = JournalPageFilterSet
    ordering = ("-date", "title")


@hooks.register("register_admin_viewset")
def register_journal_page_viewset() -> JournalPageViewSet:
    """Register the permission-aware journal explorer customization."""

    return JournalPageViewSet()
