import hashlib
import logging

from django.utils.http import quote_etag
from django.template.response import TemplateResponse
from django.utils.deprecation import MiddlewareMixin
from typing import Optional

logger = logging.getLogger("etag-diagnostic")


class EnsureRenderedAndSetETagMiddleware(MiddlewareMixin):
    def _compute_etag(self, content: bytes) -> str:
        digest = hashlib.sha1(content).hexdigest()
        return quote_etag(digest)

    def process_template_response(self, request, response):
        if isinstance(response, TemplateResponse) and not response.is_rendered:
            response.render()
        return response

    def process_response(self, request, response):
        # Log incoming conditional headers we care about
        inm = request.META.get("HTTP_IF_NONE_MATCH")
        ims = request.META.get("HTTP_IF_MODIFIED_SINCE")
        logger.info(
            "ETagDiag: Incoming If-None-Match=%r If-Modified-Since=%r", inm, ims
        )

        # Inspect response before we set anything
        try:
            has_etag_before = response.has_header("ETag")
        except Exception:
            has_etag_before = False
        logger.info(
            "ETagDiag: before: has_etag=%s status=%s",
            has_etag_before,
            getattr(response, "status_code", None),
        )

        # Normal behavior: skip streaming or non-body responses
        try:
            content = getattr(response, "content", None)
        except Exception:
            content = None
        if content is None or getattr(response, "streaming", False):
            logger.info("ETagDiag: skipping (no content or streaming).")
            return response

        if response.has_header("ETag") or response.has_header("Last-Modified"):
            logger.info("ETagDiag: response already had validator; leaving it.")
            return response

        if response.status_code not in (200, 203, 206):
            logger.info(
                "ETagDiag: status not suitable for ETag: %s", response.status_code
            )
            return response

        try:
            etag = self._compute_etag(content)
            response["ETag"] = etag
            logger.info("ETagDiag: computed and set ETag=%r", etag)
        except Exception as exc:
            logger.exception("ETagDiag: failed to compute ETag: %s", exc)

        return response


class HtmlCacheControlMiddleware:
    """
    Single middleware to:
      - Force HTML to be revalidated by browsers (no-cache, max-age=0).
      - For authenticated users, mark HTML as private so shared caches don't serve it.
    Works with ConditionalGetMiddleware which adds ETag/Last-Modified for efficient 304 responses.
    """

    # desired header values
    ANON_CACHE_CTRL = "no-cache, must-revalidate, max-age=0, proxy-revalidate"
    AUTH_CACHE_CTRL = "private, no-cache, must-revalidate, max-age=0"

    def __init__(self, get_response):
        self.get_response = get_response

    def _media_type(self, response) -> Optional[str]:
        content_type = response.get("Content-Type", "")
        return content_type.split(";", 1)[0].strip().lower() if content_type else None

    def __call__(self, request):
        response = self.get_response(request)

        media_type = self._media_type(response)
        if media_type != "text/html":
            return response

        # If there's already a Cache-Control and it's more restrictive than what we'd set,
        # prefer the existing header. We treat presence of 'no-store' or 'private' as authoritative.
        existing_cc = (response.get("Cache-Control") or "").lower()

        # Decide header to apply
        try:
            is_auth = bool(request.user and request.user.is_authenticated)
        except Exception:
            is_auth = False

        target_cc = self.AUTH_CACHE_CTRL if is_auth else self.ANON_CACHE_CTRL

        # If existing header contains 'no-store' or 'private' or 'max-age=0' we won't overwrite
        # (assume the response author knows better). Otherwise set/replace it.
        if not existing_cc or (
            "no-store" not in existing_cc
            and "private" not in existing_cc
            and "max-age=0" not in existing_cc
        ):
            response["Cache-Control"] = target_cc

        # For authenticated responses ensure Vary includes Cookie (don't clobber existing Vary)
        if is_auth:
            vary = response.get("Vary")
            if vary:
                # append Cookie if not already present (respect case/spacing)
                vary_values = [v.strip() for v in vary.split(",") if v.strip()]
                if "Cookie" not in vary_values and "cookie" not in [
                    v.lower() for v in vary_values
                ]:
                    vary_values.append("Cookie")
                    response["Vary"] = ", ".join(vary_values)
            else:
                response["Vary"] = "Cookie"

        return response
