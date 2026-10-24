"""Import recent Instagram media into the Wagtail Instagram collection."""

from __future__ import annotations

import logging
from datetime import datetime, timezone as datetime_timezone
from io import BytesIO
from typing import Any
from urllib.parse import urlsplit

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from wagtail.images.models import Image
from wagtail.models import Collection as WagtailCollection
from willow.image import UnrecognisedImageFormatError

from home.models import InstagramMedia
from home.utils import clean_alt_text, get_trusted_instagram_permalink

logger = logging.getLogger(__name__)

FACEBOOK_BASE_URL = "https://graph.facebook.com"
FACEBOOK_API_VERSION = "v22.0"
REQUEST_TIMEOUT_SECONDS = 5
IMAGE_DOWNLOAD_HOST_SUFFIXES = (".fbcdn.net", ".cdninstagram.com")
DEFAULT_MAX_IMAGE_DOWNLOAD_BYTES = 4_500_000
IMAGE_DOWNLOAD_CHUNK_SIZE = 64 * 1024


def get_trusted_instagram_download_url(value: str | None) -> str | None:
    """Return a trusted HTTPS Meta CDN image URL, if ``value`` is safe."""

    if not value:
        return None
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError:
        return None
    hostname = (parsed.hostname or "").lower().rstrip(".")
    if (
        parsed.scheme == "https"
        and parsed.username is None
        and parsed.password is None
        and port in (None, 443)
        and hostname.endswith(IMAGE_DOWNLOAD_HOST_SUFFIXES)
    ):
        return value
    return None


def build_image_title(username: str | None, caption: str | None, media_id: str) -> str:
    """Return a short editor-facing title without using it as media identity."""

    account_name = (username or "Instagram").lstrip("@") or "Instagram"
    caption_snippet = clean_alt_text(caption, max_length=60)
    if caption_snippet != "Instagram post image":
        return f"@{account_name}: {caption_snippet}"[:255]
    return f"Instagram post by @{account_name} ({media_id})"[:255]


def get_max_image_download_bytes() -> int:
    """Return the configured Wagtail image limit with a safe fallback."""

    configured_limit = getattr(
        settings, "WAGTAILIMAGES_MAX_UPLOAD_SIZE", DEFAULT_MAX_IMAGE_DOWNLOAD_BYTES
    )
    if isinstance(configured_limit, (int, float)) and configured_limit > 0:
        return int(configured_limit)
    return DEFAULT_MAX_IMAGE_DOWNLOAD_BYTES


def parse_media_timestamp(value: str | None) -> datetime | None:
    """Parse an Instagram timestamp into an aware datetime, if valid."""

    parsed_timestamp = parse_datetime(value) if value else None
    if parsed_timestamp is None:
        return None
    if timezone.is_naive(parsed_timestamp):
        return timezone.make_aware(parsed_timestamp, datetime_timezone.utc)
    return parsed_timestamp


