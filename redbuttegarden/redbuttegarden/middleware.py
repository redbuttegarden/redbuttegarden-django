from typing import Optional

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
        if not existing_cc or ("no-store" not in existing_cc and "private" not in existing_cc and "max-age=0" not in existing_cc):
            response["Cache-Control"] = target_cc

        # For authenticated responses ensure Vary includes Cookie (don't clobber existing Vary)
        if is_auth:
            vary = response.get("Vary")
            if vary:
                # append Cookie if not already present (respect case/spacing)
                vary_values = [v.strip() for v in vary.split(",") if v.strip()]
                if "Cookie" not in vary_values and "cookie" not in [v.lower() for v in vary_values]:
                    vary_values.append("Cookie")
                    response["Vary"] = ", ".join(vary_values)
            else:
                response["Vary"] = "Cookie"

        return response
