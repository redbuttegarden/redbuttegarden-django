import logging
import re
import requests
import json
import uuid

from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.mail import EmailMessage
from django.core.paginator import PageNotAnInteger, EmptyPage
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseRedirect,
    HttpResponsePermanentRedirect,
    JsonResponse,
)
from django.middleware.csrf import get_token
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_GET
from requests import HTTPError
from urllib.parse import urlencode
from django.shortcuts import render, get_object_or_404
from django_tables2.config import RequestConfig
from django_tables2.export.export import TableExport
from django_tables2.paginators import LazyPaginator
from rest_framework import generics, viewsets, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.decorators import api_view
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from wagtail.models import Collection as WagtailCollection
from wagtail.images.permissions import permission_policy as image_permission_policy

from .tables import CollectionTable, TopTreesSpeciesTable
from .filters import CollectionFilter, DedicationFilter, TopTreesSpeciesFilter
from .constants import DEDICATION_FAMILY_NAME
from .selectors import dedication_collections, public_collections, public_species
from .forms import FeedbackReportForm
from .models import (
    BrahmsPendingUpload,
    Family,
    Genus,
    Species,
    Collection,
    Location,
    PlantImage,
    SpeciesImage,
    BloomEvent,
)
from .serializers import (
    FamilySerializer,
    SpeciesSerializer,
    CollectionSerializer,
    GenusSerializer,
    LocationSerializer,
    SpeciesImageListSerializer,
    SpeciesImageEditImageDescriptionSerializer,
)
from .utils import (
    clean_querydict,
    get_dedication_feature_collection,
    get_feature_collection,
    style_message,
)
from .services import ImageAssociationIntegrityError, create_brahms_image_association
from .direct_uploads import (
    DirectUploadConfigurationError,
    DirectUploadError,
    MAX_BATCH_SIZE,
    PENDING_EXPIRY,
    StagingCopyFailed,
    StagingObjectInvalid,
    StagingObjectMissing,
    create_presigned_post,
    delete_staging_object,
    finalize_pending_upload,
    validate_direct_upload_metadata,
)

logger = logging.getLogger(__name__)


MAX_FEATURES = 5000


def _join_list_field(value):
    if not value:
        return ""
    return ", ".join(str(item) for item in value)


def _species_preview_details(species):
    detail_fields = [
        ("Cultivar", species.cultivar),
        ("Habit", species.habit),
        ("Water Needs", species.water_regime),
        ("Exposure", species.exposure),
        ("Hardiness", _join_list_field(species.hardiness)),
        ("Size", species.plant_size),
        ("Flower Color", species.flower_color),
        ("Bloom Times", _join_list_field(species.bloom_time)),
    ]
    return [
        {"label": label, "value": value}
        for label, value in detail_fields
        if value
    ]


def _species_preview_image(species):
    species_image = species.species_images.select_related("image").first()
    if species_image is None:
        return None

    image = species_image.image
    rendition = image.get_rendition("fill-320x220")
    alt_text = (
        species_image.caption
        or getattr(image, "description", "")
        or image.title
        or species.full_name
    )
    return {
        "url": rendition.url,
        "width": rendition.width,
        "height": rendition.height,
        "alt": alt_text,
    }


@require_GET
def species_preview(request: HttpRequest, species_id: int) -> JsonResponse:
    """Return preview data for a publicly visible species."""

    species = get_object_or_404(
        public_species().select_related("genus__family").prefetch_related(
            "species_images__image"
        ),
        pk=species_id,
    )
    family = species.genus.family
    family_name = family.name
    if family.vernacular_name:
        family_name = f"{family.name} ({family.vernacular_name} Family)"

    return JsonResponse(
        {
            "vernacular_name": species.vernacular_name,
            "full_name": species.full_name,
            "family": family_name,
            "details": _species_preview_details(species),
            "image": _species_preview_image(species),
        }
    )


class FamilyViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete families.
    """

    queryset = Family.objects.all()
    serializer_class = FamilySerializer


class GenusViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete genera.
    """

    queryset = Genus.objects.all()
    serializer_class = GenusSerializer


