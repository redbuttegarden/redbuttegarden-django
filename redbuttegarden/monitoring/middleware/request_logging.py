"""Privacy-safe request completion logging for CloudWatch Logs Insights."""

from __future__ import annotations

import json
import logging
import os
import re
from time import perf_counter
from typing import Callable

from django.http import HttpRequest, HttpResponseBase


logger = logging.getLogger("django.request")
_cold_start = True
_XRAY_ROOT_TRACE_ID = re.compile(r"^1-[0-9a-fA-F]{8}-[0-9a-fA-F]{24}$")


def _normalized_route(request: HttpRequest) -> str:
    """Return a stable resolver identifier without exposing request path data."""

    resolver_match = getattr(request, "resolver_match", None)
    if resolver_match is None:
        return "unresolved"
    return resolver_match.route or resolver_match.view_name or "unresolved"


def _xray_trace_id(request: HttpRequest) -> str | None:
    """Return the X-Ray root trace ID from the trusted Lambda request header."""

    trace_header = request.META.get("HTTP_X_AMZN_TRACE_ID", "")
    for part in trace_header.split(";"):
        key, separator, value = part.partition("=")
        if separator and key == "Root" and _XRAY_ROOT_TRACE_ID.fullmatch(value):
            return value
    return None


def _response_size(response: HttpResponseBase) -> int | None:
    """Return a response size without forcing streaming content into memory."""

    content_length = response.get("Content-Length")
    if content_length and content_length.isdigit():
        return int(content_length)
    if getattr(response, "streaming", False):
        return None
    try:
        return len(response.content)
    except (AttributeError, TypeError):
        return None


class RequestLoggingMiddleware:
    """Emit one low-cardinality, privacy-safe JSON record after each response."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponseBase]) -> None:
        """Store the downstream Django request handler."""

        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponseBase:
        """Log aggregate request timing fields after Django returns a response."""

        global _cold_start

        started_at = perf_counter()
        is_cold_start = _cold_start
        _cold_start = False
        response = self.get_response(request)
        duration_ms = round((perf_counter() - started_at) * 1000, 3)
        record: dict[str, object] = {
            "event": "request_complete",
            "route": _normalized_route(request),
            "method": request.method,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "response_size_bytes": _response_size(response),
            "cold_start": is_cold_start,
            "deployment_revision": os.environ.get("DEPLOYMENT_REVISION") or None,
            "trace_id": _xray_trace_id(request),
        }
        try:
            logger.info("%s", json.dumps(record, separators=(",", ":"), sort_keys=True))
        except Exception:
            # Observability must never turn an otherwise successful request into a 5xx.
            pass
        return response
