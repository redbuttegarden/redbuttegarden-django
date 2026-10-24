"""Focused tests for safe Instagram gallery ingestion and presentation."""

from __future__ import annotations

from datetime import datetime, timezone
from io import BytesIO
from importlib import import_module
from unittest.mock import patch

import requests

from django.apps import apps
from django.core.management.base import CommandError
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from wagtail.images.models import Image
from wagtail.images.tests.utils import get_test_image_file
from wagtail.models import Collection, Page

from home.management.commands.get_latest_social_media_images import (
    Command,
    get_trusted_instagram_download_url,
)
from home.models import HomePage, InstagramMedia
from home.utils import (
    DEFAULT_INSTAGRAM_PROFILE_URL,
    build_instagram_gallery_item,
    clean_alt_text,
    get_trusted_instagram_permalink,
)


class StreamingResponse:
    """Minimal streaming response used to test bounded remote downloads."""

    def __init__(
        self, chunks: list[bytes], content_length: str | None = None, status_code: int = 200
    ) -> None:
        self.chunks = chunks
        self.headers = {} if content_length is None else {"Content-Length": content_length}
        self.status_code = status_code

    def raise_for_status(self) -> None:
        """Represent a successful HTTP response."""

    def iter_content(self, chunk_size: int) -> list[bytes]:
        """Return the configured byte chunks without buffering a full response."""

        return self.chunks


class ApiResponse:
    """Minimal successful Graph response with a caller-controlled JSON body."""

    def __init__(self, payload: object) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        """Represent a successful HTTP response."""

    def json(self) -> object:
        """Return the configured JSON payload."""

        return self.payload


class InstagramGalleryUtilityTests(TestCase):
    """Test URL and accessible-text normalization at the display boundary."""

    def test_trusted_permalink_requires_https_instagram_host(self) -> None:
        """Only canonical HTTPS Instagram URLs are emitted as gallery links."""

        self.assertEqual(
            get_trusted_instagram_permalink("See https://www.instagram.com/p/example/ now"),
            "https://www.instagram.com/p/example/",
        )
        self.assertIsNone(get_trusted_instagram_permalink("http://instagram.com/p/example/"))
        self.assertIsNone(get_trusted_instagram_permalink("https://instagram.com.evil.test/p/example/"))
        self.assertIsNone(get_trusted_instagram_permalink("https://user@instagram.com/p/example/"))
        self.assertIsNone(get_trusted_instagram_permalink("https://instagram.com:444/p/example/"))
        self.assertIsNone(get_trusted_instagram_permalink("https://instagram.com:invalid/p/example/"))
        self.assertEqual(
            get_trusted_instagram_permalink("https://instagram.com:443/p/example/"),
            "https://instagram.com:443/p/example/",
        )

    def test_clean_alt_text_removes_urls_and_bounds_output(self) -> None:
        """Alt text is nonempty, readable, and never longer than its limit."""

        self.assertEqual(clean_alt_text("#Garden https://example.test/path"), "Garden")
        self.assertEqual(clean_alt_text("", max_length=8), "Instagra")
        self.assertLessEqual(len(clean_alt_text("word " * 20, max_length=20)), 20)

    def test_gallery_item_uses_profile_fallback_and_disambiguates_alt_text(self) -> None:
        """Legacy descriptions remain visible without exposing untrusted links."""

        image = Image(title="Legacy", description="https://example.test bad #caption")
        item = build_instagram_gallery_item(image, occurrence=2)
        self.assertEqual(item.url, DEFAULT_INSTAGRAM_PROFILE_URL)
        self.assertEqual(item.alt_text, "bad caption (Post 2)")


