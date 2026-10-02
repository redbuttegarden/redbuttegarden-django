"""Focused regression tests for Web Push persistence and public endpoints."""

from __future__ import annotations

import base64
import json
import sys
from types import SimpleNamespace
from datetime import timedelta

import pytest
from django.core.exceptions import ValidationError
from django.middleware.csrf import _get_new_csrf_string
from django.http import HttpResponse
from django.test import RequestFactory
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from push_notifications.models import PushDelivery, PushNotification, PushSubscriber
from push_notifications.services import record_notification_click, register_subscription


def _encoded(size: int) -> str:
    return base64.urlsafe_b64encode(b"x" * size).decode().rstrip("=")


def subscription_payload(endpoint: str = "https://fcm.googleapis.com/subscription") -> dict[str, object]:
    """Return a browser-shaped, valid subscription payload."""

    return {"endpoint": endpoint, "expirationTime": None, "keys": {"p256dh": _encoded(65), "auth": _encoded(16)}}


def create_subscriber(endpoint: str = "https://fcm.googleapis.com/subscription") -> PushSubscriber:
    """Create a valid stored subscription without the browser wrapper object."""

    return PushSubscriber.objects.create(endpoint=endpoint, p256dh=_encoded(65), auth=_encoded(16))


def test_preferences_page_has_a_single_page_specific_description(client: Client) -> None:
    """The public settings page has clear SEO metadata and retains its JS hooks."""

    response = client.get(reverse("push_notifications:preferences"))
    content = response.content.decode()

    assert response.status_code == 200
    assert response["Cache-Control"] == "private, no-store"
    assert "<title>\n        Notification preferences | Red Butte Garden" in content
    assert content.count('<meta name="description"') == 1
    assert (
        'content="Manage browser notifications from Red Butte Garden for seasonal updates, '
        'bloom alerts, and upcoming Garden events."'
    ) in content
    assert "push_notifications/css/preferences" in content
    assert 'id="enable-push"' in content
    assert 'id="disable-push"' in content
    assert 'id="push-preferences-status"' in content


@pytest.mark.django_db
def test_registration_upserts_and_reactivates_subscription() -> None:
    """Registration does not create duplicate endpoint records."""

    first = register_subscription(subscription_payload())
    PushSubscriber.objects.filter(pk=first.pk).update(is_active=False, unsubscribed_at=timezone.now())

    second = register_subscription(subscription_payload())

    assert first.pk == second.pk
    assert PushSubscriber.objects.count() == 1
    assert second.is_active is True
    assert second.unsubscribed_at is None


@pytest.mark.django_db
def test_notification_rejects_external_destination() -> None:
    """Notification navigation cannot leave the Garden origin."""

    notification = PushNotification(title="Bloom", body="Now open", destination_path="https://example.test/")

    with pytest.raises(ValidationError):
        notification.full_clean()

    notification.destination_path = "/"
    notification.status = PushNotification.Status.SCHEDULED
    notification.scheduled_time = timezone.now() - timedelta(minutes=1)
    with pytest.raises(ValidationError):
        notification.full_clean()

    notification.destination_path = "/\\evil.example"
    with pytest.raises(ValidationError):
        notification.full_clean()


@pytest.mark.django_db
def test_click_token_is_counted_once() -> None:
    """A replayed worker click does not inflate aggregate analytics."""

    subscriber = create_subscriber()
    notification = PushNotification.objects.create(title="Bloom", body="Now open")
    delivery = PushDelivery.objects.create(
        notification=notification,
        subscriber=subscriber,
        subscriber_id_at_dispatch=subscriber.pk,
        status=PushDelivery.Status.ACCEPTED,
    )
    from push_notifications.services import _signed_click_token

    token = _signed_click_token(delivery)
    assert record_notification_click(token) is True
    assert record_notification_click(token) is False
    notification.refresh_from_db()
    assert notification.click_count == 1


@pytest.mark.django_db
def test_subscription_endpoint_requires_csrf(client: Client) -> None:
    """Public subscription writes retain Django CSRF protection."""

    csrf_client = Client(enforce_csrf_checks=True)
    response = csrf_client.post(
        reverse("push_notifications:subscriptions"),
        data=json.dumps(subscription_payload()),
        content_type="application/json",
    )

    assert response.status_code == 403


@pytest.mark.django_db
def test_subscription_endpoint_accepts_valid_csrf_request(settings) -> None:
    """A same-origin browser can persist a valid subscription."""

    settings.PUSH_ORIGIN_HEADER_SECRET = "test-origin-secret"
    client = Client(enforce_csrf_checks=True)
    csrf_token = _get_new_csrf_string()
    client.cookies["csrftoken"] = csrf_token
    response = client.post(
        reverse("push_notifications:subscriptions"),
        data=json.dumps(subscription_payload()),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=csrf_token,
        HTTP_X_RBG_PUSH_ORIGIN="test-origin-secret",
    )

    assert response.status_code == 204
    assert response["Cache-Control"] == "no-store"
    assert PushSubscriber.objects.count() == 1


@pytest.mark.django_db
def test_subscription_rejects_untrusted_provider_and_invalid_key() -> None:
    """The public registration boundary rejects SSRF and malformed key inputs."""

    payload = subscription_payload("https://127.0.0.1/private")
    with pytest.raises(ValidationError):
        register_subscription(payload)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    [
        "https://fcm.googleapis.com:8443/subscription",
        "https://fcm.googleapis.com:invalid-port/subscription",
    ],
)
def test_subscription_rejects_non_default_or_malformed_https_ports(endpoint: str) -> None:
    """Subscriptions may use HTTPS only on its default provider port."""

    with pytest.raises(ValidationError):
        register_subscription(subscription_payload(endpoint))


