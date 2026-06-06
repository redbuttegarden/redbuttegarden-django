from django.test import override_settings

from external_integrations.checks import external_integration_checks


@override_settings(EXTERNAL_INTEGRATION_ENABLED=False)
def test_system_check_passes_when_disabled():
    errors = external_integration_checks(None)

    assert not [
        error for error in errors if error.id.startswith("external_integrations.")
    ]


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=True,
    EXTERNAL_INTEGRATION_BASE_URL="",
    EXTERNAL_INTEGRATION_API_TOKEN="token-value",
)
def test_system_check_reports_missing_live_base_url():
    errors = external_integration_checks(None)

    assert any(error.id == "external_integrations.E001" for error in errors)


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=True,
    EXTERNAL_INTEGRATION_BASE_URL="https://integration.example.test",
    EXTERNAL_INTEGRATION_API_TOKEN="token-value",
)
def test_system_check_passes_with_safe_live_settings():
    errors = external_integration_checks(None)

    assert not [
        error for error in errors if error.id.startswith("external_integrations.")
    ]