class Command(BaseCommand):
    """Fetch and store the ten most recent Instagram gallery images."""

    help = "Get latest social media images and save them to the database"

    def handle(self, *args: Any, **options: Any) -> str | None:
        """Import current media while keeping remote details out of logs."""

        media_url = (
            f"{FACEBOOK_BASE_URL}/{FACEBOOK_API_VERSION}/"
            f"{settings.INSTAGRAM_APP_ID}/media"
        )
        params = (
            ("access_token", settings.FB_API_TOKEN),
            (
                "fields",
                "id,media_type,media_url,permalink,thumbnail_url,timestamp,"
                "username,caption,alt_text",
            ),
            ("limit", 10),
        )
        try:
            response = requests.get(media_url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError):
            logger.error("Instagram media request failed")
            raise CommandError("Failed response while retrieving latest media data")
        if not isinstance(payload, dict):
            logger.error("Instagram media request returned an invalid payload")
            raise CommandError("Failed response while retrieving latest media data")
        data = payload.get("data")
        if not isinstance(data, list):
            logger.error("Instagram media request returned an invalid data payload")
            raise CommandError("Failed response while retrieving latest media data")
        collection = self._get_instagram_collection()
        if collection is None:
            return None
        for media_item in data:
            if isinstance(media_item, dict):
                self._import_media_item(media_item, collection)
        return None

    def _get_instagram_collection(self) -> WagtailCollection | None:
        """Return the configured gallery collection, logging a safe error if absent."""

        try:
            return WagtailCollection.objects.get(name="Instagram Data")
        except WagtailCollection.DoesNotExist:
            logger.error("Instagram Data collection is missing; media import skipped")
            return None

    def _import_media_item(
        self, media_item: dict[str, Any], collection: WagtailCollection
    ) -> None:
        """Create or update one API media item using its immutable external ID."""

        media_id = str(media_item.get("id") or "").strip()
        raw_permalink = media_item.get("permalink")
        permalink = get_trusted_instagram_permalink(
            raw_permalink if isinstance(raw_permalink, str) else None
        )
        download_url = media_item.get("thumbnail_url") or media_item.get("media_url")
        download_url = download_url if isinstance(download_url, str) else None
        raw_timestamp = media_item.get("timestamp")
        timestamp = parse_media_timestamp(
            raw_timestamp if isinstance(raw_timestamp, str) else None
        )
        if not media_id.isascii() or not media_id.isdecimal() or len(media_id) > 255:
            logger.warning("Instagram media item skipped because its ID is invalid")
            return
        if not permalink:
            logger.warning("Instagram media item skipped because its ID or permalink is invalid")
            return
        native_alt_text = media_item.get("alt_text")
        caption = media_item.get("caption")
        native_alt_text = native_alt_text if isinstance(native_alt_text, str) else None
        caption = caption if isinstance(caption, str) else None
        accessible_text = clean_alt_text(native_alt_text or caption)
        description = f"{permalink} {accessible_text}"[:255]
        username = media_item.get("username")
        title = build_image_title(
            username if isinstance(username, str) else None, caption, media_id
        )
        with transaction.atomic():
            mapping = self._get_mapping(media_id)
            if mapping.image_id is None:
                legacy_image = (
                    Image.objects.select_for_update()
                    .filter(title=f"Instagram Image {media_id}")
                    .order_by("id")
                    .first()
                )
                if legacy_image is not None:
                    mapping = self._get_or_create_mapping(media_id)
                    if mapping.image_id is None:
                        mapping.image = legacy_image
                        mapping.save(update_fields=["image"])
                else:
                    download_url = get_trusted_instagram_download_url(download_url)
                    if download_url is None:
                        logger.warning("Instagram media %s skipped because its download host is invalid", media_id)
                        return
                    if timestamp is None:
                        logger.warning("Instagram media %s skipped because its timestamp is invalid", media_id)
                        return
                    image_data = self._download_image(download_url, media_id)
                    if image_data is None:
                        return
                    try:
                        image = Image(
                            title=title,
                            file=ImageFile(image_data, name=f"instagram_{media_id}.jpg"),
                            collection=collection,
                            description=description,
                        )
                        mapping = self._get_or_create_mapping(media_id)
                        if mapping.image_id is not None:
                            image = mapping.image
                            if image is not None:
                                image.title = title
                                image.description = description
                                image.save(update_fields=["title", "description"])
                            return
                        image.save()
                        Image.objects.filter(pk=image.pk).update(created_at=timestamp)
                        image.created_at = timestamp
                        image.tags.add("Instagram")
                        mapping.image = image
                        mapping.save(update_fields=["image"])
                    except (OSError, UnrecognisedImageFormatError, ValidationError, ValueError):
                        logger.warning("Instagram media %s image data is invalid", media_id)
                        transaction.set_rollback(True)
                        return
            image = mapping.image
            if image is not None:
                image.title = title
                image.description = description
                image.save(update_fields=["title", "description"])

    def _get_mapping(self, media_id: str) -> InstagramMedia:
        """Return a locked mapping or an unsaved mapping placeholder."""

        try:
            return InstagramMedia.objects.select_for_update().get(external_id=media_id)
        except InstagramMedia.DoesNotExist:
            return InstagramMedia(external_id=media_id)

    def _get_or_create_mapping(self, media_id: str) -> InstagramMedia:
        """Lock an existing mapping or safely create one for a new media ID."""

        try:
            return InstagramMedia.objects.select_for_update().get(external_id=media_id)
        except InstagramMedia.DoesNotExist:
            try:
                with transaction.atomic():
                    return InstagramMedia.objects.create(external_id=media_id)
            except IntegrityError:
                return InstagramMedia.objects.select_for_update().get(
                    external_id=media_id
                )

    def _download_image(self, download_url: str, media_id: str) -> BytesIO | None:
        """Download a validated image URL without following redirects."""

        try:
            response = requests.get(
                download_url,
                stream=True,
                timeout=REQUEST_TIMEOUT_SECONDS,
                allow_redirects=False,
            )
            response.raise_for_status()
            if 300 <= response.status_code < 400:
                raise requests.RequestException("unexpected redirect")
        except requests.RequestException:
            logger.warning("Instagram media %s image download failed", media_id)
            return None
        maximum_size = get_max_image_download_bytes()
        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                if int(content_length) > maximum_size:
                    logger.warning("Instagram media %s image download exceeds size limit", media_id)
                    return None
            except ValueError:
                pass

        image_data = BytesIO()
        try:
            for chunk in response.iter_content(chunk_size=IMAGE_DOWNLOAD_CHUNK_SIZE):
                if not chunk:
                    continue
                if image_data.tell() + len(chunk) > maximum_size:
                    logger.warning("Instagram media %s image download exceeds size limit", media_id)
                    return None
                image_data.write(chunk)
        except requests.RequestException:
            logger.warning("Instagram media %s image download failed", media_id)
            return None
        image_data.seek(0)
        return image_data
