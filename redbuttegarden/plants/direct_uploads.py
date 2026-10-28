"""Private S3 staging and finalization services for BRAHMS image ingestion."""

from __future__ import annotations

import base64
import logging
import re
import uuid
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from django.utils.text import get_valid_filename
from wagtail.images.models import Image
from wagtail.models import Collection as WagtailCollection

from .models import BrahmsPendingUpload, Collection, Species
from .services import associate_brahms_image

logger = logging.getLogger(__name__)

MAX_BATCH_SIZE = 20
STAGING_PREFIX = "brahms-staging"
POST_EXPIRY_SECONDS = 900
PENDING_EXPIRY = timedelta(hours=24)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")


class DirectUploadError(Exception):
    """Base exception for safe direct-upload API outcomes."""


class DirectUploadConfigurationError(DirectUploadError):
    """Raised when the active Wagtail storage is not private S3 storage."""


class StagingObjectMissing(DirectUploadError):
    """Raised when a pending upload has no S3 staging object."""


class StagingObjectInvalid(DirectUploadError):
    """Raised when a staged object does not match its signed declaration."""


class StagingCopyFailed(DirectUploadError):
    """Raised when S3 cannot copy a verified object into Wagtail media."""


@dataclass(frozen=True)
class MediaStorageConfig:
    """The private S3 settings derived from Wagtail's active media storage."""

    bucket_name: str
    media_prefix: str
    region_name: str | None


def _media_storage_config() -> MediaStorageConfig:
    """Return the S3 bucket and prefix used by the configured Wagtail storage."""

    storage = default_storage
    bucket_name = getattr(storage, "bucket_name", None)
    media_prefix = getattr(storage, "location", None)
    if not isinstance(bucket_name, str) or not bucket_name:
        raise DirectUploadConfigurationError("The active media storage is not S3.")
    if not isinstance(media_prefix, str):
        raise DirectUploadConfigurationError("The active media storage has no S3 prefix.")

    region_name = getattr(storage, "region_name", None) or getattr(
        settings, "AWS_S3_REGION_NAME", None
    )
    return MediaStorageConfig(
        bucket_name=bucket_name,
        media_prefix=media_prefix.strip("/"),
        region_name=region_name,
    )


def _s3_client(config: MediaStorageConfig) -> Any:
    """Return the S3 client used for signing and object management."""

    return boto3.client("s3", region_name=config.region_name)


def _checksum_base64(sha256: str) -> str:
    """Encode a validated SHA-256 hex digest for S3 checksum headers."""

    return base64.b64encode(bytes.fromhex(sha256)).decode("ascii")


def _staging_key() -> str:
    """Return an opaque key under the sole permitted staging prefix."""

    return f"{STAGING_PREFIX}/{uuid.uuid4()}"


def _destination_name(pending: BrahmsPendingUpload) -> str:
    """Return the storage-relative Wagtail original-image name for one upload."""

    safe_filename = get_valid_filename(pending.original_filename) or "image"
    return f"original_images/brahms-{pending.pk}-{safe_filename}"


def _destination_key(config: MediaStorageConfig, pending: BrahmsPendingUpload) -> str:
    """Return the private S3 object key corresponding to a Wagtail file name."""

    filename = _destination_name(pending)
    return f"{config.media_prefix}/{filename}" if config.media_prefix else filename


def validate_direct_upload_metadata(item: dict[str, object]) -> tuple[str, str, int, int, int, str]:
    """Validate the file declaration before authorizing a direct S3 POST."""

    filename = item.get("original_filename")
    content_type = item.get("content_type")
    byte_size = item.get("byte_size")
    image_width = item.get("image_width")
    image_height = item.get("image_height")
    sha256 = item.get("sha256")
    max_size = int(settings.WAGTAILIMAGES_MAX_UPLOAD_SIZE)
    if not isinstance(filename, str) or not filename.strip():
        raise ValueError("original_filename must be a non-empty string.")
    if not isinstance(content_type, str) or not content_type.startswith("image/"):
        raise ValueError("content_type must be an image MIME type.")
    if isinstance(byte_size, bool) or not isinstance(byte_size, int) or byte_size <= 0:
        raise ValueError("byte_size must be a positive integer.")
    if byte_size > max_size:
        raise ValueError("byte_size exceeds the configured image upload limit.")
    if (
        isinstance(image_width, bool)
        or not isinstance(image_width, int)
        or image_width <= 0
    ):
        raise ValueError("image_width must be a positive integer.")
    if (
        isinstance(image_height, bool)
        or not isinstance(image_height, int)
        or image_height <= 0
    ):
        raise ValueError("image_height must be a positive integer.")
    if image_width * image_height > settings.WAGTAILIMAGES_MAX_IMAGE_PIXELS:
        raise ValueError("image dimensions exceed the configured pixel limit.")
    if not isinstance(sha256, str) or not SHA256_PATTERN.fullmatch(sha256.lower()):
        raise ValueError("sha256 must be a lowercase hexadecimal SHA-256 digest.")
    return filename, content_type, byte_size, image_width, image_height, sha256.lower()


def create_presigned_post(pending: BrahmsPendingUpload) -> dict[str, object]:
    """Create a short-lived, exact-key S3 POST policy for a pending upload."""

    config = _media_storage_config()
    checksum = _checksum_base64(pending.sha256)
    fields = {
        "key": pending.staging_key,
        "Content-Type": pending.content_type,
        "x-amz-meta-sha256": pending.sha256,
        "x-amz-meta-image-width": str(pending.image_width),
        "x-amz-meta-image-height": str(pending.image_height),
        "x-amz-checksum-sha256": checksum,
        "x-amz-server-side-encryption": "AES256",
    }
    conditions: list[object] = [
        {"key": pending.staging_key},
        {"Content-Type": pending.content_type},
        ["content-length-range", pending.byte_size, pending.byte_size],
        {"x-amz-meta-sha256": pending.sha256},
        {"x-amz-meta-image-width": str(pending.image_width)},
        {"x-amz-meta-image-height": str(pending.image_height)},
        {"x-amz-checksum-sha256": checksum},
        {"x-amz-server-side-encryption": "AES256"},
    ]
    return _s3_client(config).generate_presigned_post(
        Bucket=config.bucket_name,
        Key=pending.staging_key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=POST_EXPIRY_SECONDS,
    )


