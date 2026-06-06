from django.test import override_settings

from external_integrations.config import ExternalIntegrationConfig
from external_integrations.exceptions import ExternalIntegrationConfigError


def test_config_defaults_are_disabled():
    config = ExternalIntegrationConfig.from_django_settings()

    assert config.enabled is False
    assert config.live_requests_enabled is False
    assert config.write_enabled is False
    assert config.account_linking_enabled is False
    assert config.access_checks_enabled is False
    assert config.checkout_enabled is False
    assert config.redirect_fallback_enabled is False
    assert config.allowed_item_types == ()


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=True,
    EXTERNAL_INTEGRATION_BASE_URL="https://integration.example.test",
    EXTERNAL_INTEGRATION_API_TOKEN="token-value",
    EXTERNAL_INTEGRATION_TIMEOUT_SECONDS="2.5",
    EXTERNAL_INTEGRATION_MAX_RETRIES="2",
    EXTERNAL_INTEGRATION_ALLOWED_ITEM_TYPES="one, two",
)
def test_config_accepts_safe_live_settings():
    config = ExternalIntegrationConfig.from_django_settings()

    config.validate()

    assert config.base_url == "https://integration.example.test"
    assert config.timeout_seconds == 2.5
    assert config.max_retries == 2
    assert config.allowed_item_types == ("one", "two")


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=True,
    EXTERNAL_INTEGRATION_BASE_URL="http://integration.example.test",
    EXTERNAL_INTEGRATION_API_TOKEN="token-value",
)
def test_config_rejects_non_https_live_base_url():
    config = ExternalIntegrationConfig.from_django_settings()

    try:
        config.validate()
    except ExternalIntegrationConfigError as ex:
        assert "HTTPS" in str(ex)
    else:
        raise AssertionError("Expected unsafe base URL to fail validation.")


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=True,
    EXTERNAL_INTEGRATION_BASE_URL="https://user:pass@integration.example.test/path",
    EXTERNAL_INTEGRATION_API_TOKEN="token-value",
)
def test_config_rejects_base_url_with_credentials_or_path():
    config = ExternalIntegrationConfig.from_django_settings()

    try:
        config.validate()
    except ExternalIntegrationConfigError as ex:
        assert "must not include credentials" in str(ex)
    else:
        raise AssertionError("Expected non-origin base URL to fail validation.")


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=False,
    EXTERNAL_INTEGRATION_BASE_URL="",
    EXTERNAL_INTEGRATION_API_TOKEN="",
)
def test_config_allows_missing_live_credentials_when_live_requests_are_disabled():
    config = ExternalIntegrationConfig.from_django_settings()

    config.validate()


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_WRITE_ENABLED=True,
    EXTERNAL_INTEGRATION_LIVE_REQUESTS_ENABLED=False,
)
def test_config_rejects_writes_without_live_requests():
    config = ExternalIntegrationConfig.from_django_settings()

    try:
        config.validate()
    except ExternalIntegrationConfigError as ex:
        assert "writes require live requests" in str(ex)
    else:
        raise AssertionError("Expected write settings to fail validation.")


@override_settings(
    EXTERNAL_INTEGRATION_ENABLED=True,
    EXTERNAL_INTEGRATION_ACCESS_CHECKS_ENABLED=False,
    EXTERNAL_INTEGRATION_CHECKOUT_ENABLED=True,
)
def test_config_rejects_checkout_without_access_checks():
    config = ExternalIntegrationConfig.from_django_settings()

    try:
        config.validate()
    except ExternalIntegrationConfigError as ex:
        assert "checkout requires access checks" in str(ex)
    else:
        raise AssertionError("Expected checkout settings to fail validation.")
