from unittest.mock import patch

from django.test import override_settings


TEST_STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}


@override_settings(STORAGES=TEST_STORAGES)
def test_chat_page_renders(client, settings):
    settings.OAKLEY_CHAT_ENABLED = True

    response = client.get("/oakley-chat/")

    assert response.status_code == 200
    assert b"Oakley Chat Assistant" in response.content
    assert b"Questions? Ask Oakley." in response.content


@override_settings(STORAGES=TEST_STORAGES)
def test_chat_page_shows_disabled_state(client, settings):
    settings.OAKLEY_CHAT_ENABLED = False

    response = client.get("/oakley-chat/")

    assert response.status_code == 200
    assert b"currently disabled" in response.content


@patch("oakley_chat.views.ChatbotServiceClient.chat")
def test_send_chat_returns_json_payload(mock_chat, client, settings):
    settings.OAKLEY_CHAT_ENABLED = True
    mock_chat.return_value = {
        "response": '<p>Concert gates open at 6 PM. <a href="https://tickets.example.com/show">Buy tickets</a></p>',
        "suggested_prompts": ["What can I bring?"],
        "messages": [
            {"kind": "final", "response": "Concert gates open at 6 PM."},
        ],
    }

    response = client.post("/oakley-chat/send/", data={"message": "When do gates open?"})

    assert response.status_code == 200
    payload = response.json()
    assert "Concert gates open at 6 PM." in payload["reply_html"]
    assert payload["suggested_prompts"] == ["What can I bring?"]
    assert mock_chat.call_args.kwargs["message"] == "When do gates open?"
    assert mock_chat.call_args.kwargs["session_uuid"]


def test_send_chat_requires_message(client, settings):
    settings.OAKLEY_CHAT_ENABLED = True

    response = client.post("/oakley-chat/send/", data={"message": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "Please enter a message before sending."


@patch("oakley_chat.views.ChatbotServiceClient.chat")
def test_proxy_returns_chatbot_response(mock_chat, client, settings):
    settings.OAKLEY_CHAT_ENABLED = True
    mock_chat.return_value = {
        "response": "Testing",
        "suggested_prompts": ["What events are coming up?"],
    }

    response = client.post(
        "/oakley-chat/proxy/",
        data='{"message": "Tell me about concerts", "session_uuid": "abc"}',
        content_type="application/json",
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Testing"


def test_proxy_rejects_missing_message(client, settings):
    settings.OAKLEY_CHAT_ENABLED = True

    response = client.post(
        "/oakley-chat/proxy/",
        data='{"session_uuid": "abc"}',
        content_type="application/json",
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "message is required"


def test_healthcheck(client):
    response = client.get("/oakley-chat/health/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_legacy_underscore_chat_url_redirects(client):
    response = client.get("/oakley_chat/")

    assert response.status_code == 302
    assert response["Location"].endswith("/oakley-chat/")
