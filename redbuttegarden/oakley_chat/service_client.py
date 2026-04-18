import uuid

import requests
from django.conf import settings


class ChatbotServiceError(Exception):
    """Raised when the Oakley chatbot service cannot be reached or configured."""


class ChatbotServiceClient:
    def __init__(
        self,
        base_url=None,
        api_key=None,
        timeout=None,
    ):
        self.base_url = (
            (base_url if base_url is not None else settings.OAKLEY_CHAT_SERVICE_URL) or ""
        ).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.OAKLEY_CHAT_API_KEY
        self.timeout = (
            timeout if timeout is not None else settings.OAKLEY_CHAT_TIMEOUT_SECONDS
        )

    def chat(self, message, session_uuid=None):
        if not message:
            raise ValueError("message is required")

        if not self.base_url or not self.api_key:
            raise ChatbotServiceError("Oakley chat service is not configured")

        payload = {
            "message": message,
            "session_uuid": session_uuid or str(uuid.uuid4()),
        }
        headers = {
            "x-api-key": self.api_key,
            "Accept": "application/json",
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ChatbotServiceError(str(exc)) from exc

        try:
            return response.json()
        except ValueError as exc:
            raise ChatbotServiceError("Oakley chat service returned invalid JSON") from exc
