import logging

from ipware import get_client_ip

logger = logging.getLogger("django.request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip, is_routable = get_client_ip(request)
        ip = ip or "unknown"

        logger.info(
            f"Request from IP: {ip} | Method: {request.method} | Path: {request.path} | User-Agent: {request.META.get('HTTP_USER_AGENT', 'unknown')}"
        )

        response = self.get_response(request)
        return response
