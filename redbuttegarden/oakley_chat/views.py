import json
import logging
from uuid import uuid4

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .service_client import ChatbotServiceClient, ChatbotServiceError


CHAT_SESSION_UUID_KEY = "oakley_chat_session_uuid"
logger = logging.getLogger(__name__)


@require_GET
def healthcheck(request):
    return JsonResponse({"status": "ok"})


@require_GET
def chat_page(request):
    return render(
        request,
        "oakley_chat/index.html",
        {"oakley_chat_enabled": settings.OAKLEY_CHAT_ENABLED},
    )


@require_POST
def send_chat(request):
    user_message = (request.POST.get("message") or "").strip()
    if not user_message:
        return JsonResponse(
            {"detail": "Please enter a message before sending."},
            status=400,
        )

    if CHAT_SESSION_UUID_KEY not in request.session:
        request.session[CHAT_SESSION_UUID_KEY] = str(uuid4())

    session_uuid = request.session[CHAT_SESSION_UUID_KEY]
    client = ChatbotServiceClient()

    try:
        response_payload = client.chat(message=user_message, session_uuid=session_uuid)
    except ChatbotServiceError as exc:
        logger.warning("Oakley chatbot service error: %s", exc)
        return JsonResponse(
            {"detail": "The Oakley chatbot service is unavailable right now."},
            status=502,
        )

    return JsonResponse(
        {
            "reply_html": response_payload.get("response") or "<p>No response</p>",
            "suggested_prompts": response_payload.get("suggested_prompts", []),
            "messages": response_payload.get("messages", []),
        }
    )


@require_POST
def chat_proxy(request):
    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    message = (payload.get("message") or "").strip()
    session_uuid = payload.get("session_uuid")
    if not message:
        return JsonResponse({"detail": "message is required"}, status=400)

    if not session_uuid:
        session_uuid = str(uuid4())

    client = ChatbotServiceClient()
    try:
        response_payload = client.chat(message=message, session_uuid=session_uuid)
    except ChatbotServiceError as exc:
        return JsonResponse({"detail": str(exc)}, status=502)

    return JsonResponse(response_payload)