class SpeciesList(generics.ListCreateAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer

    def get_queryset(self) -> QuerySet[Species]:
        """Return species matching the supplied taxonomy and plant ID filters."""
        queryset = Species.objects.all()

        genus = self.request.query_params.get("genus", "unspecified")
        name = self.request.query_params.get("name", "unspecified")
        full_name = self.request.query_params.get("full_name", "unspecified")
        subspecies = self.request.query_params.get("subspecies", "unspecified")
        variety = self.request.query_params.get("variety", "unspecified")
        subvariety = self.request.query_params.get("subvariety", "unspecified")
        forma = self.request.query_params.get("forma", "unspecified")
        subforma = self.request.query_params.get("subforma", "unspecified")
        cultivar = self.request.query_params.get("cultivar", "unspecified")
        plant_id = self.request.query_params.get("plant_id", "unspecified")

        if genus != "unspecified":
            queryset = queryset.filter(genus__name=genus)
        if name != "unspecified":
            queryset = queryset.filter(name=name)
        if full_name != "unspecified":
            queryset = queryset.filter(full_name__icontains=full_name)
        if subspecies != "unspecified":
            queryset = queryset.filter(subspecies=subspecies)
        if variety != "unspecified":
            queryset = queryset.filter(variety=variety)
        if subvariety != "unspecified":
            queryset = queryset.filter(subvariety=subvariety)
        if forma != "unspecified":
            queryset = queryset.filter(forma=forma)
        if subforma != "unspecified":
            queryset = queryset.filter(subforma=subforma)
        if cultivar != "unspecified":
            queryset = queryset.filter(cultivar=cultivar)
        if plant_id != "unspecified":
            queryset = queryset.filter(collection__plant_id=plant_id).distinct()

        return queryset


class SpeciesDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Species.objects.all()
    serializer_class = SpeciesSerializer


class LocationViewSet(viewsets.ModelViewSet):
    """
    List, create, retrieve, update or delete locations.
    """

    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class CollectionList(generics.ListCreateAPIView):
    """
    List 100 most recently created collections, or create new collections.
    """

    queryset = Collection.objects.all().order_by("-id")[:100]
    serializer_class = CollectionSerializer


class CollectionDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a living plant collection.
    """

    queryset = Collection.objects.all()
    serializer_class = CollectionSerializer


@api_view(["POST"])
def bulk_collections(request: Request) -> Response:
    """Upsert at most 100 collection payloads without coupling item failures."""

    payload = request.data
    collections = payload.get("collections") if isinstance(payload, dict) else None
    if not isinstance(collections, list):
        return Response(
            {"detail": "The request body must contain a collections list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(collections) > 100:
        return Response(
            {"detail": "At most 100 collections may be submitted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results = []
    for item in collections:
        serializer = CollectionSerializer(data=item)
        if not serializer.is_valid():
            results.append({"status": "error", "code": "invalid_collection", "detail": serializer.errors})
            continue

        plant_id = serializer.validated_data["plant_id"]
        try:
            with transaction.atomic():
                created = not Collection.objects.filter(plant_id=plant_id).exists()
                collection = serializer.save()
        except DatabaseError:
            logger.exception("Bulk collection upsert failed for a plant record.")
            results.append(
                {"plant_id": plant_id, "status": "error", "code": "database_error", "detail": "The collection could not be saved."}
            )
        else:
            results.append(
                {"plant_id": plant_id, "status": "success", "created": created, "collection": CollectionSerializer(collection).data}
            )

    return Response({"results": results})


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        if user.groups.filter(name="API").exists():
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "csrf_token": get_token(request),
                }
            )
        return Response(status=status.HTTP_403_FORBIDDEN)


@api_view(["POST"])
def set_species_image(request: Request, pk: int) -> JsonResponse:
    """Upload an image and associate it with one species."""

    # Check if user has a valid API Token
    try:
        token = request.META["HTTP_AUTHORIZATION"].split(" ")[1]
    except KeyError:
        return JsonResponse({"status": "failure"})
    if Token.objects.filter(key=token).exists():
        if "copyright_info" in request.data:
            copyright_text = request.data["copyright_info"]
        else:
            copyright_text = ""

        species = Species.objects.get(pk=pk)
        uploaded_image = request.FILES.get("image")
        try:
            result = create_brahms_image_association(
                uploaded_image, species, copyright_text
            )
        except WagtailCollection.DoesNotExist:
            logger.error(
                '"BRAHMS DATA" Collection is missing. Unable to save new images.'
            )
            return JsonResponse({"status": "failure"})
        except ImageAssociationIntegrityError as error:
            logger.debug(
                "Failed to add image relationship for species %s (%s).", species, pk
            )
            return JsonResponse(
                {
                    "status": "failure",
                    "image_created": error.image_created,
                    "species_image_created": False,
                }
            )

        return JsonResponse(
            {
                "status": "success",
                "image_created": result.image_created,
                "species_image_created": result.association_created,
            }
        )

    return JsonResponse({"status": "failure"})


@api_view(["POST"])
def set_plant_image(request: Request, plant_id: str) -> JsonResponse:
    """Upload an image and associate it with the exact living-collection ID."""

    try:
        token = request.META["HTTP_AUTHORIZATION"].split(" ")[1]
    except (KeyError, IndexError):
        return JsonResponse({"status": "failure"})
    if not Token.objects.filter(key=token).exists():
        return JsonResponse({"status": "failure"})

    try:
        collection = Collection.objects.select_related("species").get(plant_id=plant_id)
    except Collection.DoesNotExist:
        return JsonResponse({"status": "failure"}, status=404)

    uploaded_image = request.FILES.get("image")
    if uploaded_image is None:
        return JsonResponse({"status": "failure"}, status=400)

    copyright_text = request.data.get("copyright_info", "")
    try:
        result = create_brahms_image_association(
            uploaded_image, collection, copyright_text
        )
    except WagtailCollection.DoesNotExist:
        logger.error('"BRAHMS DATA" Collection is missing. Unable to save new images.')
        return JsonResponse({"status": "failure"})
    except ImageAssociationIntegrityError as error:
        logger.debug("Failed to add plant image relationship.")
        return JsonResponse(
            {
                "status": "failure",
                "image_created": error.image_created,
                "plant_image_created": False,
            }
        )

    return JsonResponse(
        {
            "status": "success",
            "image_created": result.image_created,
            "plant_image_created": result.association_created,
        }
    )


TAXONOMY_LOOKUP_FIELDS = (
    "genus",
    "name",
    "subspecies",
    "variety",
    "subvariety",
    "forma",
    "subforma",
    "cultivar",
)


def _image_result(client_id: object, code: str, detail: str) -> dict[str, object]:
    """Build one stable error result for the bulk image API."""

    return {
        "client_id": client_id if isinstance(client_id, str) else "",
        "status": "error",
        "code": code,
        "detail": detail,
    }


def _resolve_manifest_species(target: dict[str, object]) -> Species:
    """Return the one species selected by a complete exact taxonomy target."""

    if set(target) != set(TAXONOMY_LOOKUP_FIELDS):
        raise ValueError("Species targets must contain every exact taxonomy field.")
    if not isinstance(target["genus"], str):
        raise ValueError("The species genus must be a string.")
    if any(
        not isinstance(target[field], (str, type(None)))
        for field in TAXONOMY_LOOKUP_FIELDS
        if field != "genus"
    ):
        raise ValueError("Species taxonomy fields must be strings or null.")

    lookup = {field: target[field] for field in TAXONOMY_LOOKUP_FIELDS if field != "genus"}
    matches = Species.objects.filter(genus__name=target["genus"], **lookup)
    count = matches.count()
    if count == 0:
        raise Species.DoesNotExist
    if count > 1:
        raise Species.MultipleObjectsReturned
    return matches.get()


@api_view(["POST"])
def bulk_images(request: Request) -> Response:
    """Associate up to 20 uploaded images while isolating every manifest item."""

    manifest_value = request.data.get("manifest")
    try:
        manifest = json.loads(manifest_value)
    except (TypeError, json.JSONDecodeError):
        return Response(
            {"detail": "manifest must be a JSON list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if not isinstance(manifest, list):
        return Response(
            {"detail": "manifest must be a JSON list."},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if len(manifest) > 20:
        return Response(
            {"detail": "At most 20 images may be submitted."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results: list[dict[str, object]] = []
    for item in manifest:
        client_id = item.get("client_id") if isinstance(item, dict) else ""
        if not isinstance(item, dict) or not isinstance(client_id, str):
            results.append(_image_result(client_id, "invalid_item", "Each item needs a string client_id."))
            continue
        file_field = item.get("file_field")
        copyright_text = item.get("copyright_info")
        if not isinstance(file_field, str) or not file_field:
            results.append(_image_result(client_id, "missing_file", "The referenced file field is required."))
            continue
        if not isinstance(copyright_text, str):
            results.append(_image_result(client_id, "invalid_item", "copyright_info must be a string."))
            continue

        has_plant = "plant_id" in item
        has_species = "species" in item
        if has_plant == has_species:
            results.append(_image_result(client_id, "invalid_target", "Specify exactly one image target."))
            continue
        uploaded_image = request.FILES.get(file_field)
        if uploaded_image is None:
            results.append(_image_result(client_id, "missing_file", "The referenced upload was not provided."))
            continue

        try:
            with transaction.atomic():
                if has_plant:
                    plant_id = item["plant_id"]
                    if not isinstance(plant_id, str) or not plant_id:
                        raise ValueError("plant_id must be a non-empty string.")
                    try:
                        target = Collection.objects.select_related("species").get(plant_id=plant_id)
                    except Collection.DoesNotExist:
                        results.append(_image_result(client_id, "plant_not_found", "No collection matches this plant_id."))
                        continue
                else:
                    species_target = item["species"]
                    if not isinstance(species_target, dict):
                        raise ValueError("species must be an object.")
                    try:
                        target = _resolve_manifest_species(species_target)
                    except Species.DoesNotExist:
                        results.append(_image_result(client_id, "species_not_found", "No species matches this taxonomy."))
                        continue
                    except Species.MultipleObjectsReturned:
                        results.append(_image_result(client_id, "species_ambiguous", "More than one species matches this taxonomy."))
                        continue

                association = create_brahms_image_association(
                    uploaded_image, target, copyright_text
                )
        except ValueError as error:
            results.append(_image_result(client_id, "invalid_target", str(error)))
        except WagtailCollection.DoesNotExist:
            logger.exception("BRAHMS Data collection missing during bulk image upload.")
            results.append(_image_result(client_id, "storage_error", "The image could not be stored."))
        except IntegrityError:
            logger.exception("Database integrity error during bulk image upload.")
            results.append(_image_result(client_id, "database_error", "The image association could not be saved."))
        except DatabaseError:
            logger.exception("Database error during bulk image upload.")
            results.append(_image_result(client_id, "database_error", "The image association could not be saved."))
        except Exception:
            logger.exception("Storage error during bulk image upload.")
            results.append(_image_result(client_id, "storage_error", "The image could not be stored."))
        else:
            results.append(
                {"client_id": client_id, "status": "success", "created": association.association_created}
            )

    return Response({"results": results})


def _direct_upload_result(client_id: object, code: str, detail: str) -> dict[str, object]:
    """Build a stable per-item result for the direct-upload endpoints."""

    return _image_result(client_id, code, detail)


def _resolve_direct_upload_target(item: dict[str, object]) -> Collection | Species:
    """Resolve one exact plant or species target before creating a pending upload."""

    has_plant = "plant_id" in item
    has_species = "species" in item
    if has_plant == has_species:
        raise ValueError("Specify exactly one image target.")
    if has_plant:
        plant_id = item["plant_id"]
        if not isinstance(plant_id, str) or not plant_id:
            raise ValueError("plant_id must be a non-empty string.")
        return Collection.objects.select_related("species").get(plant_id=plant_id)

    species_target = item["species"]
    if not isinstance(species_target, dict):
        raise ValueError("species must be an object.")
    return _resolve_manifest_species(species_target)


def _direct_upload_outer_items(request: Request, field_name: str) -> list[object] | None:
    """Return a bounded JSON array or signal a malformed direct-upload envelope."""

    payload = request.data
    items = payload.get(field_name) if isinstance(payload, dict) else None
    if not isinstance(items, list) or len(items) > MAX_BATCH_SIZE:
        return None
    return items


@api_view(["POST"])
def initiate_direct_upload(request: Request) -> Response:
    """Create pending uploads and exact, short-lived private S3 POST policies."""

    items = _direct_upload_outer_items(request, "uploads")
    if items is None:
        return Response(
            {"detail": "uploads must be a JSON list containing at most 20 items."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results: list[dict[str, object]] = []
    for item in items:
        client_id = item.get("client_id") if isinstance(item, dict) else ""
        if not isinstance(item, dict) or not isinstance(client_id, str) or not client_id:
            results.append(_direct_upload_result(client_id, "invalid_item", "Each item needs a string client_id."))
            continue
        copyright_info = item.get("copyright_info", "")
        if not isinstance(copyright_info, str):
            results.append(_direct_upload_result(client_id, "invalid_item", "copyright_info must be a string."))
            continue
        try:
            (
                filename,
                content_type,
                byte_size,
                image_width,
                image_height,
                sha256,
            ) = validate_direct_upload_metadata(item)
            target = _resolve_direct_upload_target(item)
        except Collection.DoesNotExist:
            results.append(_direct_upload_result(client_id, "plant_not_found", "No collection matches this plant_id."))
            continue
        except Species.DoesNotExist:
            results.append(_direct_upload_result(client_id, "species_not_found", "No species matches this taxonomy."))
            continue
        except Species.MultipleObjectsReturned:
            results.append(_direct_upload_result(client_id, "species_ambiguous", "More than one species matches this taxonomy."))
            continue
        except ValueError as error:
            results.append(_direct_upload_result(client_id, "invalid_upload", str(error)))
            continue

        with transaction.atomic():
            pending, created = BrahmsPendingUpload.objects.get_or_create(
                owner=request.user,
                client_id=client_id,
                defaults={
                    "collection": target if isinstance(target, Collection) else None,
                    "species": target if isinstance(target, Species) else None,
                    "original_filename": filename,
                    "copyright_info": copyright_info,
                    "content_type": content_type,
                    "byte_size": byte_size,
                    "image_width": image_width,
                    "image_height": image_height,
                    "sha256": sha256,
                    "staging_key": f"brahms-staging/{uuid.uuid4()}",
                    "expires_at": timezone.now() + PENDING_EXPIRY,
                },
            )
        if not created:
            if pending.finalized_at is not None:
                results.append(_direct_upload_result(client_id, "already_finalized", "This client_id was already finalized."))
                continue
            if (
                pending.original_filename != filename
                or pending.content_type != content_type
                or pending.byte_size != byte_size
                or pending.image_width != image_width
                or pending.image_height != image_height
                or pending.sha256 != sha256
                or pending.copyright_info != copyright_info
                or (
                    isinstance(target, Collection)
                    and pending.collection_id != target.pk
                )
                or (
                    isinstance(target, Species)
                    and pending.species_id != target.pk
                )
            ):
                results.append(_direct_upload_result(client_id, "client_id_conflict", "This client_id already identifies a different upload."))
                continue
        try:
            post = create_presigned_post(pending)
        except DirectUploadConfigurationError as error:
            logger.exception("Direct upload storage is not configured.")
            results.append(_direct_upload_result(client_id, "storage_unavailable", str(error)))
            continue
        except Exception:
            logger.exception("Could not create direct upload POST policy.")
            results.append(_direct_upload_result(client_id, "storage_error", "Could not authorize the direct upload."))
            continue
        results.append(
            {
                "client_id": client_id,
                "status": "success",
                "pending_id": str(pending.pk),
                "staging_key": pending.staging_key,
                "expires_at": pending.expires_at.isoformat(),
                "upload": post,
            }
        )
    return Response({"results": results})


def _get_owned_pending_upload(item: dict[str, object], user: object) -> BrahmsPendingUpload:
    """Look up one caller-owned pending upload by opaque ID or client ID only."""

    has_pending_id = "pending_id" in item
    has_client_id = "client_id" in item
    if has_pending_id == has_client_id:
        raise ValueError("Specify exactly one pending_id or client_id.")
    if has_pending_id:
        pending_id = item["pending_id"]
        if not isinstance(pending_id, str):
            raise ValueError("pending_id must be a string.")
        return BrahmsPendingUpload.objects.select_for_update().get(pk=pending_id, owner=user)
    client_id = item["client_id"]
    if not isinstance(client_id, str) or not client_id:
        raise ValueError("client_id must be a non-empty string.")
    return BrahmsPendingUpload.objects.select_for_update().get(owner=user, client_id=client_id)


@api_view(["POST"])
def finalize_direct_upload(request: Request) -> Response:
    """Verify caller-owned staged objects and create their Wagtail associations."""

    items = _direct_upload_outer_items(request, "uploads")
    if items is None:
        return Response(
            {"detail": "uploads must be a JSON list containing at most 20 items."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    results: list[dict[str, object]] = []
    successful: list[BrahmsPendingUpload] = []
    for item in items:
        client_id = item.get("client_id") if isinstance(item, dict) else ""
        if not isinstance(item, dict):
            results.append(_direct_upload_result(client_id, "invalid_item", "Each item must be an object."))
            continue
        try:
            with transaction.atomic():
                pending = _get_owned_pending_upload(item, request.user)
                response_client_id = pending.client_id
                if pending.finalized_at is not None:
                    results.append(
                        {
                            "client_id": response_client_id,
                            "status": "success",
                            "created": pending.association_created,
                            "finalized": True,
                        }
                    )
                    continue
                if pending.expires_at <= timezone.now():
                    results.append(_direct_upload_result(response_client_id, "upload_expired", "The pending upload has expired."))
                    continue
                image, association_created = finalize_pending_upload(pending)
                pending.image = image
                pending.association_created = association_created
                pending.finalized_at = timezone.now()
                pending.save(update_fields=["image", "association_created", "finalized_at"])
                successful.append(pending)
                results.append(
                    {
                        "client_id": response_client_id,
                        "status": "success",
                        "created": association_created,
                        "finalized": False,
                    }
                )
        except BrahmsPendingUpload.DoesNotExist:
            results.append(_direct_upload_result(client_id, "pending_not_found", "No pending upload is available."))
        except ValueError as error:
            results.append(_direct_upload_result(client_id, "invalid_item", str(error)))
        except StagingObjectMissing as error:
            results.append(_direct_upload_result(client_id, "staging_not_found", str(error)))
        except StagingObjectInvalid as error:
            results.append(_direct_upload_result(client_id, "staging_invalid", str(error)))
        except (StagingCopyFailed, DirectUploadConfigurationError):
            logger.exception("Could not finalize a BRAHMS direct upload.")
            results.append(_direct_upload_result(client_id, "storage_error", "The staged upload could not be finalized."))
        except IntegrityError:
            logger.exception("Database integrity error finalizing a BRAHMS direct upload.")
            results.append(_direct_upload_result(client_id, "database_error", "The image association could not be saved."))
        except DatabaseError:
            logger.exception("Database error finalizing a BRAHMS direct upload.")
            results.append(_direct_upload_result(client_id, "database_error", "The image association could not be saved."))
        except Exception:
            logger.exception("Unexpected error finalizing a BRAHMS direct upload.")
            results.append(_direct_upload_result(client_id, "storage_error", "The staged upload could not be finalized."))

    for pending in successful:
        delete_staging_object(pending)
    return Response({"results": results})


class SpeciesImageListView(generics.ListAPIView):
    queryset = SpeciesImage.objects.select_related("species", "image").order_by(
        "species_id", "sort_order", "id"
    )
    serializer_class = SpeciesImageListSerializer


class SpeciesImageEditImageDescriptionView(generics.RetrieveUpdateAPIView):
    queryset = SpeciesImage.objects.select_related("species", "image")
    serializer_class = SpeciesImageEditImageDescriptionSerializer

    def patch(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return self.update(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()  # SpeciesImage
        image = instance.image  # wagtailimages.Image

        # Collection-aware permission check (respects Wagtail collection permissions)
        if not image_permission_policy.user_has_permission_for_instance(
            request.user, "change", image
        ):
            raise PermissionDenied(
                "You do not have permission to edit this Wagtail image."
            )

        serializer = self.get_serializer(
            instance,
            data=request.data,
            partial=kwargs.get("partial", False),
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return super().update(request, *args, **kwargs)


def csrf_view(request):
    return render(request, "plants/token.html")


def _parse_bbox(bbox: str):
    parts = bbox.split(",")
    if len(parts) != 4:
        raise ValueError("bbox must have 4 comma-separated values")
    west, south, east, north = (Decimal(p.strip()) for p in parts)
    return west, south, east, north


@require_GET
def collections_geojson(request: HttpRequest) -> JsonResponse:
    """Return GeoJSON features for public plant collections within an optional bbox."""

    qs = public_collections().exclude(location=None).select_related(
        "location", "species", "species__genus", "species__genus__family", "garden"
    )

    bbox = request.GET.get("bbox")
    if bbox:
        try:
            west, south, east, north = _parse_bbox(bbox)
        except (ValueError, InvalidOperation):
            return JsonResponse({"message": "Invalid bbox."}, status=400)

        # Handle antimeridian wrap (rare for you, but correct)
        if west <= east:
            qs = qs.filter(
                location__longitude__gte=west,
                location__longitude__lte=east,
                location__latitude__gte=south,
                location__latitude__lte=north,
            )
        else:
            # bbox crosses the dateline; split into two longitude ranges
            qs = qs.filter(
                location__latitude__gte=south,
                location__latitude__lte=north,
            ).filter(
                (Q(location__longitude__gte=west) |
                 Q(location__longitude__lte=east))
            )

    qs = CollectionFilter(request.GET or None, queryset=qs).qs

    qs = qs.order_by("-id")[:MAX_FEATURES]
    return JsonResponse(get_feature_collection(qs), safe=False)


def plant_map_view(request: HttpRequest) -> HttpResponse:
    """Render the filtered plant map with safe query-string canonicalization."""

    mapbox_api_token = getattr(settings, "MAPBOX_API_TOKEN", None)

    # Use the same filterset contract as list view
    base_qs = public_collections().exclude(location=None).select_related(
        "location", "species", "garden"
    )
    f = CollectionFilter(request.GET or None, queryset=base_qs)
    filtered_qs = f.qs

    # Optional: canonicalize URL on full page loads (same as list view)
    is_htmx = (
        request.headers.get("HX-Request") == "true"
        or request.META.get("HTTP_HX_REQUEST") == "true"
        or request.GET.get("_hx") == "1"
    )
    if request.method == "GET" and not is_htmx and request.GET:
        cleaned = clean_querydict(request.GET)
        if cleaned.urlencode() != request.GET.urlencode():
            url = request.path
            qs = cleaned.urlencode()
            redirect_url = f"{url}?{qs}" if qs else url
            if url_has_allowed_host_and_scheme(
                redirect_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return HttpResponseRedirect(redirect_url)

    return render(
        request,
        "plants/collection_map.html",
        {
            "mapbox_token": mapbox_api_token,
            "filter": f,  # map template renders filter.form
            "objects": filtered_qs,  # or build GeoJSON / bounds / counts etc.
        },
    )


def collection_detail(request: HttpRequest, collection_id: int) -> HttpResponse:
    """Render a plant collection or redirect a dedication to its canonical URL."""

    collection = get_object_or_404(
        Collection.objects.select_related("species__genus__family").prefetch_related(
            "plant_images__image"
        ),
        pk=collection_id,
    )
    if collection.species.genus.family.name == DEDICATION_FAMILY_NAME:
        return HttpResponsePermanentRedirect(collection.get_absolute_url())
    mapbox_api_token = getattr(settings, "MAPBOX_API_TOKEN", None)

    # Check if there are any BloomEvents associated with the collection
    today_local = timezone.localdate()
    in_bloom = collection.bloomevent_set.filter(
        bloom_start__lte=today_local, bloom_end__gte=today_local
    ).exists()
    return render(
        request,
        "plants/collection_detail.html",
        {
            "collection": collection,
            "images": collection.plant_images.select_related("image"),
            "in_bloom": in_bloom,
            "mapbox_token": mapbox_api_token,
        },
    )


def dedication_detail(request: HttpRequest, collection_id: int) -> HttpResponse:
    """Render the public dedicated detail page for one dedication."""

    collection = get_object_or_404(
        dedication_collections().select_related("location", "garden", "species"),
        pk=collection_id,
    )
    plant_images = collection.plant_images.select_related("image")
    return render(
        request,
        "plants/dedication_detail.html",
        {
            "collection": collection,
            "images": plant_images,
            "mapbox_token": getattr(settings, "MAPBOX_API_TOKEN", None),
        },
    )


@require_GET
def dedications_geojson(request: HttpRequest) -> JsonResponse:
    """Return mapped dedication records without exposing general plant records."""

    queryset = dedication_collections().exclude(location=None).select_related(
        "location", "species__genus__family", "garden"
    )
    filtered = DedicationFilter(request.GET or None, queryset=queryset).qs
    return JsonResponse(
        get_dedication_feature_collection(filtered.order_by("-id")[:MAX_FEATURES]),
        safe=False,
    )


def dedication_map_view(request: HttpRequest) -> HttpResponse:
    """Render the dedicated map and its narrowly scoped discovery filters."""

    queryset = dedication_collections().exclude(location=None).select_related(
        "location", "species__genus__family", "garden"
    )
    dedication_filter = DedicationFilter(request.GET or None, queryset=queryset)
    return render(
        request,
        "plants/dedication_map.html",
        {
            "filter": dedication_filter,
            "dedications": dedication_filter.qs,
            "mapbox_token": getattr(settings, "MAPBOX_API_TOKEN", None),
        },
    )


def species_detail(request, species_id):
    """
    View for displaying detailed info about a single Species object.
    """
    species = get_object_or_404(
        public_species().select_related("genus__family"), pk=species_id
    )
    species_images = SpeciesImage.objects.filter(species=species)
    species_collections = public_collections().filter(species=species).select_related(
        "garden"
    )
    collections_table = None
    has_geolocation = False

    if species_collections.exists():
        collections_table = CollectionTable(
            species_collections, exclude=("species",)
        )
        RequestConfig(
            request,
            paginate={
                "per_page": 50,
                "paginator_class": LazyPaginator,
                "silent": True,
            },
        ).configure(collections_table)

        # Check if at least one collection has a linked location with non-null latitude and longitude
        has_geolocation = species_collections.filter(
            location__isnull=False,
            location__latitude__isnull=False,
            location__longitude__isnull=False
        ).exists()

    # Check if there are any BloomEvents associated with the species
    today_local = timezone.localdate()
    in_bloom = BloomEvent.objects.filter(
        species=species, bloom_start__lte=today_local, bloom_end__gte=today_local
    ).exists()
    return render(
        request,
        "plants/species_detail.html",
        {
            "species": species,
            "in_bloom": in_bloom,
            "images": species_images,
            "collections_table": collections_table,
            "has_geolocation": has_geolocation,
        },
    )


def species_or_collection_feedback(request, species_id=None, collection_id=None):
    """
    Form view for reporting a problem with a Species or Collection object.
    """
    species = None
    collection = None
    if species_id:
        species = get_object_or_404(Species, pk=species_id)
    elif collection_id:
        collection = get_object_or_404(Collection, pk=collection_id)
    else:
        raise ValueError("Missing ID to Species or Collection")

    if request.method == "POST":
        form = FeedbackReportForm(species_id, collection_id, request.POST)
        if form.is_valid():
            subject = form.cleaned_data["subject"]
            original_message = form.cleaned_data["message"]
            sender = form.cleaned_data["sender"]
            cc_myself = form.cleaned_data["cc_myself"]

            hcaptcha_token = request.POST.get("h-captcha-response", None)

            # We use this to distinguish between requests error or hCaptcha error when hcaptcha_passed is False
            json_response = None

            try:
                # Make sure captcha is valid before we do anything else
                hcaptcha_response = requests.post(
                    "https://api.hcaptcha.com/siteverify",
                    data={
                        "response": hcaptcha_token,
                        "secret": settings.HCAPTCHA_SECRET_KEY,
                        "sitekey": settings.HCAPTCHA_SITE_KEY,
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                hcaptcha_response.raise_for_status()
                json_response = hcaptcha_response.json()
                logger.debug(f"hCaptcha Reponse: {json_response}")
                hcaptcha_passed = json_response["success"]
            except HTTPError as e:
                logger.error(f"Error while checking hCaptcha response: {e}")
                messages.error(
                    request,
                    "Error encountered while processing Captcha check. Please try again later.",
                )
                hcaptcha_passed = False

            except Exception as e:
                logger.error(
                    f"General exception occurred while processing hCaptcha response: {e}"
                )
                messages.error(
                    request,
                    "Error encountered while processing Captcha check. Please try again later.",
                )
                hcaptcha_passed = False

            if hcaptcha_passed:
                recipients = [
                    user.email
                    for user in get_user_model().objects.filter(
                        groups__name="Plant Collection Curators"
                    )
                ]

                subject = "RBG Website Plants Feedback: " + subject
                message = style_message(
                    request, species, collection, original_message)
                email = EmailMessage(
                    subject=subject,
                    body=message,
                    from_email=getattr(
                        settings, "DEFAULT_FROM_EMAIL", "admin@redbuttegarden.org"
                    ),
                    to=recipients,
                    cc=(sender,) if cc_myself else None,
                    reply_to=(sender,),
                )
                email.send()
                return HttpResponseRedirect(reverse("plants:feedback-thanks"))
            else:
                # if json_response exists, must be an hCaptcha error
                if json_response:
                    logger.debug(
                        f"Encountered hCaptcha error(s): {json_response['error-codes']}"
                    )
                    # Add non-field error to form
                    form.add_error(
                        None,
                        "We encountered an error while processing your Captcha challenge. Please try again.",
                    )

    else:
        form = FeedbackReportForm(species_id, collection_id)

    context = {
        "form": form,
        "species_id": species_id,
        "collection_id": collection_id,
        "hcaptcha_site_key": settings.HCAPTCHA_SITE_KEY,
    }
    return render(request, "plants/plant_feedback.html", context)


def _coerce_positive_int(value, default=1):
    try:
        value = int(value)
    except (TypeError, ValueError):
        return default
    return value if value > 0 else default


def _is_safe_local_url(url: str, *, require_https: bool) -> bool:
    """Return whether a URL is a root-relative path without an external host."""

    return (
        url.startswith("/")
        and not url.startswith("//")
        and url_has_allowed_host_and_scheme(
            url,
            allowed_hosts=set(),
            require_https=require_https,
        )
    )


def collection_results(request: HttpRequest) -> HttpResponse:
    """Render filtered collection results using only safe local request URLs."""

    request_path = request.path
    require_https = request.is_secure()
    if not _is_safe_local_url(request_path, require_https=require_https):
        return HttpResponseBadRequest("Invalid request path.")

    # HTMX detection
    is_htmx = (
        request.headers.get("HX-Request") == "true"
        or request.META.get("HTTP_HX_REQUEST") == "true"
        or request.GET.get("_hx") == "1"
    )

    # Canonicalize querystring
    if request.method == "GET" and not is_htmx and request.GET:
        cleaned = clean_querydict(request.GET)
        if cleaned.urlencode() != request.GET.urlencode():
            url = request_path
            qs = cleaned.urlencode()
            if qs:
                url = f"{url}?{qs}"
            if not _is_safe_local_url(url, require_https=require_https):
                return HttpResponseBadRequest("Invalid redirect URL.")
            return HttpResponseRedirect(url)

    mode = request.GET.get("mode", "list")
    if mode not in ("list", "map"):
        mode = "list"

    base_qs = public_collections()
    collection_filter = CollectionFilter(request.GET or None, queryset=base_qs)
    filtered_qs = collection_filter.qs

    if collection_filter.form.is_bound and not collection_filter.form.is_valid():
        messages.error(request, "Invalid search criteria. Please adjust your filters and try again.")

    context = {
        "page_title": "Living Collections",
        "heading": "Living Collections",
        "filter": collection_filter,
        "mode": mode,
        "show_mode_toggle": True,
        "htmx_enabled": (mode == "list"),
        "clear_url": f"{request_path}?mode={mode}",
        "table_template": "plants/collection_list_table.html",
    }

    if mode == "map":
        filtered_qs = filtered_qs.select_related("species", "garden")
        context["objects"] = filtered_qs
        return render(request, "plants/collection_map.html", context)

    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        export_table = CollectionTable(filtered_qs)
        exporter = TableExport(export_format, export_table)
        return exporter.response(f"collections.{export_format}")

    table = CollectionTable(filtered_qs)

    per_page = 50
    requested_page = _coerce_positive_int(request.GET.get("page"), default=1)

    RequestConfig(
        request,
        paginate={
            "per_page": per_page,
            "paginator_class": LazyPaginator,
            "silent": True,
        },
    ).configure(table)

    # Use the actual resolved page number if pagination succeeded
    page_number = requested_page
    if getattr(table, "page", None) is not None:
        try:
            page_number = table.page.number
        except Exception:
            page_number = requested_page

    try:
        current_page_count = (
            len(table.rows) if getattr(table, "rows", None) is not None else 0
        )
    except Exception:
        current_page_count = 0

    paginator = getattr(getattr(table, "page", None), "paginator", None)

    # LazyPaginator does not support count()
    if isinstance(paginator, LazyPaginator):
        table_total = None
        total_known = False
    else:
        try:
            table_total = filtered_qs.count()
            total_known = True
        except Exception:
            table_total = None
            total_known = False

    if current_page_count == 0:
        table_start = 0
        table_end = 0
        if total_known and table_total is None:
            table_total = 0

        if collection_filter.form.is_bound and collection_filter.form.is_valid():
            messages.info(request, "No collections found matching your search criteria.")
    else:
        table_start = (page_number - 1) * per_page + 1
        if total_known and isinstance(table_total, int):
            table_end = min(table_start + current_page_count - 1, table_total)
        else:
            table_end = table_start + current_page_count - 1

    querystring = ""
    if collection_filter.form.is_bound and collection_filter.form.is_valid():
        params = {}
        for name, value in collection_filter.form.cleaned_data.items():
            if name == "_export":
                continue
            if value in ("", None, [], (), {}):
                continue
            if value is False:
                continue
            params[name] = "true" if value is True else value

        querystring = urlencode(params, doseq=True)

    context.update(
        {
            "table": table,
            "querystring": querystring,
            "table_start": table_start,
            "table_end": table_end,
            "table_total": table_total,
            "total_known": total_known,
            "per_page": per_page,
        }
    )

    if is_htmx:
        return render(request, "plants/includes/_results_container.html", context)

    return render(request, "plants/collection_results.html", context)


def collection_search_page(request):
    """
    Landing page only: displays the filter form and sends users to results.
    No POST; no filtering here beyond binding the form for UX.
    """
    base_qs = Collection.objects.none()  # we don't need results here
    collection_filter = CollectionFilter(
        request.GET or None, queryset=base_qs, exclude_hidden_gardens=True)

    return render(
        request,
        "plants/collection_search.html",
        {
            "filter": collection_filter,
        },
    )


def get_garden_code_view(request: HttpRequest) -> HttpResponse:
    """Render public plant garden-code options for an optionally selected garden."""

    selected_name = request.GET.get("garden_name", "").strip()

    qs = public_collections().exclude(garden__code__isnull=True).exclude(
        garden__code=""
    )

    if selected_name:
        qs = qs.filter(garden__name__iexact=selected_name)

    codes = qs.values_list("garden__code", flat=True).distinct().order_by("garden__code")

    return render(
        request,
        "plants/partials/garden_code_select.html",
        {"codes": codes}
    )


def feedback_thanks(request):
    return render(request, "plants/feedback_thanks.html")


def get_filtered_collections(request, species_id):
    """
    Returns a JSON response with filtered collections based on the species_id.

    Used for AJAX requests to dynamically populate options in a form field of BloomEvent admin Snippet.
    """
    # Filter collections to those that match the given species_id
    options = Collection.objects.filter(
        species=species_id).values("id", "plant_id")
    return JsonResponse(
        {"options": [{"value": o["id"], "label": o["plant_id"]}
                     for o in options]}
    )


def top_trees(request: HttpRequest) -> HttpResponse:
    """
    List of Species that have been marked as Arborist Recommended in BRAHMS,
    with filtering, export, and HTMX partial responses. Uses LazyPaginator
    so total may be unknown; compute display values safely.
    """
    qs = public_species().filter(arborist_rec=True)
    f = TopTreesSpeciesFilter(request.GET, queryset=qs)

    # Export handling
    export_format = request.GET.get("_export", None)
    if TableExport.is_valid_format(export_format):
        export_table = TopTreesSpeciesTable(f.qs)
        exporter = TableExport(export_format, export_table)
        return exporter.response(f"top_trees.{export_format}")

    # --- configure table with an explicit per_page so we can compute ranges ---
    per_page = 50  # choose your page size
    table = TopTreesSpeciesTable(f.qs)
    RequestConfig(request, paginate={
                  "paginator_class": LazyPaginator}).configure(table)

    raw_page = request.GET.get("page", "1")
    if not re.fullmatch(r"\d+", str(raw_page)):
        logger.warning(
            "Invalid page param: %r from %s", raw_page, request.META.get(
                "REMOTE_ADDR")
        )
        page_for_pagination = 1
    else:
        page_for_pagination = int(raw_page)
        if page_for_pagination < 1:
            page_for_pagination = 1

    try:
        table.paginate(page=page_for_pagination, per_page=per_page)
    except (PageNotAnInteger, EmptyPage) as exc:
        logger.warning("Paginator fallback for page=%r: %s", raw_page, exc)
        # fallback to page 1
        table.paginate(page=1, per_page=per_page)
    except Exception as exc:
        logger.exception("Unexpected paginator error for page=%r", raw_page)
        table.paginate(page=1, per_page=per_page)

    # --- determine current page number (can reuse page_for_pagination) ---
    page_number = page_for_pagination

    # --- Try to determine total count (may be expensive) ---
    total_known = True
    table_total = None
    try:
        table_total = f.qs.count()
    except Exception:
        # Can't or don't want to count; mark as unknown
        total_known = False
        table_total = None

    # If the paginator exposes a reliable count attribute, prefer that
    if getattr(table, "page", None) is not None:
        try:
            maybe_count = getattr(table.page.paginator, "count", None)
            if isinstance(maybe_count, int):
                table_total = maybe_count
                total_known = True
        except Exception:
            pass

    # If no rows at all:
    current_page_count = 0
    if getattr(table, "rows", None) is not None:
        try:
            current_page_count = len(table.rows)
        except Exception:
            # defensive fallback
            current_page_count = 0

    if current_page_count == 0:
        table_start = 0
        table_end = 0
    else:
        table_start = (page_number - 1) * per_page + 1

        if total_known and isinstance(table_total, int):
            # when we know the total, compute end using arithmetic (don't trust table.rows)
            table_end = min(page_number * per_page, table_total)
        else:
            # total unknown: compute end from number of rows on this page
            table_end = table_start + current_page_count - 1

    # build querystring without _export so export links preserve filters
    querydict = request.GET.copy()
    querydict.pop("_export", None)
    querystring = querydict.urlencode()

    additional_html = """<p>This list highlights trees growing successfully at Red Butte Garden and Arboretum. These are species and cultivars that have proven their resilience and performance in our climate. Compiled by our Arborist and Horticulture Director, it is intended to serve as a practical guide for anyone choosing trees that will thrive in Utah. The trees are organized alphabetically by scientific name for easy reference.</p>
<p>Whether you’re planning a new landscape or replacing an existing tree, we hope this resource makes the selection process easier and helps you feel confident in planting the right tree for your site.</p>
<p>Click the botanical name to learn more about each tree.</p>
<p>To download this list as an Excel file, use this link to our <a href="https://redbuttegarden.org/media/documents/Top_Tree_Selections_for_Utah_2025.xlsx" title="Top Tree Selections for Utah 2025">Top Tree Selections for Utah 2025</a>.</p>
"""

    context = {
        "page_title": "Top Trees",
        "heading": "Top Tree Selections for Utah",
        "additional_html": additional_html,
        "table": table,
        "filter": f,
        "querystring": querystring,
        "table_start": table_start,
        "table_end": table_end,
        "table_total": table_total,
        "total_known": total_known,
        "per_page": per_page,
        # template switches
        "show_mode_toggle": False,
        "htmx_enabled": True,
        "clear_url": request.path,  # clears filters
        "table_template": "plants/collection_list_table.html",
    }

    # Robust HTMX detection: header OR WSGI META OR explicit GET param fallback (_hx=1)
    is_htmx = (
        request.headers.get("HX-Request") == "true"
        or request.META.get("HTTP_HX_REQUEST") == "true"
        or request.GET.get("_hx") == "1"
    )

    if is_htmx:
        return render(request, "plants/includes/_results_container.html", context)

    return render(request, "plants/collection_results.html", context)
