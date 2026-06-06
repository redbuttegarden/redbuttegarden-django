"""Application configuration for external integration helpers."""

from __future__ import annotations

from django.apps import AppConfig


class ExternalIntegrationsConfig(AppConfig):
    """Configure neutral external integration helpers."""

    default_auto_field = "django.db.models.AutoField"
    name = "external_integrations"

    def ready(self) -> None:
        """Register integration system checks when Django starts."""

        from . import checks  # noqa: F401
