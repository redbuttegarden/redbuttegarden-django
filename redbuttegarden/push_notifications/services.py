"""Business logic for safely registering, dispatching, and measuring Web Push."""

from __future__ import annotations

import json
import logging
import ipaddress
import re
import time
import uuid
from base64 import urlsafe_b64decode
from dataclasses import dataclass
from datetime import timedelta
from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.core import signing
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, F
from django.utils import timezone

from .models import PushDelivery, PushNotification, PushRequestRateLimit, PushSubscriber

logger = logging.getLogger(__name__)
CLICK_TOKEN_SALT = "push_notifications.click"
LEASE_DURATION = timedelta(minutes=15)
DISPATCH_BATCH_SIZE = 100
DELIVERY_LEASE_DURATION = timedelta(minutes=5)
URLSAFE_BASE64_RE = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass(frozen=True)
class DispatchResult:
    """Aggregate result of one completed notification dispatch."""

    accepted: int
    failed: int
    expired: int


def _validate_endpoint(endpoint: object) -> str:
    """Validate an endpoint before it can be persisted or used for egress."""

    if not isinstance(endpoint, str):
        raise ValidationError("The subscription endpoint is invalid.")
    try:
        parsed = urlparse(endpoint)
        port = parsed.port
    except ValueError as exc:
        raise ValidationError("The subscription endpoint is invalid.") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme != "https"
        or not host
        or parsed.username
        or parsed.password
        or (port is not None and port != 443)
        or len(endpoint) > 2048
    ):
        raise ValidationError("The subscription endpoint is invalid.")
    try:
        ipaddress.ip_address(host)
        raise ValidationError("The subscription endpoint is invalid.")
    except ValueError:
        pass
    if not any(host == allowed or host.endswith(f".{allowed}") for allowed in settings.PUSH_ALLOWED_ENDPOINT_HOSTS):
        raise ValidationError("The subscription endpoint is not from an allowed push provider.")
    return endpoint


def register_subscription(payload: dict[str, Any]) -> PushSubscriber:
    """Validate and upsert an anonymous browser Web Push subscription."""

    endpoint = payload.get("endpoint")
    keys = payload.get("keys")
    if set(payload) - {"endpoint", "expirationTime", "keys"}:
        raise ValidationError("The subscription contains unsupported fields.")
    if not isinstance(keys, dict):
        raise ValidationError("A subscription endpoint and keys are required.")
    endpoint = _validate_endpoint(endpoint)
    if set(keys) != {"p256dh", "auth"}:
        raise ValidationError("The subscription keys are invalid.")
    p256dh = keys.get("p256dh")
    auth = keys.get("auth")
    if not isinstance(p256dh, str) or not 20 <= len(p256dh) <= 256:
        raise ValidationError("The p256dh subscription key is invalid.")
    if not isinstance(auth, str) or not 8 <= len(auth) <= 128:
        raise ValidationError("The auth subscription key is invalid.")
    if not URLSAFE_BASE64_RE.fullmatch(p256dh) or not URLSAFE_BASE64_RE.fullmatch(auth):
        raise ValidationError("The subscription keys are invalid.")
    try:
        # Browser subscriptions are URL-safe base64 without required padding.
        decoded_p256dh = urlsafe_b64decode(p256dh + "=" * (-len(p256dh) % 4))
        decoded_auth = urlsafe_b64decode(auth + "=" * (-len(auth) % 4))
    except ValueError as exc:
        raise ValidationError("The subscription keys are invalid.") from exc
    if len(decoded_p256dh) != 65 or len(decoded_auth) != 16:
        raise ValidationError("The subscription keys are invalid.")

    now = timezone.now()
    subscriber, _ = PushSubscriber.objects.update_or_create(
        endpoint=endpoint,
        defaults={
            "p256dh": p256dh,
            "auth": auth,
            "is_active": True,
            "last_seen_at": now,
            "unsubscribed_at": None,
        },
    )
    return subscriber


def deactivate_subscription(endpoint: object) -> None:
    """Deactivate a submitted subscription without revealing whether it exists."""

    PushSubscriber.objects.filter(endpoint=_validate_endpoint(endpoint)).update(
        is_active=False,
        unsubscribed_at=timezone.now(),
    )


def _signed_click_token(delivery: PushDelivery) -> str:
    """Return a tamper-evident, time-independent token for a delivery click."""

    return signing.dumps(str(delivery.click_token), salt=CLICK_TOKEN_SALT, compress=True)


