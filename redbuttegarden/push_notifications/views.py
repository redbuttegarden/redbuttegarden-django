"""Public, same-origin endpoints for Web Push preference management."""

from __future__ import annotations

import json
import secrets
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.crypto import salted_hmac
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from ipware import get_client_ip

from .services import deactivate_subscription, record_notification_click, register_subscription
from .models import PushRequestRateLimit

MAX_BODY_BYTES = 8_192


def _rate_limited(request: HttpRequest) -> bool:
    """Apply a DB-backed fixed-window limit shared by all Lambda instances."""

    client_ip, _ = get_client_ip(request)
    if not client_ip:
        return True
    now = timezone.now()
    window_started_at = now.replace(minute=0, second=0, microsecond=0)
    client_hash = salted_hmac("push-notifications-rate-limit", client_ip).hexdigest()
    for _ in range(2):
        try:
            with transaction.atomic():
                counter, _ = PushRequestRateLimit.objects.select_for_update().get_or_create(
                    client_hash=client_hash,
                    window_started_at=window_started_at,
                )
                counter.request_count += 1
                counter.save(update_fields=["request_count"])
                return counter.request_count > settings.PUSH_REQUESTS_PER_HOUR
        except IntegrityError:
            # A concurrent Lambda created this client's hourly window first.
            continue
    return True


def _from_trusted_origin(request: HttpRequest) -> bool:
    """Require CloudFront's private origin header outside local development."""

    expected = settings.PUSH_ORIGIN_HEADER_SECRET
    if not expected and settings.DEBUG:
        return True
    return bool(expected) and secrets.compare_digest(
        request.headers.get("X-RBG-Push-Origin", ""), expected
    )


def _json_payload(request: HttpRequest) -> dict[str, Any] | None:
    """Return a small JSON object or None for malformed/unacceptable input."""

    if request.content_type != "application/json" or len(request.body) > MAX_BODY_BYTES:
        return None
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


@require_GET
@ensure_csrf_cookie
def preferences(request: HttpRequest) -> HttpResponse:
    """Render the explicit, accessible Web Push opt-in preference page."""

    response = render(
        request,
        "push_notifications/preferences.html",
        {"vapid_public_key": settings.VAPID_PUBLIC_KEY},
    )
    # The response sets a CSRF cookie and includes deployment-specific VAPID
    # configuration, so it must never be retained by a shared cache.
    response["Cache-Control"] = "private, no-store"
    return response


@require_http_methods(["POST", "DELETE"])
def subscriptions(request: HttpRequest) -> JsonResponse:
    """Register or deactivate a browser subscription under Django CSRF protection."""

    if not _from_trusted_origin(request):
        return JsonResponse({"detail": "Not found."}, status=404)
    if _rate_limited(request):
        return JsonResponse({"detail": "Too many requests."}, status=429)
    payload = _json_payload(request)
    if payload is None:
        return JsonResponse({"detail": "Invalid JSON request."}, status=400)
    try:
        if request.method == "POST":
            register_subscription(payload)
        else:
            endpoint = payload.get("endpoint")
            deactivate_subscription(endpoint)
    except ValidationError:
        return JsonResponse({"detail": "Invalid subscription."}, status=400)
    response = JsonResponse({}, status=204)
    response["Cache-Control"] = "no-store"
    return response


@csrf_exempt
@require_POST
def click(request: HttpRequest) -> JsonResponse:
    """Record a signed service-worker click without relying on a CSRF cookie."""

    if not _from_trusted_origin(request):
        return JsonResponse({"detail": "Not found."}, status=404)
    if _rate_limited(request):
        return JsonResponse({"detail": "Too many requests."}, status=429)
    payload = _json_payload(request)
    token = payload.get("token") if payload else None
    if not isinstance(token, str):
        return JsonResponse({"detail": "Invalid click."}, status=400)
    record_notification_click(token)
    response = JsonResponse({}, status=204)
    response["Cache-Control"] = "no-store"
    return response
