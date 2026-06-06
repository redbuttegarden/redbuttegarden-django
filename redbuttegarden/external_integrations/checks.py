"""Django system checks for neutral external integration settings."""

from __future__ import annotations

from typing import Any

from django.apps import AppConfig
from django.core.checks import Error, register

from .config import ExternalIntegrationConfig
from .exceptions import ExternalIntegrationConfigError


@register()
def external_integration_checks(
    app_configs: list[AppConfig] | None,
    **kwargs: Any,
) -> list[Error]:
    """Validate external integration settings for safe deployment."""

    try:
        ExternalIntegrationConfig.from_django_settings().validate()
    except ExternalIntegrationConfigError as ex:
        return [
            Error(
                str(ex),
                id="external_integrations.E001",
            )
        ]
    return []
