import requests

from external_integrations.client import ExternalIntegrationClient
from external_integrations.config import ExternalIntegrationConfig
from external_integrations.exceptions import (
    ExternalIntegrationDisabled,
    ExternalIntegrationRequestError,
    ExternalIntegrationResponseError,
)


class FakeResponse:
    def __init__(self, status_code=200, payload=None, json_error=False):
        self.status_code = status_code
        self.payload = {} if payload is None else payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise ValueError("bad json")
        return self.payload


class FakeSession:
    def __init__(self, responses=None, error=None):
        self.responses = list(responses or [FakeResponse(payload={"ok": True})])
        self.error = error
        self.calls = []

    def request(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return self.responses.pop(0)


def make_config(**overrides):
    values = {
        "enabled": True,
        "live_requests_enabled": True,
        "write_enabled": False,
        "account_linking_enabled": False,
        "access_checks_enabled": False,
        "checkout_enabled": False,
        "redirect_fallback_enabled": False,
        "allowed_item_types": (),
        "base_url": "https://integration.example.test",
        "api_token": "secret-token",
        "timeout_seconds": 3,
        "max_retries": 0,
    }
    values.update(overrides)
    return ExternalIntegrationConfig(**values)


def test_client_does_not_request_when_disabled():
    session = FakeSession()
    client = ExternalIntegrationClient(
        make_config(enabled=False),
        session=session,
    )

    try:
        client.request_json("GET", "/health")
    except ExternalIntegrationDisabled:
        pass
    else:
        raise AssertionError("Expected disabled client to fail closed.")

    assert session.calls == []


def test_client_adds_auth_tracing_and_disables_redirects():
    session = FakeSession()
    client = ExternalIntegrationClient(make_config(), session=session)

    payload = client.request_json("GET", "/health", request_id="req-1")

    assert payload == {"ok": True}
    args, kwargs = session.calls[0]
    assert args == ("GET", "https://integration.example.test/health")
    assert kwargs["headers"]["Authorization"] == "Bearer secret-token"
    assert kwargs["headers"]["X-Request-ID"] == "req-1"
    assert kwargs["allow_redirects"] is False
    assert kwargs["timeout"] == 3


def test_client_protects_auth_headers_from_caller_override():
    session = FakeSession()
    client = ExternalIntegrationClient(make_config(), session=session)

    client.request_json(
        "GET",
        "/health",
        headers={"Authorization": "Bearer caller-token", "X-Request-ID": "caller"},
        request_id="server",
    )

    _, kwargs = session.calls[0]
    assert kwargs["headers"]["Authorization"] == "Bearer secret-token"
    assert kwargs["headers"]["X-Request-ID"] == "server"


def test_client_rejects_restricted_caller_headers():
    session = FakeSession()
    client = ExternalIntegrationClient(make_config(), session=session)

    try:
        client.request_json("GET", "/health", headers={"Host": "elsewhere"})
    except ExternalIntegrationRequestError as ex:
        assert "restricted values" in str(ex)
    else:
        raise AssertionError("Expected restricted caller header to fail.")

    assert session.calls == []


def test_client_rejects_absolute_paths():
    client = ExternalIntegrationClient(make_config(), session=FakeSession())

    try:
        client.request_json("GET", "https://elsewhere.example.test/health")
    except ExternalIntegrationRequestError as ex:
        assert "root-relative" in str(ex)
    else:
        raise AssertionError("Expected absolute path to fail.")


def test_client_requires_idempotency_key_for_unsafe_methods():
    client = ExternalIntegrationClient(
        make_config(write_enabled=True),
        session=FakeSession(),
    )

    try:
        client.request_json("POST", "/write", json={"ok": True})
    except ExternalIntegrationRequestError as ex:
        assert "idempotency key" in str(ex)
    else:
        raise AssertionError("Expected unsafe write without key to fail.")


def test_client_blocks_writes_when_write_flag_is_disabled():
    session = FakeSession()
    client = ExternalIntegrationClient(make_config(), session=session)

    try:
        client.request_json(
            "POST",
            "/write",
            json={"ok": True},
            idempotency_key="idem-1",
        )
    except ExternalIntegrationDisabled as ex:
        assert "writes are disabled" in str(ex)
    else:
        raise AssertionError("Expected disabled writes to fail closed.")

    assert session.calls == []


def test_client_redacts_token_from_response_errors():
    session = FakeSession(responses=[FakeResponse(status_code=500)])
    client = ExternalIntegrationClient(make_config(), session=session)

    try:
        client.request_json("GET", "/health")
    except ExternalIntegrationResponseError as ex:
        assert "secret-token" not in str(ex)
        assert ex.status_code == 500
    else:
        raise AssertionError("Expected unsuccessful response to fail.")


def test_client_retries_idempotent_errors_with_same_headers():
    session = FakeSession(
        responses=[
            FakeResponse(payload={"ok": True}),
        ],
        error=requests.Timeout("timeout"),
    )
    client = ExternalIntegrationClient(
        make_config(max_retries=1),
        session=session,
    )

    try:
        client.request_json("GET", "/health", request_id="req-1")
    except ExternalIntegrationRequestError as ex:
        assert "secret-token" not in str(ex)
    else:
        raise AssertionError("Expected repeated request failures to fail.")

    assert len(session.calls) == 2
