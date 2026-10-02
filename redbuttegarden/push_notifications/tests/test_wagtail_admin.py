"""Editor-facing Wagtail behavior for Push Notifications."""

from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.http import HttpResponse
from django.template.loader import get_template
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone

from push_notifications.forms import PushNotificationForm
from push_notifications.models import PushNotification
from push_notifications.wagtail_hooks import (
    PushNotificationEditView,
    PushNotificationViewSet,
)


def form_data() -> dict[str, str]:
    """Return valid editor-owned notification input."""

    return {
        "title": "Spring bloom alert",
        "body": "The cherry blossoms are starting to bloom.",
        "icon_path": "",
        "destination_path": "/blooms",
        "scheduled_time": "",
        # A forged raw lifecycle state is ignored because status is not a
        # ModelForm field; the selected server-side action owns the transition.
        "status": PushNotification.Status.SENT,
    }


def test_viewset_is_a_top_level_notifications_menu_item() -> None:
    """Notifications are directly available from Wagtail's main sidebar."""

    viewset = PushNotificationViewSet()

    assert viewset.add_to_admin_menu is True
    assert viewset.menu_label == "Notifications"
    assert viewset.menu_icon == "mail"


@pytest.mark.django_db
def test_wagtail_create_view_requires_an_authenticated_editor(client: Client) -> None:
    """The dedicated top-level view keeps Wagtail's authentication boundary."""

    response = client.post(reverse("wagtailsnippets_push_notifications_pushnotification:add"), form_data())

    assert response.status_code == 302
    assert "/admin/login/" in response.url


@pytest.mark.django_db
def test_wagtail_create_view_requires_csrf_for_an_authorized_editor() -> None:
    """The custom template/view does not bypass Django's CSRF protection."""

    user = get_user_model().objects.create_user(
        username="notification-editor",
        email="notifications@example.test",
        password="password",
        is_staff=True,
    )
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="push_notifications",
            content_type__model="pushnotification",
            codename="add_pushnotification",
        )
    )
    client = Client(enforce_csrf_checks=True)
    client.force_login(user)

    response = client.post(reverse("wagtailsnippets_push_notifications_pushnotification:add"), form_data())

    assert response.status_code == 403


@pytest.mark.django_db
def test_wagtail_edit_view_requires_change_permission(client: Client) -> None:
    """An editor with only add permission cannot alter an existing broadcast."""

    notification = PushNotification.objects.create(title="Draft", body="Not sent")
    user = get_user_model().objects.create_user(
        username="add-only-notification-editor",
        email="add-only@example.test",
        password="password",
        is_staff=True,
    )
    user.user_permissions.add(
        Permission.objects.get(
            content_type__app_label="push_notifications",
            content_type__model="pushnotification",
            codename="add_pushnotification",
        )
    )
    client.force_login(user)

    response = client.post(
        reverse("wagtailsnippets_push_notifications_pushnotification:edit", args=[notification.pk]),
        {**form_data(), "action-send-now": "1"},
    )

    assert response.status_code == 302
    notification.refresh_from_db()
    assert notification.status == PushNotification.Status.DRAFT


def test_editor_form_hides_status_and_explains_each_field() -> None:
    """Editors see only meaningful content and scheduling controls."""

    form = PushNotificationForm()

    assert "status" not in form.fields
    assert form.fields["title"].help_text == (
        "The header text shown at the top of the push notification (e.g., 'Spring Bloom Alert!')."
    )
    assert "1-2 short sentences" in form.fields["body"].help_text
    assert "Must start with a forward slash" in form.fields["destination_path"].help_text
    assert form.fields["icon_path"].required is False
    assert "checks for due notifications every 5 minutes" in form.fields["scheduled_time"].help_text


