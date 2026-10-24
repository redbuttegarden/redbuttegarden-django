"""Safe presentation helpers for the homepage Instagram gallery."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlsplit

if TYPE_CHECKING:
    from wagtail.images.models import Image


DEFAULT_INSTAGRAM_PROFILE_URL = "https://www.instagram.com/redbuttegarden/"
INSTAGRAM_PERMALINK_HOSTS = frozenset({"instagram.com", "www.instagram.com"})
_URL_PATTERN = re.compile(r"https?://[^\s<>'\"]+")
_HASHTAG_PATTERN = re.compile(r"#([\w-]+)")


@dataclass(frozen=True)
class InstagramGalleryItem:
    """A validated Instagram gallery entry ready for template rendering."""

    image: Image
    url: str
    alt_text: str
    caption: str


def get_trusted_instagram_permalink(value: str | None) -> str | None:
    """Return the first trusted HTTPS Instagram permalink in ``value``."""

    if not value:
        return None
    for match in _URL_PATTERN.finditer(value):
        candidate = match.group(0).rstrip(".,;:!?")
        try:
            parsed = urlsplit(candidate)
            port = parsed.port
        except ValueError:
            continue
        if (
            parsed.scheme == "https"
            and parsed.hostname is not None
            and parsed.username is None
            and parsed.password is None
            and port in (None, 443)
            and parsed.hostname.lower().rstrip(".") in INSTAGRAM_PERMALINK_HOSTS
        ):
            return candidate
    return None


def clean_alt_text(text: str | None, max_length: int = 180) -> str:
    """Normalize native Instagram text or captions for a useful image label."""

    if max_length < 1:
        raise ValueError("max_length must be positive")
    normalized = _URL_PATTERN.sub("", text or "")
    normalized = _HASHTAG_PATTERN.sub(r"\1", normalized)
    normalized = " ".join(normalized.split())
    if not normalized:
        return "Instagram post image"[:max_length]
    if len(normalized) <= max_length:
        return normalized
    if max_length <= 3:
        return normalized[:max_length]
    shortened = normalized[: max_length - 3].rsplit(" ", 1)[0]
    return f"{shortened or normalized[: max_length - 3]}..."


def build_instagram_gallery_item(
    image: Image, occurrence: int = 1
) -> InstagramGalleryItem:
    """Build a safe, accessible gallery item from a Wagtail image record."""

    description = (image.description or "").strip()
    permalink = get_trusted_instagram_permalink(description)
    caption = description.replace(permalink, "").strip() if permalink else description
    alt_text = clean_alt_text(caption)
    if occurrence > 1:
        alt_text = f"{alt_text} (Post {occurrence})"
    return InstagramGalleryItem(
        image=image,
        url=permalink or DEFAULT_INSTAGRAM_PROFILE_URL,
        alt_text=alt_text,
        caption=caption,
    )
