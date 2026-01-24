from django.utils.deprecation import MiddlewareMixin

class HtmlCacheControlMiddleware(MiddlewareMixin):
    """
    For authenticated users: private, no-cache, must-revalidate, max-age=0
    For anonymous users: leave as-is (allow CDN to cache)
    Apply only to text/html responses.
    """
    AUTH_CACHE_CTRL = "private, no-cache, must-revalidate, max-age=0"
    ANON_CACHE_CTRL = "no-cache, must-revalidate, max-age=0, proxy-revalidate"

    def process_response(self, request, response):
        content_type = response.get("Content-Type", "")
        media_type = content_type.split(";", 1)[0].strip().lower()
        if media_type != "text/html":
            return response

        try:
            is_auth = bool(request.user and request.user.is_authenticated)
        except Exception:
            is_auth = False

        existing_cc = (response.get("Cache-Control") or "").lower()

        # If existing header contains 'no-store' or 'private' or 'max-age=0', respect it
        if not existing_cc or ("no-store" not in existing_cc and "private" not in existing_cc and "max-age=0" not in existing_cc):
            response["Cache-Control"] = self.AUTH_CACHE_CTRL if is_auth else self.ANON_CACHE_CTRL

        if is_auth:
            vary = response.get("Vary")
            if vary:
                vary_values = [v.strip() for v in vary.split(",") if v.strip()]
                if "Cookie" not in vary_values and "cookie" not in [v.lower() for v in vary_values]:
                    vary_values.append("Cookie")
                    response["Vary"] = ", ".join(vary_values)
            else:
                response["Vary"] = "Cookie"

        return response
