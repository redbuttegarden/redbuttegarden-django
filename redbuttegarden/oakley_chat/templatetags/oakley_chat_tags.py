from django import template
from django.conf import settings
from django.middleware.csrf import get_token
from django.urls import reverse


register = template.Library()


@register.inclusion_tag("oakley_chat/includes/widget.html", takes_context=True)
def oakley_chat_widget(context):
    request = context.get("request")
    enabled = bool(getattr(settings, "OAKLEY_CHAT_ENABLED", False))
    csrf_token = get_token(request) if request is not None else ""

    return {
        "oakley_chat_enabled": enabled,
        "oakley_chat_send_url": reverse("oakley_chat:send_chat") if enabled else "",
        "oakley_chat_page_url": reverse("oakley_chat:chat_page") if enabled else "",
        "oakley_chat_csrf_token": csrf_token,
    }