@pytest.mark.django_db
def test_subscription_accepts_explicit_default_https_port() -> None:
    """An explicit HTTPS default port remains a valid browser endpoint."""

    subscriber = register_subscription(subscription_payload("https://fcm.googleapis.com:443/subscription"))

    assert subscriber.endpoint == "https://fcm.googleapis.com:443/subscription"
    payload = subscription_payload()
    payload["keys"]["auth"] = "not+url-safe"
    with pytest.raises(ValidationError):
        register_subscription(payload)


@pytest.mark.django_db
def test_unsubscribed_subscription_is_retained_until_cleanup() -> None:
    """Voluntary opt-out preserves limited retention data until the cleanup window."""

    subscriber = create_subscriber()
    subscriber.is_active = False
    subscriber.unsubscribed_at = timezone.now() - timedelta(days=91)
    subscriber.save()
    from push_notifications.services import purge_inactive_subscribers

    assert purge_inactive_subscribers() == 1
    assert not PushSubscriber.objects.exists()


@pytest.mark.django_db
def test_dispatch_records_provider_acceptance(monkeypatch: pytest.MonkeyPatch, settings) -> None:
    """A claimed notification sends its delivery once and updates aggregate metrics."""

    settings.VAPID_PRIVATE_KEY = "test-key"
    settings.VAPID_CLAIMS_SUBJECT = "mailto:push@example.test"
    calls: list[dict[str, object]] = []
    monkeypatch.setitem(
        sys.modules,
        "pywebpush",
        SimpleNamespace(WebPushException=Exception, webpush=lambda **kwargs: calls.append(kwargs)),
    )
    create_subscriber()
    notification = PushNotification.objects.create(
        title="Bloom", body="Now open", status=PushNotification.Status.SENDING,
        dispatch_lease_token=__import__("uuid").uuid4(),
        dispatch_lease_expires_at=timezone.now() + timedelta(minutes=5),
    )
    from push_notifications.services import dispatch_notification

    result = dispatch_notification(notification.pk, notification.dispatch_lease_token, deadline_seconds=1)

    notification.refresh_from_db()
    assert len(calls) == 1
    assert result.accepted == 1
    assert notification.status == PushNotification.Status.SENT
    assert notification.accepted_count == 1


@pytest.mark.django_db
def test_claim_delivery_batch_locks_only_delivery_rows() -> None:
    """Claim a delivery without locking its nullable subscriber outer join."""

    subscriber = create_subscriber()
    notification = PushNotification.objects.create(title="Bloom", body="Now open")
    PushDelivery.objects.create(
        notification=notification,
        subscriber=subscriber,
        subscriber_id_at_dispatch=subscriber.pk,
    )
    from push_notifications.services import _claim_delivery_batch

    claimed = _claim_delivery_batch(notification)

    assert len(claimed) == 1
    assert claimed[0].status == PushDelivery.Status.SENDING
    assert claimed[0].dispatch_lease_token is not None
    assert claimed[0].subscriber == subscriber
    assert claimed[0].notification == notification


@pytest.mark.django_db
def test_dispatch_removes_expired_subscription(monkeypatch: pytest.MonkeyPatch, settings) -> None:
    """A 410 provider response permanently removes the invalid endpoint."""

    settings.VAPID_PRIVATE_KEY = "test-key"
    settings.VAPID_CLAIMS_SUBJECT = "mailto:push@example.test"

    class ProviderError(Exception):
        """Provider exception carrying the HTTP response status used by pywebpush."""

        response = SimpleNamespace(status_code=410)

    monkeypatch.setitem(
        sys.modules,
        "pywebpush",
        SimpleNamespace(WebPushException=ProviderError, webpush=lambda **kwargs: (_ for _ in ()).throw(ProviderError())),
    )
    subscriber = create_subscriber()
    notification = PushNotification.objects.create(
        title="Bloom", body="Now open", status=PushNotification.Status.SENDING,
        dispatch_lease_token=__import__("uuid").uuid4(),
        dispatch_lease_expires_at=timezone.now() + timedelta(minutes=5),
    )
    from push_notifications.services import dispatch_notification

    result = dispatch_notification(notification.pk, notification.dispatch_lease_token, deadline_seconds=1)

    assert result.expired == 1
    assert not PushSubscriber.objects.filter(pk=subscriber.pk).exists()
    assert PushDelivery.objects.get(notification=notification).subscriber is None


@pytest.mark.django_db
def test_wagtail_send_now_action_queues_scheduler_work(monkeypatch: pytest.MonkeyPatch) -> None:
    """The editor action never sends inline; it queues the scheduler-owned state."""

    from push_notifications.forms import PushNotificationForm
    from push_notifications.wagtail_hooks import PushNotificationEditView
    from wagtail.snippets.views.snippets import EditView

    notification = PushNotification.objects.create(title="Bloom", body="Now open")
    form = PushNotificationForm(
        data={
            "title": "Bloom",
            "body": "Now open",
            "icon_path": "/static/redbuttegarden/img/favicon/icon-192x192.png",
            "destination_path": "/",
            "status": PushNotification.Status.DRAFT,
        },
        instance=notification,
    )
    assert form.is_valid()
    view = PushNotificationEditView()
    view.request = RequestFactory().post("/admin/", {"action-send-now": "1"})
    monkeypatch.setattr(EditView, "form_valid", lambda self, bound_form: HttpResponse())

    view.form_valid(form)

    assert form.instance.status == PushNotification.Status.SCHEDULED
    assert form.instance.scheduled_time is not None
