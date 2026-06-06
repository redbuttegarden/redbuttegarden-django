"""Exceptions raised by neutral external integration helpers."""

from __future__ import annotations


class ExternalIntegrationError(Exception):
    """Base exception for external integration failures."""


class ExternalIntegrationConfigError(ExternalIntegrationError):
    """Raised when integration settings are missing or unsafe."""


class ExternalIntegrationDisabled(ExternalIntegrationError):
    """Raised when outbound integration behavior is disabled."""


class ExternalIntegrationRequestError(ExternalIntegrationError):
    """Raised when a request cannot be completed safely."""


class ExternalIntegrationResponseError(ExternalIntegrationError):
    """Raised when a response is invalid or unsuccessful."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        """Store a redacted response error message and status code."""

        super().__init__(message)
        self.status_code = status_code