@override_settings(INSTAGRAM_APP_ID="account", FB_API_TOKEN="test-token")
class InstagramImporterTests(TestCase):
    """Test immutable media identity and safe remote-image handling."""

    def setUp(self) -> None:
        """Create the Wagtail collection used by the importer."""

        root = Collection.get_first_root_node()
        self.collection = root.add_child(instance=Collection(name="Instagram Data"))
        self.command = Command()

    def media_item(self, **overrides: object) -> dict[str, object]:
        """Return a valid API item that callers may specialize."""

        item: dict[str, object] = {
            "id": "123",
            "permalink": "https://www.instagram.com/p/example/",
            "thumbnail_url": "https://scontent-den2-1.xx.fbcdn.net/image.jpg",
            "caption": "Spring #flowers",
            "username": "redbuttegarden",
            "timestamp": "2025-01-02T03:04:05+00:00",
        }
        item.update(overrides)
        return item

    def test_trusted_download_url_rejects_unsafe_authorities_and_ports(self) -> None:
        """Download URL validation has the same authority safeguards as permalinks."""

        trusted_url = "https://scontent-den2-1.xx.fbcdn.net/image.jpg"
        self.assertEqual(get_trusted_instagram_download_url(trusted_url), trusted_url)
        self.assertEqual(
            get_trusted_instagram_download_url(
                "https://scontent-den2-1.xx.fbcdn.net:443/image.jpg"
            ),
            "https://scontent-den2-1.xx.fbcdn.net:443/image.jpg",
        )
        self.assertIsNone(
            get_trusted_instagram_download_url(
                "https://user@scontent-den2-1.xx.fbcdn.net/image.jpg"
            )
        )
        self.assertIsNone(
            get_trusted_instagram_download_url(
                "https://scontent-den2-1.xx.fbcdn.net:444/image.jpg"
            )
        )
        self.assertIsNone(
            get_trusted_instagram_download_url(
                "https://scontent-den2-1.xx.fbcdn.net:invalid/image.jpg"
            )
        )

    def test_reuses_legacy_image_and_updates_caption_without_download(self) -> None:
        """A legacy title is mapped by ID and never duplicated on later imports."""

        legacy = Image.objects.create(
            title="Instagram Image 123",
            file=get_test_image_file(filename="instagram-legacy.png"),
            collection=self.collection,
        )
        with patch.object(self.command, "_download_image") as download:
            self.command._import_media_item(self.media_item(caption="Changed caption"), self.collection)
            self.command._import_media_item(self.media_item(caption="Another caption"), self.collection)

        mapping = InstagramMedia.objects.get(external_id="123")
        legacy.refresh_from_db()
        self.assertEqual(mapping.image_id, legacy.id)
        self.assertEqual(Image.objects.filter(collection=self.collection).count(), 1)
        self.assertIn("Another caption", legacy.description)
        download.assert_not_called()

    def test_new_item_downloads_once_and_uses_external_id_not_caption(self) -> None:
        """Repeated IDs update presentation text but retain one stored image."""

        test_image = get_test_image_file(filename="instagram-new.png")
        test_image.seek(0)
        image_bytes = test_image.read()
        with patch.object(self.command, "_download_image", return_value=BytesIO(image_bytes)) as download:
            self.command._import_media_item(self.media_item(caption="Same caption"), self.collection)
            self.command._import_media_item(self.media_item(caption="Different caption"), self.collection)

        self.assertEqual(InstagramMedia.objects.filter(external_id="123").count(), 1)
        self.assertEqual(Image.objects.filter(collection=self.collection).count(), 1)
        download.assert_called_once()

    def test_new_image_uses_graph_timestamp_without_updating_existing_order(self) -> None:
        """New imports use the upstream timestamp and retain it on later refreshes."""

        test_image = get_test_image_file(filename="instagram-timestamp.png")
        test_image.seek(0)
        image_bytes = test_image.read()
        with patch.object(self.command, "_download_image", return_value=BytesIO(image_bytes)):
            self.command._import_media_item(self.media_item(), self.collection)
            image = InstagramMedia.objects.get(external_id="123").image
            self.command._import_media_item(
                self.media_item(timestamp="2030-01-01T00:00:00+00:00"), self.collection
            )

        image.refresh_from_db()
        self.assertEqual(image.created_at, datetime(2025, 1, 2, 3, 4, 5, tzinfo=timezone.utc))

    def test_invalid_image_payload_is_skipped_without_mapping_or_image(self) -> None:
        """A successful non-image response cannot create partial gallery records."""

        with patch.object(self.command, "_download_image", return_value=BytesIO(b"not an image")):
            self.command._import_media_item(self.media_item(), self.collection)

        self.assertFalse(InstagramMedia.objects.exists())
        self.assertFalse(Image.objects.filter(collection=self.collection).exists())

    def test_native_alt_text_takes_precedence_and_is_cleaned_and_bounded(self) -> None:
        """Native image labels override captions while still meeting alt-text constraints."""

        legacy = Image.objects.create(
            title="Instagram Image 123",
            file=get_test_image_file(filename="instagram-native-alt.png"),
            collection=self.collection,
        )
        native_alt = "#Native https://example.test/ " + ("description " * 30)
        self.command._import_media_item(
            self.media_item(caption="Caption should not be used", alt_text=native_alt),
            self.collection,
        )

        legacy.refresh_from_db()
        description = legacy.description.split(" ", 1)[1]
        self.assertTrue(description.startswith("Native"))
        self.assertNotIn("https://", description)
        self.assertNotIn("Caption should not be used", description)
        self.assertLessEqual(len(description), 180)

    def test_rejects_invalid_permalink_or_download_host(self) -> None:
        """No image is created for an untrusted public or download URL."""

        with patch.object(self.command, "_download_image") as download:
            self.command._import_media_item(self.media_item(permalink="https://example.test/post"), self.collection)
            self.command._import_media_item(self.media_item(thumbnail_url="https://example.test/image.jpg"), self.collection)

        self.assertFalse(InstagramMedia.objects.exists())
        download.assert_not_called()

    def test_rejects_non_numeric_or_oversized_media_ids_without_mappings(self) -> None:
        """External IDs are constrained before they reach database or file names."""

        with patch.object(self.command, "_download_image") as download:
            self.command._import_media_item(self.media_item(id="not-an-id"), self.collection)
            self.command._import_media_item(self.media_item(id="1" * 256), self.collection)

        self.assertFalse(InstagramMedia.objects.exists())
        download.assert_not_called()

    def test_missing_id_does_not_create_a_mapping(self) -> None:
        """Items without the immutable upstream identifier are ignored."""

        self.command._import_media_item(self.media_item(id=""), self.collection)

        self.assertFalse(InstagramMedia.objects.exists())

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=10)
    def test_download_rejects_declared_or_streamed_oversized_images(self) -> None:
        """The importer bounds both declared and chunked image downloads."""

        with patch(
            "home.management.commands.get_latest_social_media_images.requests.get",
            return_value=StreamingResponse([b"small"], content_length="11"),
        ):
            self.assertIsNone(self.command._download_image("https://scontent.xx.fbcdn.net/a", "123"))
        with patch(
            "home.management.commands.get_latest_social_media_images.requests.get",
            return_value=StreamingResponse([b"12345", b"678901"]),
        ):
            self.assertIsNone(self.command._download_image("https://scontent.xx.fbcdn.net/a", "123"))

    @override_settings(WAGTAILIMAGES_MAX_UPLOAD_SIZE=10)
    def test_download_streams_a_bounded_image(self) -> None:
        """Chunked images below the configured size limit are returned intact."""

        with patch(
            "home.management.commands.get_latest_social_media_images.requests.get",
            return_value=StreamingResponse([b"123", b"456"]),
        ):
            image_data = self.command._download_image("https://scontent.xx.fbcdn.net/a", "123")

        self.assertIsNotNone(image_data)
        self.assertEqual(image_data.read(), b"123456")

    def test_download_rejects_redirects(self) -> None:
        """Image redirects cannot change the validated download destination."""

        with patch(
            "home.management.commands.get_latest_social_media_images.requests.get",
            return_value=StreamingResponse([], status_code=302),
        ):
            self.assertIsNone(self.command._download_image("https://scontent.xx.fbcdn.net/a", "123"))

    def test_api_errors_raise_a_generic_command_error_without_token_logging(self) -> None:
        """API failures preserve neither exception details nor credentials in logs."""

        with patch(
            "home.management.commands.get_latest_social_media_images.requests.get",
            side_effect=requests.RequestException("test-token should not be logged"),
        ):
            with self.assertLogs("home.management.commands.get_latest_social_media_images", "ERROR") as logs:
                with self.assertRaises(CommandError):
                    self.command.handle()

        self.assertNotIn("test-token", " ".join(logs.output))

    def test_non_list_graph_data_raises_a_generic_command_error(self) -> None:
        """Malformed Graph data fields cannot reach importer iteration."""

        for invalid_data in (None, "not a list", 1, {}):
            with self.subTest(invalid_data=invalid_data):
                with patch(
                    "home.management.commands.get_latest_social_media_images.requests.get",
                    return_value=ApiResponse({"data": invalid_data}),
                ):
                    with self.assertLogs(
                        "home.management.commands.get_latest_social_media_images", "ERROR"
                    ) as logs:
                        with self.assertRaises(CommandError):
                            self.command.handle()

                self.assertEqual(
                    logs.output,
                    [
                        "ERROR:home.management.commands.get_latest_social_media_images:"
                        "Instagram media request returned an invalid data payload"
                    ],
                )

    def test_download_errors_do_not_log_signed_url_or_exception_text(self) -> None:
        """Download failures retain only the stable media ID in logs."""

        with patch(
            "home.management.commands.get_latest_social_media_images.requests.get",
            side_effect=requests.RequestException("signed-url-secret"),
        ):
            with self.assertLogs("home.management.commands.get_latest_social_media_images", "WARNING") as logs:
                self.command._download_image("https://scontent.xx.fbcdn.net/secret", "123")

        self.assertNotIn("signed-url-secret", " ".join(logs.output))
        self.assertNotIn("scontent", " ".join(logs.output))


