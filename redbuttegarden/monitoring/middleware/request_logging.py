import logging

logger = logging.getLogger("django.request")


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        logger.info(
            f"Request from IP: {get_client_ip(request)} | "
            f"Method: {request.method} | Path: {request.path} | "
            f"Status: {response.status_code}"
        )

        return response


def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")
