"""Regression coverage for private direct-to-S3 BRAHMS image ingestion."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from django.contrib.auth import get_user_model
from django.core.files.images import ImageFile
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone
from PIL import Image as PillowImage
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient
from wagtail.images import get_image_model
from wagtail.models import Collection as WagtailCollection

from plants.direct_uploads import (
    MediaStorageConfig,
    StagingObjectInvalid,
    StagingObjectMissing,
    _copy_staging_object,
    _create_or_reuse_image,
    _verified_staging_object,
    create_presigned_post,
    finalize_pending_upload,
    purge_expired_pending_uploads,
)
from plants.models import BrahmsPendingUpload
from plants.tests.utils import get_collection, get_custom_user


SHA256 = "a" * 64


def _authenticated_client(user=None) -> tuple[APIClient, object]:
    """Return a token-authenticated client and its owning user."""

    user = user or get_custom_user("direct-uploader")
    token = Token.objects.create(user=user)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")
    return client, user


def _payload(plant_id: str, **overrides: object) -> dict[str, object]:
    """Return one valid direct-upload initiation item."""

    payload: dict[str, object] = {
        "client_id": "client-photo",
        "plant_id": plant_id,
        "copyright_info": "RBG",
        "original_filename": "photo.jpg",
        "content_type": "image/jpeg",
        "byte_size": 123,
        "image_width": 10,
        "image_height": 12,
        "sha256": SHA256,
    }
    payload.update(overrides)
    return payload


def _pending(owner, plant, **overrides: object) -> BrahmsPendingUpload:
    """Create a pending upload with the required server-validated metadata."""

    values: dict[str, object] = {
        "owner": owner,
        "client_id": "pending-client",
        "collection": plant,
        "original_filename": "photo.jpg",
        "copyright_info": "RBG",
        "content_type": "image/jpeg",
        "byte_size": 123,
        "image_width": 10,
        "image_height": 12,
        "sha256": SHA256,
        "staging_key": "brahms-staging/test-key",
        "expires_at": timezone.now() + timedelta(hours=1),
    }
    values.update(overrides)
    return BrahmsPendingUpload.objects.create(**values)


@pytest.mark.django_db
def test_direct_upload_initiation_requires_authentication():
    """Direct-upload authorization keeps the existing API authentication boundary."""

    response = APIClient().post(
        reverse("plants:api-direct-upload-initiate"), {"uploads": []}, format="json"
    )

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_initiate_validates_target_metadata_and_size_before_signing():
    """Bad targets or oversized metadata do not create pending S3 authorizations."""

    plant = get_collection(plant_id="direct-validate")
    client, _ = _authenticated_client()
    endpoint = reverse("plants:api-direct-upload-initiate")
    oversized = _payload(plant.plant_id, client_id="large", byte_size=9_999_999)
    invalid_target = _payload(
        plant.plant_id,
        client_id="two-targets",
        species={"genus": "bad"},
    )

    response = client.post(endpoint, {"uploads": [oversized, invalid_target]}, format="json")

    assert response.status_code == 200
    assert [item["code"] for item in response.json()["results"]] == [
        "invalid_upload",
        "invalid_upload",
    ]
    assert not BrahmsPendingUpload.objects.exists()


@pytest.mark.django_db
def test_initiate_creates_owned_pending_upload_and_returns_private_policy():
    """A valid item persists only server-selected S3 state and returns a POST policy."""

    plant = get_collection(plant_id="direct-initiate")
    client, user = _authenticated_client()
    signed_post = {"url": "https://bucket.example", "fields": {"key": "opaque"}}
    with patch("plants.views.create_presigned_post", return_value=signed_post) as signer:
        response = client.post(
            reverse("plants:api-direct-upload-initiate"),
            {"uploads": [_payload(plant.plant_id)]},
            format="json",
        )

    assert response.status_code == 200
    result = response.json()["results"][0]
    pending = BrahmsPendingUpload.objects.get(pk=result["pending_id"])
    assert pending.owner == user
    assert pending.collection == plant
    assert pending.staging_key.startswith("brahms-staging/")
    assert pending.staging_key != "opaque"
    assert result["upload"] == signed_post
    signer.assert_called_once_with(pending)


@pytest.mark.django_db
def test_initiate_rejects_client_id_retries_with_changed_target_or_copyright():
    """A retry cannot repurpose an existing pending upload's target or copyright."""

    plant = get_collection(plant_id="direct-retry-original")
    other_plant = get_collection(plant_id="direct-retry-other")
    client, _ = _authenticated_client()
    endpoint = reverse("plants:api-direct-upload-initiate")
    signed_post = {"url": "https://bucket.example", "fields": {"key": "opaque"}}
    species_target = {
        "genus": plant.species.genus.name,
        "name": plant.species.name,
        "subspecies": plant.species.subspecies,
        "variety": plant.species.variety,
        "subvariety": plant.species.subvariety,
        "forma": plant.species.forma,
        "subforma": plant.species.subforma,
        "cultivar": plant.species.cultivar,
    }
    original = _payload(plant.plant_id)
    changed_plant = _payload(other_plant.plant_id)
    changed_species = _payload(plant.plant_id)
    changed_species.pop("plant_id")
    changed_species["species"] = species_target
    changed_copyright = _payload(plant.plant_id, copyright_info="Other copyright")

    with patch("plants.views.create_presigned_post", return_value=signed_post) as signer:
        response = client.post(
            endpoint,
            {"uploads": [original, changed_plant, changed_species, changed_copyright]},
            format="json",
        )

    results = response.json()["results"]
    assert results[0]["status"] == "success"
    assert [result["code"] for result in results[1:]] == [
        "client_id_conflict",
        "client_id_conflict",
        "client_id_conflict",
    ]
    pending = BrahmsPendingUpload.objects.get(owner__username="direct-uploader")
    assert pending.collection == plant
    assert pending.species is None
    assert pending.copyright_info == "RBG"
    signer.assert_called_once_with(pending)