def record_notification_click(token: str) -> bool:
    """Record one accepted delivery click and return whether it was newly counted."""

    try:
        click_token = signing.loads(token, salt=CLICK_TOKEN_SALT)
        delivery_id = uuid.UUID(click_token)
    except (signing.BadSignature, TypeError, ValueError):
        return False

    with transaction.atomic():
        delivery = (
            PushDelivery.objects.select_for_update()
            .select_related("notification")
            .filter(click_token=delivery_id, status=PushDelivery.Status.ACCEPTED)
            .first()
        )
        if not delivery or delivery.clicked_at:
            return False
        delivery.clicked_at = timezone.now()
        delivery.save(update_fields=["clicked_at", "updated_at"])
        PushNotification.objects.filter(pk=delivery.notification_id).update(
            click_count=F("click_count") + 1
        )
    return True


def claim_due_notifications(limit: int = 10) -> list[tuple[uuid.UUID, uuid.UUID]]:
    """Claim due work and recover expired claims without holding locks while sending."""

    now = timezone.now()
    with transaction.atomic():
        PushNotification.objects.filter(
            status=PushNotification.Status.SENDING,
            dispatch_lease_expires_at__lt=now,
        ).update(
            status=PushNotification.Status.SCHEDULED,
            dispatch_lease_expires_at=None,
            dispatch_lease_token=None,
        )
        due = list(
            PushNotification.objects.select_for_update(skip_locked=True)
            .filter(status=PushNotification.Status.SCHEDULED, scheduled_time__lte=now)
            .order_by("scheduled_time")[:limit]
        )
        for notification in due:
            token = uuid.uuid4()
            notification.status = PushNotification.Status.SENDING
            notification.dispatch_started_at = now
            notification.dispatch_lease_expires_at = now + LEASE_DURATION
            notification.dispatch_lease_token = token
            notification.save(
                update_fields=[
                    "status", "dispatch_started_at", "dispatch_lease_expires_at",
                    "dispatch_lease_token", "updated_at",
                ]
            )
    return [(notification.pk, notification.dispatch_lease_token) for notification in due]


def _create_deliveries(notification: PushNotification) -> None:
    """Snapshot active subscribers once, before this notification is dispatched."""

    if notification.deliveries.exists():
        return
    subscribers = list(PushSubscriber.objects.filter(is_active=True).only("id"))
    PushDelivery.objects.bulk_create(
        [
            PushDelivery(notification=notification, subscriber=subscriber, subscriber_id_at_dispatch=subscriber.id)
            for subscriber in subscribers
        ],
        batch_size=DISPATCH_BATCH_SIZE,
        ignore_conflicts=True,
    )
    PushNotification.objects.filter(pk=notification.pk).update(
        subscriber_count_at_send=len(subscribers)
    )


def _claim_delivery_batch(notification: PushNotification) -> list[PushDelivery]:
    """Atomically lease a bounded delivery batch before performing network I/O."""

    now = timezone.now()
    token = uuid.uuid4()
    with transaction.atomic():
        PushDelivery.objects.filter(
            notification=notification,
            status=PushDelivery.Status.SENDING,
            dispatch_lease_expires_at__lt=now,
        ).update(status=PushDelivery.Status.PENDING, dispatch_lease_token=None, dispatch_lease_expires_at=None)
        deliveries = list(
            PushDelivery.objects.select_for_update(skip_locked=True, of=("self",))
            .select_related("subscriber", "notification")
            .filter(notification=notification, status=PushDelivery.Status.PENDING)
            .order_by("created_at")[:DISPATCH_BATCH_SIZE]
        )
        for delivery in deliveries:
            delivery.status = PushDelivery.Status.SENDING
            delivery.dispatch_lease_token = token
            delivery.dispatch_lease_expires_at = now + DELIVERY_LEASE_DURATION
            delivery.save(update_fields=["status", "dispatch_lease_token", "dispatch_lease_expires_at", "updated_at"])
    return deliveries


