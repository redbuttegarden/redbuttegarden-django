"""Regression tests for production security-setting literals."""

from __future__ import annotations

from urllib.parse import urlsplit

from redbuttegarden.settings import production


def test_production_cors_origins_are_https_origins() -> None:
    """Require each production CORS allow-list entry to be a full HTTPS origin."""

    assert production.CORS_ORIGIN_ALLOW_ALL is False
    for origin in production.CORS_ALLOWED_ORIGINS:
        parsed = urlsplit(origin)

        assert parsed.scheme == "https"
        assert parsed.netloc
        assert not parsed.path
        assert not parsed.query
        assert not parsed.fragment
