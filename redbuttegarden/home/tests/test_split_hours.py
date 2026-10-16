"""Regression coverage for split hours validation and the public hours API."""

import json
from datetime import time

from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import RequestFactory, SimpleTestCase, TestCase
from wagtail.admin.telepath import JSContext
from wagtail.models import Locale, Page
from wagtail.models.i18n import get_supported_content_language_variant

from home.hour_blocks import OpeningPeriodBlock
from home.models import HomePage, RBGHours, RBGHoursOrderable
from home.views import get_hours


def period(start: time | None, end: time | None, label: str = "") -> tuple:
    """Build an additional-hours block with editor-equivalent typed values."""

    return ("opening_period", {"garden_open": start, "garden_close": end, "label": label})


class SplitHoursValidationTests(SimpleTestCase):
    """Enforce same-day periods without breaking message-only snippets."""

    def test_editor_widget_serialization_preserves_error_associations(self) -> None:
        block = OpeningPeriodBlock()
        for name in ["garden_open", "garden_close", "label"]:
            with self.subTest(field=name):
                packed = JSContext().pack(block.child_blocks[name].field.widget)
                self.assertIn('aria-describedby="__ID__-errors"', packed["_args"][0])

    def test_legacy_and_message_only_schedules(self) -> None:
        hours = RBGHours(name="Legacy", garden_open=time(9), garden_close=time(17))
        hours.full_clean()
        self.assertEqual(hours.get_time_ranges(), [
            {"garden_open": "09:00", "garden_close": "17:00", "label": ""},
        ])
        closed = RBGHours(name="Closed", additional_message="Closed for maintenance")
        closed.full_clean()
        self.assertEqual(closed.get_time_ranges(), [])

    def test_primary_endpoints_must_be_paired(self) -> None:
        for start, end, missing in [(time(9), None, "garden_close"), (None, time(17), "garden_open")]:
            with self.subTest(missing=missing), self.assertRaises(ValidationError) as caught:
                RBGHours(name="Invalid", garden_open=start, garden_close=end).full_clean()
            self.assertIn(missing, caught.exception.message_dict)

    def test_primary_label_requires_primary_hours(self) -> None:
        with self.assertRaises(ValidationError) as caught:
            RBGHours(name="Invalid", garden_hours_label="Daytime").full_clean()
        self.assertIn("garden_hours_label", caught.exception.message_dict)

    def test_primary_closing_must_follow_opening(self) -> None:
        for end in [time(9), time(8)]:
            with self.subTest(end=end), self.assertRaises(ValidationError) as caught:
                RBGHours(name="Invalid", garden_open=time(9), garden_close=end).full_clean()
            self.assertIn("garden_close", caught.exception.message_dict)

    def test_additional_periods_require_both_endpoints_and_forward_order(self) -> None:
        for start, end in [(None, time(20)), (time(18), None), (time(18), time(18)), (time(20), time(18))]:
            with self.subTest(start=start, end=end), self.assertRaises(ValidationError) as caught:
                RBGHours(name="Invalid", additional_hours=[period(start, end)]).full_clean()
            self.assertIn("additional_hours", caught.exception.message_dict)

    def test_periods_display_chronologically_and_preserve_plain_labels(self) -> None:
        hours = RBGHours(
            name="Split", garden_open=time(18), garden_close=time(20),
            garden_hours_label="Garden After Dark",
            additional_hours=[period(time(9), time(17), '<img src=x onerror="alert(1)">')],
        )
        hours.full_clean()
        self.assertEqual(hours.get_time_ranges(), [
            {"garden_open": "09:00", "garden_close": "17:00", "label": '<img src=x onerror="alert(1)">'},
            {"garden_open": "18:00", "garden_close": "20:00", "label": "Garden After Dark"},
        ])

    def test_adjacent_periods_and_additional_only_schedule_are_allowed(self) -> None:
        hours = RBGHours(name="Adjacent", additional_hours=[
            period(time(9), time(17)), period(time(17), time(20)),
        ])
        hours.full_clean()
        self.assertEqual(len(hours.get_time_ranges()), 2)

    def test_primary_and_additional_overlap_is_rejected(self) -> None:
        hours = RBGHours(name="Overlap", garden_open=time(9), garden_close=time(17),
                         additional_hours=[period(time(16), time(20))])
        with self.assertRaises(ValidationError) as caught:
            hours.full_clean()
        self.assertIn("additional_hours", caught.exception.message_dict)

    def test_overlap_between_additional_periods_is_rejected(self) -> None:
        hours = RBGHours(name="Overlap", additional_hours=[
            period(time(9), time(17)), period(time(16), time(20)),
        ])
        with self.assertRaises(ValidationError):
            hours.full_clean()

    def test_validation_preserves_seconds_when_checking_overlap(self) -> None:
        hours = RBGHours(name="Seconds", garden_open=time(9), garden_close=time(17, 0, 45),
                         additional_hours=[period(time(17, 0, 15), time(20))])
        with self.assertRaises(ValidationError):
            hours.full_clean()

    def test_labels_are_limited_to_200_characters(self) -> None:
        for kwargs in [
            {"garden_hours_label": "x" * 201, "garden_open": time(9), "garden_close": time(17)},
            {"additional_hours": [period(time(18), time(20), "x" * 201)]},
        ]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValidationError):
                RBGHours(name="Invalid", **kwargs).full_clean()


