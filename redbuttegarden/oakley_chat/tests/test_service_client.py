from unittest.mock import Mock, patch

import pytest
import requests

from oakley_chat.service_client import ChatbotServiceClient, ChatbotServiceError


@patch("oakley_chat.service_client.requests.post")
def test_chat_sends_expected_payload(mock_post, settings):
    settings.OAKLEY_CHAT_SERVICE_URL = "http://chatbot.example.com"
    settings.OAKLEY_CHAT_API_KEY = "api-key"
    mock_response = Mock()
    mock_response.json.return_value = {
        "response": "Testing",
        "suggested_prompts": [],
    }
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    client = ChatbotServiceClient(timeout=5.0)
    response_payload = client.chat("Tell me about concerts", "session-123")

    assert response_payload["response"] == "Testing"
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["headers"]["x-api-key"] == "api-key"
    assert kwargs["json"]["session_uuid"] == "session-123"
    assert kwargs["timeout"] == 5.0


@patch("oakley_chat.service_client.requests.post")
def test_chat_raises_service_error_on_http_failure(mock_post, settings):
    settings.OAKLEY_CHAT_SERVICE_URL = "http://chatbot.example.com"
    settings.OAKLEY_CHAT_API_KEY = "api-key"
    mock_post.side_effect = requests.RequestException("upstream failed")

    client = ChatbotServiceClient()

    with pytest.raises(ChatbotServiceError, match="upstream failed"):
        client.chat("Tell me about plants")


def test_chat_requires_configuration(settings):
    settings.OAKLEY_CHAT_SERVICE_URL = ""
    settings.OAKLEY_CHAT_API_KEY = ""

    client = ChatbotServiceClient()

    with pytest.raises(ChatbotServiceError, match="not configured"):
        client.chat("Tell me about concerts")
