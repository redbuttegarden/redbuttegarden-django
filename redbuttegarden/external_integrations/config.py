"""Configuration helpers for neutral external integrations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlsplit

from django.conf import settings

from .exceptions import ExternalIntegrationConfigError


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _parse_timeout(value: Any) -> float:
    try:
        timeout = float(value)
    except (TypeError, ValueError) as ex:
        raise ExternalIntegrationConfigError(
            "External integration timeout must be a number."
        ) from ex
    if timeout <= 0:
        raise ExternalIntegrationConfigError(
            "External integration timeout must be greater than zero."
        )
    if timeout > 30:
        raise ExternalIntegrationConfigError(
            "External integration timeout must not exceed 30 seconds."
        )
    return timeout


def _parse_retries(value: Any) -> int:
    try:
        retries = int(value)
    except (TypeError, ValueError) as ex:
        raise ExternalIntegrationConfigError(
            "External integration retry count must be an integer."
        ) from ex
    if retries < 0:
        raise ExternalIntegrationConfigError(
            "External integration retry count cannot be negative."
        )
    if retries > 3:
        raise ExternalIntegrationConfigError(
            "External integration retry count must not exceed three."
        )
    return retries


def _parse_allowed_item_types(value: Any) -> tuple[str, ...]:
    if not value:
        return ()
    if isinstance(value, (list, tuple)):
        raw_items = value
    else:
        raw_items = str(value).split(",")
    return tuple(
        item.strip().lower()
        for item in raw_items
        if item and item.strip()
    )


@dataclass(frozen=True)
class ExternalIntegrationConfig:
    """Runtime configuration for neutral server-side integration calls."""

    enabled: bool
    live_requests_enabled: bool
    write_enabled: bool
    account_linking_enabled: bool
    access_checks_enabled: bool
    checkout_enabled: bool
    redirect_fallback_enabled: bool
    allowed_item_types: tuple[str, ...]
    base_url: str
    api_token: str
    timeout_seconds: float
    max_retries: int

    @classmethod
    def from_django_settings(cls) -> "ExternalIntegrationConfig":
        """Build integration configuration from Django settings."""

        return cls(
            enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_ENABLED", False)
            ),
            live_requests_enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED", False)
            ),
            write_enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_WRITE_ENABLED", False)
            ),
            account_linking_enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_ACCOUNT_LINKING_ENABLED", False)
            ),
            access_checks_enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_ACCESS_CHECKS_ENABLED", False)
            ),
            checkout_enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_CHECKOUT_ENABLED", False)
            ),
            redirect_fallback_enabled=_parse_bool(
                getattr(settings, "EXTERNAL_INTEGRATION_REDIRECT_FALLBACK_ENABLED", False)
            ),
            allowed_item_types=_parse_allowed_item_types(
                getattr(settings, "EXTERNAL_INTEGRATION_ALLOWED_ITEM_TYPES", "")
            ),
            base_url=str(getattr(settings, "EXTERNAL_INTEGRATION_BASE_URL", "")).strip(),
            api_token=str(getattr(settings, "EXTERNAL_INTEGRATION_API_TOKEN", "")),
            timeout_seconds=_parse_timeout(
                getattr(settings, "EXTERNAL_INTEGRATION_TIMEOUT_SECONDS", "5")
            ),
            max_retries=_parse_retries(
                getattr(settings, "EXTERNAL_INTEGRATION_MAX_RETRIES", "1")
            ),
        )

    def validate(self) -> None:
        """Raise when enabled settings are incomplete or unsafe."""

        if not self.enabled:
            return

        if self.live_requests_enabled:
            if not self.base_url:
                raise ExternalIntegrationConfigError(
                    "External integration base URL is required for live requests."
                )
            if not self.api_token:
                raise ExternalIntegrationConfigError(
                    "External integration API token is required for live requests."
                )
            parsed = urlsplit(self.base_url)
            if parsed.scheme != "https" or not parsed.netloc:
                raise ExternalIntegrationConfigError(
                    "External integration base URL must be an HTTPS origin."
                )
            if (
                parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
                or parsed.path not in {"", "/"}
            ):
                raise ExternalIntegrationConfigError(
                    "External integration base URL must not include credentials, "
                    "paths, query strings, or fragments."
                )

        if self.write_enabled and not self.live_requests_enabled:
            raise ExternalIntegrationConfigError(
                "External integration writes require live requests to be enabled."
            )

        if self.checkout_enabled and not self.access_checks_enabled:
            raise ExternalIntegrationConfigError(
                "External integration checkout requires access checks to be enabled."
            )
