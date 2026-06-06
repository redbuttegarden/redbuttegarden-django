"""Generic JSON client for neutral server-side external integrations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any
from urllib.parse import urlsplit
from uuid import uuid4

import requests

from .config import ExternalIntegrationConfig
from .exceptions import (
    ExternalIntegrationDisabled,
    ExternalIntegrationRequestError,
    ExternalIntegrationResponseError,
)

SAFE_RETRY_METHODS = {"GET", "HEAD", "OPTIONS"}
BLOCKED_CALLER_HEADERS = {
    "cookie",
    "host",
    "proxy-authorization",
}


class ExternalIntegrationClient:
    """Small JSON client with fail-closed integration controls."""

    def __init__(
        self,
        config: ExternalIntegrationConfig | None = None,
        *,
        session: requests.Session | None = None,
    ) -> None:
        """Initialize the client with optional config and session injection."""

        self.config = config or ExternalIntegrationConfig.from_django_settings()
        self.session = session or requests.Session()

    def request_json(
        self,
        method: str,
        path: str,
        *,
        json: Mapping[str, Any] | None = None,
        request_id: str | None = None,
        idempotency_key: str | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> dict[str, Any]:
        """Return JSON from an external integration endpoint."""

        self.config.validate()
        if not self.config.enabled or not self.config.live_requests_enabled:
            raise ExternalIntegrationDisabled(
                "External integration live requests are disabled."
            )

        normalized_method = method.upper()
        is_unsafe_method = normalized_method not in SAFE_RETRY_METHODS
        if is_unsafe_method and not self.config.write_enabled:
            raise ExternalIntegrationDisabled(
                "External integration writes are disabled."
            )
        if is_unsafe_method and not idempotency_key:
            raise ExternalIntegrationRequestError(
                "Unsafe external integration requests require an idempotency key."
            )

        url = self._build_url(path)
        request_headers = self._build_headers(
            request_id=request_id,
            idempotency_key=idempotency_key,
            headers=headers,
        )
        attempts = self._attempt_count(normalized_method, idempotency_key)

        last_error: ExternalIntegrationRequestError | None = None
        for _ in range(attempts):
            try:
                response = self.session.request(
                    normalized_method,
                    url,
                    json=json,
                    headers=request_headers,
                    timeout=self.config.timeout_seconds,
                    allow_redirects=False,
                )
            except requests.RequestException as ex:
                last_error = ExternalIntegrationRequestError(
                    "External integration request failed."
                )
                last_error.__cause__ = ex
                continue

            return self._decode_response(response)

        if last_error:
            raise last_error
        raise ExternalIntegrationRequestError("External integration request failed.")

    def _attempt_count(self, method: str, idempotency_key: str | None) -> int:
        if method in SAFE_RETRY_METHODS or idempotency_key:
            return self.config.max_retries + 1
        return 1

    def _build_url(self, path: str) -> str:
        parsed = urlsplit(path)
        if (
            parsed.scheme
            or parsed.netloc
            or not path.startswith("/")
            or path.startswith("//")
        ):
            raise ExternalIntegrationRequestError(
                "External integration paths must be root-relative."
            )
        return f"{self.config.base_url.rstrip('/')}{path}"

    def _build_headers(
        self,
        *,
        request_id: str | None,
        idempotency_key: str | None,
        headers: Mapping[str, str] | None,
    ) -> dict[str, str]:
        request_headers = {"Accept": "application/json"}
        if headers:
            blocked_headers = sorted(
                header for header in headers if header.lower() in BLOCKED_CALLER_HEADERS
            )
            if blocked_headers:
                raise ExternalIntegrationRequestError(
                    "External integration headers include restricted values."
                )
            request_headers.update(headers)
        request_headers.update(
            {
                "Authorization": "Bearer " + self.config.api_token,
                "X-Request-ID": request_id or str(uuid4()),
            }
        )
        if idempotency_key:
            request_headers["Idempotency-Key"] = idempotency_key
        return request_headers

    def _decode_response(self, response: requests.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise ExternalIntegrationResponseError(
                "External integration response was not successful.",
                status_code=response.status_code,
            )
        try:
            payload = response.json()
        except ValueError as ex:
            raise ExternalIntegrationResponseError(
                "External integration response was not valid JSON.",
                status_code=response.status_code,
            ) from ex
        if not isinstance(payload, dict):
            raise ExternalIntegrationResponseError(
                "External integration response JSON must be an object.",
                status_code=response.status_code,
            )
        return payload