@pytest.mark.django_db
def test_terminal_notification_form_is_read_only() -> None:
    """System-owned lifecycle states cannot be changed through editor fields."""

    notification = PushNotification.objects.create(
        title="Sent bloom alert",
        body="Already delivered.",
        status=PushNotification.Status.SENT,
    )
    form = PushNotificationForm(instance=notification)

    assert all(field.disabled for field in form.fields.values())
    assert "status" not in form.fields


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("action", "expected_status", "has_schedule"),
    [
        ("action-save-draft", PushNotification.Status.DRAFT, False),
        ("action-schedule", PushNotification.Status.SCHEDULED, True),
        ("action-send-now", PushNotification.Status.SCHEDULED, True),
    ],
)
def test_editor_actions_apply_only_editor_owned_states(
    monkeypatch: pytest.MonkeyPatch,
    action: str,
    expected_status: str,
    has_schedule: bool,
) -> None:
    """Draft, schedule, and send-now buttons set the server-owned workflow safely."""

    notification = PushNotification.objects.create(title="Bloom", body="Now open")
    data = form_data()
    if action == "action-schedule":
        data["scheduled_time"] = (timezone.now() + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
    form = PushNotificationForm(data=data, instance=notification)
    assert form.is_valid()
    view = PushNotificationEditView()
    view.request = RequestFactory().post("/admin/", {action: "1"})
    monkeypatch.setattr(
        "wagtail.snippets.views.snippets.EditView.form_valid",
        lambda self, bound_form: HttpResponse(),
    )

    view.form_valid(form)

    assert form.instance.status == expected_status
    assert (form.instance.scheduled_time is not None) is has_schedule


@pytest.mark.django_db
def test_terminal_notification_rejects_forged_editor_action(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A crafted POST cannot reschedule a sent notification."""

    notification = PushNotification.objects.create(
        title="Sent bloom alert",
        body="Already delivered.",
        status=PushNotification.Status.SENT,
    )
    form = PushNotificationForm(data=form_data(), instance=notification)
    assert form.is_valid()
    view = PushNotificationEditView()
    view.request = RequestFactory().post("/admin/", {"action-send-now": "1"})
    monkeypatch.setattr(view, "form_invalid", lambda bound_form: HttpResponse(status=400))

    response = view.form_valid(form)

    assert response.status_code == 400
    notification.refresh_from_db()
    assert notification.status == PushNotification.Status.SENT


@pytest.mark.django_db(transaction=True)
def test_stale_editor_post_cannot_overwrite_a_scheduler_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A scheduler claim made after page load locks the stale editor form."""

    notification = PushNotification.objects.create(
        title="Scheduled bloom alert",
        body="Soon.",
        status=PushNotification.Status.SCHEDULED,
        scheduled_time=timezone.now() + timedelta(minutes=10),
    )
    form = PushNotificationForm(
        data={**form_data(), "scheduled_time": (timezone.now() + timedelta(minutes=20)).strftime("%Y-%m-%d %H:%M:%S")},
        instance=notification,
    )
    assert form.is_valid()
    PushNotification.objects.filter(pk=notification.pk).update(status=PushNotification.Status.SENDING)

    view = PushNotificationEditView()
    view.request = RequestFactory().post("/admin/", {"action-schedule": "1"})
    parent_save_called = False

    def parent_form_valid(*args: object, **kwargs: object) -> HttpResponse:
        nonlocal parent_save_called
        parent_save_called = True
        return HttpResponse()

    monkeypatch.setattr("wagtail.snippets.views.snippets.EditView.form_valid", parent_form_valid)
    monkeypatch.setattr(view, "form_invalid", lambda bound_form: HttpResponse(status=400))

    response = view.form_valid(form)

    assert response.status_code == 400
    assert parent_save_called is False
    notification.refresh_from_db()
    assert notification.status == PushNotification.Status.SENDING


def test_editor_templates_explain_delivery_and_opted_in_audience() -> None:
    """Both editor views include the non-technical delivery guidance."""

    guidance = get_template("push_notifications/wagtail/includes/editor_guidance.html").template.source
    create = get_template("push_notifications/wagtail/create.html").template.source
    edit = get_template("push_notifications/wagtail/edit.html").template.source

    assert "How sending works" in guidance
    assert "within 5 minutes" in guidance
    assert "opted in to receive browser notifications" in guidance
    assert "editor_guidance.html" in create
    assert "editor_guidance.html" in edit