class InstagramMigrationAndHomepageTests(TestCase):
    """Test legacy backfill and safe gallery context/template output."""

    def setUp(self) -> None:
        """Create gallery data and use the existing Wagtail homepage."""

        root = Collection.get_first_root_node()
        self.collection = root.add_child(instance=Collection(name="Instagram Data"))

    def create_image(self, title: str, description: str) -> Image:
        """Create a valid Wagtail image in the Instagram collection."""

        return Image.objects.create(
            title=title,
            description=description,
            collection=self.collection,
            file=get_test_image_file(filename=f"{title}.png"),
        )

    def test_migration_backfills_valid_titles_and_ignores_invalid_or_duplicate_ids(self) -> None:
        """Backfill maps valid historical IDs once without overwriting mappings."""

        valid_image = self.create_image("Instagram Image 456", "")
        self.create_image("Instagram Image ", "")
        self.create_image("Instagram Image non-numeric", "")
        preexisting_image = self.create_image("Current image", "")
        InstagramMedia.objects.create(external_id="789", image=preexisting_image)
        self.create_image("Instagram Image 789", "")

        migration = import_module("home.migrations.0115_instagrammedia")
        migration.backfill_legacy_instagram_media(apps, None)

        self.assertEqual(InstagramMedia.objects.get(external_id="456").image_id, valid_image.id)
        self.assertEqual(InstagramMedia.objects.get(external_id="789").image_id, preexisting_image.id)
        self.assertEqual(InstagramMedia.objects.count(), 2)

    def test_homepage_context_and_template_use_safe_links_and_accessible_labels(self) -> None:
        """Trusted links render while legacy links use the official profile fallback."""

        homepage = HomePage(title="Gallery home", slug="gallery-home")
        Page.get_first_root_node().add_child(instance=homepage)
        self.create_image("Trusted", "https://www.instagram.com/p/trusted/ Same #caption")
        self.create_image("Fallback", "https://example.test/post Same #caption")
        context = homepage.get_context(RequestFactory().get("/"))
        gallery_items = context["social_media_images_links"]

        self.assertEqual(len(gallery_items), 2)
        self.assertEqual(gallery_items[0].url, DEFAULT_INSTAGRAM_PROFILE_URL)
        self.assertEqual(gallery_items[1].url, "https://www.instagram.com/p/trusted/")
        self.assertTrue(all(item.alt_text for item in gallery_items))
        self.assertEqual({item.alt_text for item in gallery_items}, {"Same caption", "Same caption (Post 2)"})

        html = render_to_string(
            "home/includes/follow_us_images.html",
            {"images_and_links": gallery_items},
        )
        self.assertIn(DEFAULT_INSTAGRAM_PROFILE_URL, html)
        self.assertIn("https://www.instagram.com/p/trusted/", html)
        self.assertIn('alt="Same caption', html)
        self.assertIn("width=", html)
        self.assertIn("height=", html)
        self.assertIn('button type="button"', html)
        self.assertIn('aria-label="Show previous Instagram posts"', html)
        self.assertIn('aria-label="Show next Instagram posts"', html)