def _send_delivery(delivery: PushDelivery, lease_token: uuid.UUID) -> None:
    """Send one pending delivery and persist a privacy-safe result."""

    if not PushDelivery.objects.filter(
        pk=delivery.pk,
        status=PushDelivery.Status.SENDING,
        dispatch_lease_token=lease_token,
        dispatch_lease_expires_at__gt=timezone.now(),
    ).exists():
        return
    if not delivery.subscriber:
        delivery.status = PushDelivery.Status.EXPIRED
        delivery.error_category = "subscription_removed"
        delivery.save(update_fields=["status", "error_category", "updated_at"])
        return
    try:
        from pywebpush import WebPushException, webpush

        payload = {
            "title": delivery.notification.title,
            "body": delivery.notification.body,
            "icon": delivery.notification.icon_path,
            "notificationId": str(delivery.notification_id),
            "destinationPath": delivery.notification.destination_path,
            "clickEndpoint": "/push/click/",
            "clickToken": _signed_click_token(delivery),
        }
        webpush(
            subscription_info={
                "endpoint": delivery.subscriber.endpoint,
                "keys": {"p256dh": delivery.subscriber.p256dh, "auth": delivery.subscriber.auth},
            },
            data=json.dumps(payload),
            vapid_private_key=settings.VAPID_PRIVATE_KEY,
            vapid_claims={"sub": settings.VAPID_CLAIMS_SUBJECT},
            timeout=settings.PUSH_REQUEST_TIMEOUT_SECONDS,
        )
    except ImportError:
        raise RuntimeError("pywebpush must be installed before scheduled push dispatch can run.")
    except Exception as exc:  # pywebpush wraps response status in provider-specific exceptions.
        response = getattr(exc, "response", None)
        status_code = getattr(response, "status_code", None)
        if status_code in {404, 410}:
            subscriber = delivery.subscriber
            delivery.status = PushDelivery.Status.EXPIRED
            delivery.error_category = "expired_subscription"
            delivery.subscriber = None
            delivery.save(update_fields=["status", "error_category", "subscriber", "updated_at"])
            subscriber.delete()
            return
        logger.warning("Web Push provider rejected a delivery", extra={"status_code": status_code})
        delivery.status = PushDelivery.Status.FAILED
        delivery.error_category = "provider_error"
        delivery.save(update_fields=["status", "error_category", "updated_at"])
        return
    delivery.status = PushDelivery.Status.ACCEPTED
    delivery.accepted_at = timezone.now()
    delivery.error_category = ""
    delivery.save(update_fields=["status", "accepted_at", "error_category", "updated_at"])


def dispatch_notification(
    notification_id: uuid.UUID,
    lease_token: uuid.UUID,
    deadline_seconds: int | None = None,
) -> DispatchResult:
    """Dispatch one claimed notification in bounded batches and finalize aggregate state."""

    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_CLAIMS_SUBJECT:
        raise RuntimeError("VAPID_PRIVATE_KEY and VAPID_CLAIMS_SUBJECT must be configured.")
    notification = PushNotification.objects.filter(
        pk=notification_id,
        status=PushNotification.Status.SENDING,
        dispatch_lease_token=lease_token,
        dispatch_lease_expires_at__gt=timezone.now(),
    ).first()
    if not notification:
        return DispatchResult(accepted=0, failed=0, expired=0)
    if deadline_seconds is None:
        deadline_seconds = settings.PUSH_DISPATCH_MAX_SECONDS
    _create_deliveries(notification)
    deadline = time.monotonic() + deadline_seconds
    while time.monotonic() < deadline:
        deliveries = _claim_delivery_batch(notification)
        if not deliveries:
            break
        for delivery in deliveries:
            if time.monotonic() >= deadline:
                break
            _send_delivery(delivery, delivery.dispatch_lease_token)

    counts = notification.deliveries.values("status").annotate(total=Count("id"))
    totals = {row["status"]: row["total"] for row in counts}
    accepted = totals.get(PushDelivery.Status.ACCEPTED, 0)
    expired = totals.get(PushDelivery.Status.EXPIRED, 0)
    failed = totals.get(PushDelivery.Status.FAILED, 0) + expired
    remaining = totals.get(PushDelivery.Status.PENDING, 0) + totals.get(PushDelivery.Status.SENDING, 0)
    if remaining:
        return DispatchResult(accepted=accepted, failed=failed, expired=expired)
    PushNotification.objects.filter(pk=notification.pk, dispatch_lease_token=lease_token).update(
        status=PushNotification.Status.SENT if accepted else PushNotification.Status.FAILED,
        sent_at=timezone.now(),
        accepted_count=accepted,
        failure_count=failed,
        dispatch_lease_expires_at=None,
        dispatch_lease_token=None,
    )
    return DispatchResult(accepted=accepted, failed=failed, expired=expired)


def purge_inactive_subscribers(days: int = 90) -> int:
    """Delete voluntarily inactive subscriptions after the documented retention period."""

    threshold = timezone.now() - timedelta(days=days)
    deleted, _ = PushSubscriber.objects.filter(
        is_active=False, unsubscribed_at__lt=threshold
    ).delete()
    return deleted


def purge_request_rate_limits(hours: int = 2) -> int:
    """Remove expired hashed request counters as a bounded scheduler maintenance task."""

    deleted, _ = PushRequestRateLimit.objects.filter(
        window_started_at__lt=timezone.now() - timedelta(hours=hours)
    ).delete()
    return deleted
