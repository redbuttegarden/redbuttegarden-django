import hashlib

from django.utils.http import quote_etag
from django.template.response import TemplateResponse
from django.utils.deprecation import MiddlewareMixin
from typing import Optional


class EnsureRenderedAndSetETagMiddleware(MiddlewareMixin):
    """
    Render TemplateResponse objects early and set an ETag for non-streaming
    responses that don't already have one.

    Behavior:
    - Renders TemplateResponse (Wagtail pages return TemplateResponse).
    - Skips streaming responses.
    - Respects existing ETag / Last-Modified set by views or other middleware.
    - Computes SHA1 of response.content and sets a quoted ETag.
    """

    # Optional: configure a max size to avoid hashing very large pages.
    # If you have very large HTML responses you can set MAX_HASH_SIZE to a value
    # in bytes (e.g. 200_000) and the middleware will skip hashing larger bodies.
    MAX_HASH_SIZE = None  # or e.g. 200_000

    def _compute_etag(self, content: bytes) -> str:
        digest = hashlib.sha1(content).hexdigest()
        return quote_etag(digest)

    def process_template_response(self, request, response):
        # Ensure TemplateResponse is rendered so we can compute ETag from final body.
        if isinstance(response, TemplateResponse) and not response.is_rendered:
            response.render()
        return response

    def process_response(self, request, response):
        # Skip if no content attribute or streaming response
        try:
            content = getattr(response, "content", None)
        except Exception:
            content = None

        if content is None:
            return response

        if getattr(response, "streaming", False):
            return response

        # Do not override existing validators
        if response.has_header("ETag") or response.has_header("Last-Modified"):
            return response

        # Only compute on typical successful responses
        if response.status_code not in (200, 203, 206):
            return response

        # Optional size guard
        if self.MAX_HASH_SIZE is not None:
            try:
                if len(content) > self.MAX_HASH_SIZE:
                    return response
            except Exception:
                # If length check fails, continue without the guard
                pass

        # Compute and set ETag
        try:
            etag = self._compute_etag(content)
            response["ETag"] = etag
        except Exception:
            # Be conservative — don't fail requests if hashing fails
            pass

        return response


class HtmlCacheControlMiddleware(MiddlewareMixin):
    """
    Middleware to set sane Cache-Control for HTML responses.

    With personalization moved to a client-side fragment, the main HTML should be
    cacheable at shared caches (CloudFront) and revalidation-friendly (ETag/304).
    This middleware:
      - Leaves responses that already include explicit 'no-store'/'private'
        or a non-zero max-age alone.
      - For HTML responses without explicit restrictive headers, sets a
        public revalidation-friendly Cache-Control that allows shared caches to cache
        and use s-maxage for CDN TTL while still allowing conditional GET revalidation.
      - Does NOT set Vary: Cookie for main HTML. Per-user fragments should set Vary/Cookie.
    """

    # Default we will apply if nothing more restrictive exists
    # - max-age=0 encourages revalidation
    # - s-maxage set to 30 minutes
    # - must-revalidate/proxy-revalidate allow proper revalidation semantics
    DEFAULT_CACHE_CTRL = (
        "public, max-age=0, s-maxage=1800, must-revalidate, proxy-revalidate"
    )

    def _media_type(self, response) -> Optional[str]:
        content_type = response.get("Content-Type", "")
        return content_type.split(";", 1)[0].strip().lower() if content_type else None

    def __call__(self, request):
        response = self.get_response(request)

        media_type = self._media_type(response)
        if media_type != "text/html":
            return response

        # Respect explicit unsafe headers from view/origin:
        existing_cc = (response.get("Cache-Control") or "").lower()

        # If response explicitly forbids caching or is already private, do not overwrite.
        # Treat presence of 'no-store' or 'private' or an explicit positive max-age as authoritative.
        if existing_cc:
            # If the existing header already contains s-maxage or public or max-age, keep it.
            # We only override when no restrictive flags exist and header is empty/unspecified.
            if ("no-store" in existing_cc) or ("private" in existing_cc):
                return response
            if (
                "max-age" in existing_cc
                or "s-maxage" in existing_cc
                or "public" in existing_cc
            ):
                return response

        # No explicit policy from upstream: set our default Cache-Control for main HTML.
        response["Cache-Control"] = self.DEFAULT_CACHE_CTRL

        # Ensure we do NOT set Vary: Cookie for the main HTML.
        # If a view accidentally set Vary: Cookie for HTML, we prefer to remove it here
        # because fragment approach uses separate endpoint to vary by cookie.
        vary = response.get("Vary")
        if vary:
            # remove Cookie from Vary if present (preserve other tokens)
            parts = [v.strip() for v in vary.split(",") if v.strip()]
            parts = [p for p in parts if p.lower() != "cookie"]
            if parts:
                response["Vary"] = ", ".join(parts)
            else:
                # remove Vary header entirely if empty
                try:
                    del response["Vary"]
                except KeyError:
                    pass

        return response
