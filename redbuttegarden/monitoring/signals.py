import logging
from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.dispatch import receiver

logger = logging.getLogger("django.request")

@receiver(user_logged_in)
def log_successful_login(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    logger.info(f"Successful login | IP: {ip} | Username: {user.username}")

@receiver(user_login_failed)
def log_failed_login(sender, credentials, request, **kwargs):
    ip = get_client_ip(request)
    username = credentials.get("username", "unknown")
    logger.warning(f"Failed login attempt | IP: {ip} | Username: {username}")

def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0]
    return request.META.get("REMOTE_ADDR")