def test_presigned_post_strictly_constrains_private_upload_metadata():
    """The S3 policy fixes key, size, MIME, checksum, encryption, and expiry."""

    pending = SimpleNamespace(
        staging_key="brahms-staging/opaque-id",
        content_type="image/jpeg",
        byte_size=123,
        image_width=10,
        image_height=12,
        sha256=SHA256,
    )
    s3 = Mock()
    s3.generate_presigned_post.return_value = {"url": "https://s3.example", "fields": {}}
    with patch(
        "plants.direct_uploads._media_storage_config",
        return_value=MediaStorageConfig("private-bucket", "media", "us-east-1"),
    ), patch("plants.direct_uploads._s3_client", return_value=s3):
        create_presigned_post(pending)

    kwargs = s3.generate_presigned_post.call_args.kwargs
    assert kwargs["Bucket"] == "private-bucket"
    assert kwargs["Key"] == "brahms-staging/opaque-id"
    assert kwargs["ExpiresIn"] == 900
    assert {"key": "brahms-staging/opaque-id"} in kwargs["Conditions"]
    assert ["content-length-range", 123, 123] in kwargs["Conditions"]
    assert {"Content-Type": "image/jpeg"} in kwargs["Conditions"]
    assert {"x-amz-meta-image-width": "10"} in kwargs["Conditions"]
    assert {"x-amz-meta-image-height": "12"} in kwargs["Conditions"]
    assert {"x-amz-server-side-encryption": "AES256"} in kwargs["Conditions"]
    assert kwargs["Fields"]["x-amz-meta-sha256"] == SHA256
    assert kwargs["Fields"]["x-amz-meta-image-width"] == "10"
    assert kwargs["Fields"]["x-amz-meta-image-height"] == "12"
    assert kwargs["Fields"]["x-amz-checksum-sha256"]