class SplitHoursAPITests(TestCase):
    """Keep legacy response fields, ordering, and bounded snippet fetching."""

    def setUp(self) -> None:
        Locale.objects.get_or_create(
            language_code=get_supported_content_language_variant(settings.LANGUAGE_CODE)
        )
        root = Page.get_first_root_node()
        if root is None:
            root = Page.add_root(instance=Page(title="Root", slug="root"))
        self.page = root.add_child(instance=HomePage(title="Split hours test", slug="split-hours"))
        self.request = RequestFactory().get("/api/hours/", HTTP_X_REQUESTED_WITH="XMLHttpRequest")

    def test_split_hours_persist_and_api_adds_ranges_without_changing_legacy_fields(self) -> None:
        hours = RBGHours.objects.create(
            name="Event", garden_open=time(9), garden_close=time(17),
            garden_hours_label="Regular visitation",
            additional_hours=[period(time(18), time(20), "Garden After Dark")],
        )
        RBGHoursOrderable.objects.create(page=self.page, hours=hours, sort_order=0)
        hours.refresh_from_db()
        self.assertEqual(hours.additional_hours[0].value["garden_open"], time(18))
        with self.assertNumQueries(2):
            response = get_hours(self.request, self.page.pk)
        data = json.loads(response.content)["0"]
        self.assertEqual(data["garden_open"], "9:00")
        self.assertEqual(data["garden_close"], "17:00")
        self.assertEqual(data["time_ranges"], [
            {"garden_open": "09:00", "garden_close": "17:00", "label": "Regular visitation"},
            {"garden_open": "18:00", "garden_close": "20:00", "label": "Garden After Dark"},
        ])
        self.assertIn("additional_message", data)
        self.assertEqual(data["days_of_week"], list(range(7)))

    def test_snippet_order_is_preserved_and_query_count_does_not_grow(self) -> None:
        for sort_order, name in [(2, "Fallback"), (0, "Override"), (1, "Second")]:
            hours = RBGHours.objects.create(name=name)
            RBGHoursOrderable.objects.create(page=self.page, hours=hours, sort_order=sort_order)
        with self.assertNumQueries(2):
            response = get_hours(self.request, self.page.pk)
        data = json.loads(response.content)
        self.assertEqual([item["name"] for item in data.values()], ["Override", "Second", "Fallback"])
        self.assertEqual(data["0"]["time_ranges"], [])

    def test_no_attached_hours_returns_no_content(self) -> None:
        self.assertEqual(get_hours(self.request, self.page.pk).status_code, 204)

    def test_missing_page_and_non_ajax_requests(self) -> None:
        self.assertEqual(get_hours(self.request, 99999999).status_code, 404)
        self.assertEqual(get_hours(RequestFactory().get("/api/hours/"), self.page.pk).status_code, 204)