def _verified_staging_object(
    pending: BrahmsPendingUpload, config: MediaStorageConfig
) -> dict[str, object]:
    """Head and validate the private staged object against the pending declaration."""

    if not pending.staging_key.startswith(f"{STAGING_PREFIX}/"):
        raise StagingObjectInvalid("The pending upload has an invalid staging key.")
    try:
        response = _s3_client(config).head_object(
            Bucket=config.bucket_name, Key=pending.staging_key
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") in {"404", "NoSuchKey", "NotFound"}:
            raise StagingObjectMissing("The staged upload is missing.") from error
        raise StagingCopyFailed("Could not inspect the staged upload.") from error

    if response.get("ContentLength") != pending.byte_size:
        raise StagingObjectInvalid("The staged object size does not match.")
    if response.get("ContentType") != pending.content_type:
        raise StagingObjectInvalid("The staged object content type does not match.")
    metadata = response.get("Metadata", {})
    if metadata.get("sha256", "").lower() != pending.sha256:
        raise StagingObjectInvalid("The staged object checksum metadata does not match.")
    if metadata.get("image-width") != str(pending.image_width):
        raise StagingObjectInvalid("The staged object width metadata does not match.")
    if metadata.get("image-height") != str(pending.image_height):
        raise StagingObjectInvalid("The staged object height metadata does not match.")
    if response.get("ChecksumSHA256") not in (None, _checksum_base64(pending.sha256)):
        raise StagingObjectInvalid("The staged object checksum does not match.")
    if response.get("ServerSideEncryption") != "AES256":
        raise StagingObjectInvalid("The staged object encryption does not match.")
    return response


def _copy_staging_object(pending: BrahmsPendingUpload, config: MediaStorageConfig) -> str:
    """Copy a verified stage object to the active Wagtail media prefix."""

    destination_key = _destination_key(config, pending)
    try:
        _s3_client(config).copy_object(
            Bucket=config.bucket_name,
            Key=destination_key,
            CopySource={"Bucket": config.bucket_name, "Key": pending.staging_key},
            MetadataDirective="COPY",
            ServerSideEncryption="AES256",
        )
    except ClientError as error:
        raise StagingCopyFailed("Could not copy the staged upload.") from error
    return _destination_name(pending)


def _delete_destination_object(
    pending: BrahmsPendingUpload, config: MediaStorageConfig
) -> None:
    """Best-effort remove a copied media object after finalization fails.

    The copy is outside the database transaction. Removing the destination here
    prevents a failed Wagtail record or relationship write from leaving a
    private, unreachable media object behind.
    """

    try:
        _s3_client(config).delete_object(
            Bucket=config.bucket_name, Key=_destination_key(config, pending)
        )
    except ClientError:
        logger.exception("Could not remove failed BRAHMS media copy.")


def _create_or_reuse_image(
    pending: BrahmsPendingUpload, storage_name: str
) -> tuple[Image, bool]:
    """Create the Wagtail record after S3 copy, retaining title idempotency."""

    return Image.objects.get_or_create(
        title=pending.original_filename,
        defaults={
            "file": storage_name,
            "collection": WagtailCollection.objects.get(name="BRAHMS Data"),
            # The client declares dimensions at initiation. Keeping them on the
            # instance prevents Django's ImageField descriptor from opening
            # the just-copied S3 object to recalculate them in Lambda.
            "width": pending.image_width,
            "height": pending.image_height,
            "file_size": pending.byte_size,
            # Wagtail stores a SHA-1-sized (40-character) file hash here. The
            # pending record retains the verified SHA-256 instead; assigning it
            # here would exceed the database column and force no useful read.
            "file_hash": "",
        },
    )


def finalize_pending_upload(pending: BrahmsPendingUpload) -> tuple[Image, bool]:
    """Verify, copy, and associate one owned pending upload exactly once."""

    config = _media_storage_config()
    _verified_staging_object(pending, config)

    copied_destination = False
    try:
        existing_image = Image.objects.filter(title=pending.original_filename).first()
        if existing_image is None:
            storage_name = _copy_staging_object(pending, config)
            copied_destination = True
            image, image_created = _create_or_reuse_image(pending, storage_name)
            if image_created:
                image.tags.add("BRAHMS")
        else:
            image = existing_image

        target: Collection | Species = pending.collection or pending.species  # type: ignore[assignment]
        association_created = associate_brahms_image(image, target, pending.copyright_info)
        return image, association_created
    except Exception:
        if copied_destination:
            _delete_destination_object(pending, config)
        raise


def delete_staging_object(pending: BrahmsPendingUpload) -> None:
    """Remove a finalized staging object; lifecycle handles a retry failure."""

    config = _media_storage_config()
    try:
        _s3_client(config).delete_object(
            Bucket=config.bucket_name, Key=pending.staging_key
        )
    except ClientError:
        logger.exception("Could not delete finalized BRAHMS staging object.")


def purge_expired_pending_uploads() -> int:
    """Delete all expired direct-upload outcome rows after their retention window."""

    deleted, _ = BrahmsPendingUpload.objects.filter(expires_at__lt=timezone.now()).delete()
    return deleted