@pytest.mark.django_db
def test_finalize_rejects_foreign_and_expired_pending_uploads():
    """Finalize never reveals or processes another user's pending upload."""

    plant = get_collection(plant_id="direct-owner")
    owner = get_custom_user("direct-owner")
    foreign_client, _ = _authenticated_client(get_custom_user("direct-foreign"))
    pending = _pending(owner, plant)
    foreign = foreign_client.post(
        reverse("plants:api-direct-upload-finalize"),
        {"uploads": [{"pending_id": str(pending.pk)}]},
        format="json",
    )
    assert foreign.json()["results"][0]["code"] == "pending_not_found"

    owner_client, _ = _authenticated_client(owner)
    pending.expires_at = timezone.now() - timedelta(seconds=1)
    pending.save(update_fields=["expires_at"])
    expired = owner_client.post(
        reverse("plants:api-direct-upload-finalize"),
        {"uploads": [{"pending_id": str(pending.pk)}]},
        format="json",
    )
    assert expired.json()["results"][0]["code"] == "upload_expired"


@pytest.mark.django_db
@pytest.mark.parametrize("failure, code", [(StagingObjectMissing("missing"), "staging_not_found"), (StagingObjectInvalid("bad"), "staging_invalid")])
def test_finalize_reports_staging_verification_failures(failure, code):
    """Object verification failures are item errors and retain the pending record."""

    plant = get_collection(plant_id=f"direct-{code}")
    client, owner = _authenticated_client()
    pending = _pending(owner, plant)
    with patch("plants.views.finalize_pending_upload", side_effect=failure):
        response = client.post(
            reverse("plants:api-direct-upload-finalize"),
            {"uploads": [{"pending_id": str(pending.pk)}]},
            format="json",
        )

    assert response.status_code == 200
    assert response.json()["results"][0]["code"] == code
    pending.refresh_from_db()
    assert pending.finalized_at is None


def _test_image_file(name: str = "direct.jpg") -> ImageFile:
    """Build a tiny valid local image used only for Wagtail test records."""

    from io import BytesIO

    stream = BytesIO()
    PillowImage.new("RGB", (10, 12), color=(255, 0, 0)).save(stream, "JPEG")
    stream.seek(0)
    return ImageFile(stream, name=name)


@pytest.mark.django_db
def test_finalize_succeeds_for_plant_and_species_and_is_idempotent():
    """Finalize stores success once, cleans staging, and returns that state on retry."""

    root = WagtailCollection.get_first_root_node()
    if root is None:
        root = WagtailCollection.add_root(name="Root")
    brahms = root.add_child(name="BRAHMS Data")
    plant = get_collection(plant_id="direct-success")
    client, owner = _authenticated_client()
    ImageModel = get_image_model()
    image = ImageModel.objects.create(
        title="direct-final.jpg", file=_test_image_file(), collection=brahms
    )
    plant_pending = _pending(owner, plant, client_id="plant-final")
    species_pending = _pending(
        owner,
        plant,
        client_id="species-final",
        collection=None,
        species=plant.species,
        staging_key="brahms-staging/species-key",
    )
    endpoint = reverse("plants:api-direct-upload-finalize")
    with patch("plants.views.finalize_pending_upload", side_effect=[(image, True), (image, True)]) as finalize, patch(
        "plants.views.delete_staging_object"
    ) as cleanup:
        response = client.post(
            endpoint,
            {"uploads": [{"pending_id": str(plant_pending.pk)}, {"pending_id": str(species_pending.pk)}]},
            format="json",
        )
        retry = client.post(
            endpoint,
            {"uploads": [{"pending_id": str(plant_pending.pk)}]},
            format="json",
        )

    assert [result["status"] for result in response.json()["results"]] == ["success", "success"]
    assert retry.json()["results"] == [
        {"client_id": "plant-final", "status": "success", "created": True, "finalized": True}
    ]
    assert finalize.call_count == 2
    assert cleanup.call_count == 2


def test_wagtail_record_uses_client_dimensions_without_opening_s3_bytes():
    """Copied S3 files are registered with complete Wagtail metadata, not reopened."""

    pending = SimpleNamespace(
        original_filename="copied.jpg",
        image_width=1200,
        image_height=800,
        byte_size=345,
        sha256=SHA256,
    )
    image_manager = Mock()
    image_manager.get_or_create.return_value = (Mock(), True)
    with patch("plants.direct_uploads.Image.objects", image_manager), patch(
        "plants.direct_uploads.WagtailCollection.objects.get", return_value=Mock()
    ):
        _create_or_reuse_image(pending, "original_images/copied.jpg")

    defaults = image_manager.get_or_create.call_args.kwargs["defaults"]
    assert defaults["width"] == 1200
    assert defaults["height"] == 800
    assert defaults["file_size"] == 345
    # Wagtail's file_hash column is SHA-1-sized. The verified SHA-256 remains
    # on BrahmsPendingUpload rather than causing a database error here.
    assert defaults["file_hash"] == ""


