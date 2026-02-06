import base64
import secrets
from functools import wraps

from django.conf import settings
from django.http import HttpResponse


def _unauthorized_response(realm: str = "Members testing"):
    resp = HttpResponse("Unauthorized", status=401)
    resp["WWW-Authenticate"] = f'Basic realm="{realm}"'
    return resp


def basic_auth_required(view_func=None, *, realm: str = "Members testing"):
    """
    Basic-auth decorator that checks credentials in settings:
      - MEMBERS_BASIC_AUTH_ENABLED (bool, default True)
      - MEMBERS_BASIC_AUTH_USERNAME (str)
      - MEMBERS_BASIC_AUTH_PASSWORD (str)

    Usage:
      @basic_auth_required
      def my_view(request): ...

    Or with a custom realm:
      @basic_auth_required(realm="My realm")
      def my_view(request): ...
    """
    def decorator(fn):
        @wraps(fn)
        def _wrapped(request, *args, **kwargs):
            # Shortcut: allow bypass when disabled
            enabled = getattr(settings, "MEMBERS_BASIC_AUTH_ENABLED", True)
            if not enabled:
                return fn(request, *args, **kwargs)

            username = getattr(settings, "MEMBERS_BASIC_AUTH_USERNAME", "")
            password = getattr(settings, "MEMBERS_BASIC_AUTH_PASSWORD", "")
            if not username or not password:
                # If credentials are missing, deny by default.
                return _unauthorized_response(realm)

            auth = request.META.get("HTTP_AUTHORIZATION")
            if not auth:
                return _unauthorized_response(realm)

            try:
                auth_type, creds = auth.split(" ", 1)
            except ValueError:
                return _unauthorized_response(realm)

            if auth_type.lower() != "basic":
                return _unauthorized_response(realm)

            try:
                decoded = base64.b64decode(creds).decode("utf-8")
                req_user, req_pass = decoded.split(":", 1)
            except Exception:
                return _unauthorized_response(realm)

            # Use constant-time compare
            if (secrets.compare_digest(req_user, username) and
                    secrets.compare_digest(req_pass, password)):
                return fn(request, *args, **kwargs)

            return _unauthorized_response(realm)

        return _wrapped

    # Support both @basic_auth_required and @basic_auth_required(...)
    if view_func is None:
        return decorator
    else:
        return decorator(view_func)