def test_server_side_copy_preserves_verified_content_metadata():
    """Copying retains the staged content type without conflicting S3 directives."""

    pending = SimpleNamespace(
        pk="opaque-id",
        original_filename="copied.jpg",
        staging_key="brahms-staging/opaque-id",
        content_type="image/jpeg",
    )
    config = MediaStorageConfig("private-bucket", "media", "us-east-1")
    s3 = Mock()
    with patch("plants.direct_uploads._s3_client", return_value=s3):
        _copy_staging_object(pending, config)

    kwargs = s3.copy_object.call_args.kwargs
    assert kwargs["MetadataDirective"] == "COPY"
    assert "ContentType" not in kwargs
    assert kwargs["ServerSideEncryption"] == "AES256"


def test_finalize_rejects_staged_dimension_metadata_mismatch():
    """Finalization requires the same dimensions that the signed POST fixed."""

    pending = SimpleNamespace(
        staging_key="brahms-staging/opaque-id",
        byte_size=123,
        content_type="image/jpeg",
        image_width=10,
        image_height=12,
        sha256=SHA256,
    )
    s3 = Mock()
    s3.head_object.return_value = {
        "ContentLength": 123,
        "ContentType": "image/jpeg",
        "Metadata": {
            "sha256": SHA256,
            "image-width": "9",
            "image-height": "12",
        },
        "ServerSideEncryption": "AES256",
    }
    with patch("plants.direct_uploads._s3_client", return_value=s3):
        with pytest.raises(StagingObjectInvalid, match="width metadata"):
            _verified_staging_object(
                pending, MediaStorageConfig("private-bucket", "media", "us-east-1")
            )


@pytest.mark.django_db
def test_expired_upload_purge_removes_finalized_and_unfinished_rows():
    """The 24-hour retention job removes both pending and result-state rows."""

    plant = get_collection(plant_id="direct-purge")
    owner = get_custom_user("direct-purge")
    expired = timezone.now() - timedelta(seconds=1)
    unfinished = _pending(owner, plant, client_id="purge-unfinished", expires_at=expired)
    finalized = _pending(
        owner,
        plant,
        client_id="purge-finalized",
        staging_key="brahms-staging/purge-finalized",
        expires_at=expired,
        finalized_at=timezone.now() - timedelta(minutes=1),
    )
    retained = _pending(
        owner,
        plant,
        client_id="purge-retained",
        staging_key="brahms-staging/purge-retained",
    )

    assert purge_expired_pending_uploads() == 2
    assert not BrahmsPendingUpload.objects.filter(pk__in=[unfinished.pk, finalized.pk]).exists()
    assert BrahmsPendingUpload.objects.filter(pk=retained.pk).exists()


def test_failed_association_removes_the_copied_destination_object():
    """A database failure after CopyObject does not leave unreachable media behind."""

    pending = SimpleNamespace(
        original_filename="failed.jpg",
        collection=Mock(),
        species=None,
        copyright_info="RBG",
    )
    config = MediaStorageConfig("private-bucket", "media", "us-east-1")
    image_filter = Mock()
    image_filter.first.return_value = None
    with patch("plants.direct_uploads._media_storage_config", return_value=config), patch(
        "plants.direct_uploads._verified_staging_object"
    ), patch("plants.direct_uploads.Image.objects.filter", return_value=image_filter), patch(
        "plants.direct_uploads._copy_staging_object", return_value="original_images/failed.jpg"
    ), patch("plants.direct_uploads._create_or_reuse_image", side_effect=IntegrityError), patch(
        "plants.direct_uploads._delete_destination_object"
    ) as cleanup:
        with pytest.raises(IntegrityError):
            finalize_pending_upload(pending)

    cleanup.assert_called_once_with(pending, config)
