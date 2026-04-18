from __future__ import annotations

from datetime import datetime
import re

from django.conf import settings
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.utils.html import strip_tags
from django.views.decorators.http import require_GET

from events.models import EventGeneralPage, EventPage
from plants.models import (
    BloomEvent,
    Collection,
    Family,
    GardenArea,
    Genus,
    Location,
    Species,
    SpeciesImage,
)


EVENT_QUERY_STOP_WORDS = {
    "a",
    "about",
    "after",
    "am",
    "an",
    "and",
    "any",
    "are",
    "at",
    "be",
    "butte",
    "can",
    "coming",
    "concert",
    "do",
    "event",
    "events",
    "garden",
    "help",
    "i",
    "in",
    "is",
    "me",
    "need",
    "next",
    "non",
    "of",
    "on",
    "other",
    "our",
    "please",
    "red",
    "show",
    "soon",
    "tell",
    "that",
    "the",
    "there",
    "this",
    "up",
    "upcoming",
    "us",
    "what",
    "when",
    "which",
}


def _json_error(detail: str, status: int) -> JsonResponse:
    return JsonResponse({"detail": detail}, status=status)


def _get_limit(request, default: int = 5, maximum: int = 25) -> int:
    raw_limit = request.GET.get("limit")
    if not raw_limit:
        return default

    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return default

    return max(1, min(limit, maximum))


def _get_bool_param(request, name: str, default: bool = False) -> bool:
    value = request.GET.get(name)
    if value is None:
        return default

    return value.strip().lower() in {"1", "true", "yes", "on"}


def _serialize_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _page_url(page, request) -> str:
    page_url = page.get_url() or ""
    return request.build_absolute_uri(page_url)


def _serialize_event_page(page: EventPage, request) -> dict:
    return {
        "object_type": "event",
        "page_type": "event_page",
        "title": page.title,
        "url": _page_url(page, request),
        "description": strip_tags(page.search_description or page.sub_heading or ""),
        "sub_heading": page.sub_heading,
        "event_dates": page.event_dates,
        "start_datetime": _serialize_datetime(page.start_datetime),
        "end_datetime": _serialize_datetime(page.end_datetime),
        "location": page.location,
        "instructor": page.instructor,
        "member_cost": page.member_cost,
        "public_cost": page.public_cost,
        "purchase_url": page.purchase_url,
        "categories": [category.name for category in page.event_categories.all()],
        "notes": strip_tags(page.notes or ""),
        "additional_info": strip_tags(page.additional_info or ""),
        "is_upcoming": bool(
            page.start_datetime and page.start_datetime >= timezone.now()
        ),
    }


def _serialize_event_general_page(page: EventGeneralPage, request) -> dict:
    return {
        "object_type": "event",
        "page_type": "event_general_page",
        "title": page.title,
        "url": _page_url(page, request),
        "description": strip_tags(page.search_description or ""),
        "sub_heading": "",
        "event_dates": page.event_dates,
        "start_datetime": None,
        "end_datetime": None,
        "location": "",
        "instructor": "",
        "member_cost": None,
        "public_cost": None,
        "purchase_url": "",
        "categories": [category.name for category in page.event_categories.all()],
        "notes": strip_tags(page.notes or ""),
        "additional_info": "",
        "is_upcoming": None,
    }


def _event_sort_key(result: dict) -> tuple[int, str, str]:
    start_datetime = result.get("start_datetime")
    return (
        0 if start_datetime else 1,
        start_datetime or "",
        result["title"].lower(),
    )


def _event_query_terms(query: str) -> list[str]:
    terms = []
    for term in re.findall(r"[a-z0-9]+", query.lower()):
        if len(term) < 3 or term in EVENT_QUERY_STOP_WORDS or term in terms:
            continue
        terms.append(term)
    return terms


def _event_page_term_filter(terms: list[str]) -> Q:
    if not terms:
        return Q()

    filters = Q()
    for term in terms:
        filters |= (
            Q(title__icontains=term)
            | Q(search_description__icontains=term)
            | Q(sub_heading__icontains=term)
            | Q(event_dates__icontains=term)
            | Q(location__icontains=term)
            | Q(instructor__icontains=term)
            | Q(additional_info__icontains=term)
            | Q(notes__icontains=term)
            | Q(body__icontains=term)
            | Q(event_categories__name__icontains=term)
        )
    return filters


def _event_general_page_term_filter(terms: list[str]) -> Q:
    if not terms:
        return Q()

    filters = Q()
    for term in terms:
        filters |= (
            Q(title__icontains=term)
            | Q(search_description__icontains=term)
            | Q(event_dates__icontains=term)
            | Q(notes__icontains=term)
            | Q(body__icontains=term)
            | Q(event_categories__name__icontains=term)
        )
    return filters


def _event_result_search_text(result: dict) -> str:
    searchable_bits = [
        result.get("title", ""),
        result.get("description", ""),
        result.get("sub_heading", ""),
        result.get("event_dates", ""),
        result.get("location", ""),
        result.get("instructor", ""),
        result.get("notes", ""),
        result.get("additional_info", ""),
        " ".join(result.get("categories") or []),
    ]
    return " ".join(bit for bit in searchable_bits if bit).lower()


def _event_result_score(result: dict, terms: list[str]) -> int:
    if not terms:
        return 0

    title_text = (result.get("title") or "").lower()
    category_text = " ".join(result.get("categories") or []).lower()
    searchable_text = _event_result_search_text(result)
    score = 0

    for term in terms:
        if term in title_text:
            score += 5
        elif term in category_text:
            score += 4
        elif term in searchable_text:
            score += 1

    return score


def _authorized(request) -> bool:
    expected_api_key = getattr(settings, "OAKLEY_DATA_API_KEY", "")
    if not expected_api_key:
        return False

    provided_api_key = request.headers.get("x-api-key", "")
    return provided_api_key == expected_api_key


def _auth_or_error(request) -> JsonResponse | None:
    expected_api_key = getattr(settings, "OAKLEY_DATA_API_KEY", "")
    if not expected_api_key:
        return _json_error("Oakley data API is not configured.", 503)

    if not _authorized(request):
        return _json_error("Unauthorized", 403)

    return None


@require_GET
def garden_events_data(request):
    auth_error = _auth_or_error(request)
    if auth_error is not None:
        return auth_error

    query = (request.GET.get("q") or "").strip()
    query_terms = _event_query_terms(query)
    upcoming_only = _get_bool_param(request, "upcoming_only", default=True)
    limit = _get_limit(request, default=5)
    now = timezone.now()

    event_page_filters = Q(alias_of__isnull=True)
    general_page_filters = Q(alias_of__isnull=True)

    if upcoming_only:
        event_page_filters &= Q(start_datetime__gte=now) | Q(start_datetime__isnull=True)

    if query_terms:
        event_page_filters &= _event_page_term_filter(query_terms)
        general_page_filters &= _event_general_page_term_filter(query_terms)

    event_pages = (
        EventPage.objects.live()
        .filter(event_page_filters)
        .prefetch_related("event_categories")
        .distinct()
    )
    general_pages = (
        EventGeneralPage.objects.live()
        .filter(general_page_filters)
        .prefetch_related("event_categories")
        .distinct()
    )

    results = [
        *[_serialize_event_page(page, request) for page in event_pages],
        *[_serialize_event_general_page(page, request) for page in general_pages],
    ]
    results = sorted(
        results,
        key=lambda result: (-_event_result_score(result, query_terms), *_event_sort_key(result)),
    )[:limit]

    return JsonResponse(
        {
            "query": query,
            "upcoming_only": upcoming_only,
            "count": len(results),
            "results": results,
        }
    )


def _serialize_family(family: Family) -> dict:
    return {
        "object_type": "family",
        "id": family.id,
        "name": family.name,
        "vernacular_name": family.vernacular_name,
    }


def _serialize_genus(genus: Genus) -> dict:
    return {
        "object_type": "genus",
        "id": genus.id,
        "name": genus.name,
        "family_name": genus.family.name,
    }


def _serialize_species(species: Species, request) -> dict:
    return {
        "object_type": "species",
        "id": species.id,
        "full_name": species.full_name,
        "vernacular_name": species.vernacular_name,
        "genus_name": species.genus.name,
        "family_name": species.genus.family.name,
        "habit": species.habit,
        "water_regime": species.water_regime,
        "exposure": species.exposure,
        "plant_size": species.plant_size,
        "flower_color": species.flower_color,
        "utah_native": species.utah_native,
        "plant_select": species.plant_select,
        "deer_resist": species.deer_resist,
        "rabbit_resist": species.rabbit_resist,
        "bee_friend": species.bee_friend,
        "high_elevation": species.high_elevation,
        "arborist_rec": species.arborist_rec,
        "url": request.build_absolute_uri(species.get_absolute_url()),
    }


def _serialize_collection(collection: Collection, request) -> dict:
    location = None
    if collection.location_id:
        location = {
            "latitude": str(collection.location.latitude),
            "longitude": str(collection.location.longitude),
        }

    return {
        "object_type": "collection",
        "id": collection.id,
        "plant_id": collection.plant_id,
        "species_full_name": collection.species.full_name,
        "species_vernacular_name": collection.species.vernacular_name,
        "garden_name": collection.garden.name if collection.garden_id else None,
        "garden_area": collection.garden.area if collection.garden_id else None,
        "plant_date": collection.plant_date.isoformat() if collection.plant_date else None,
        "commemoration_category": collection.commemoration_category,
        "commemoration_person": collection.commemoration_person,
        "location": location,
        "url": request.build_absolute_uri(collection.get_absolute_url()),
    }


def _serialize_garden_area(garden_area: GardenArea) -> dict:
    return {
        "object_type": "garden_area",
        "id": garden_area.id,
        "area": garden_area.area,
        "name": garden_area.name,
        "code": garden_area.code,
    }


def _serialize_bloom_event(bloom_event: BloomEvent) -> dict:
    return {
        "object_type": "bloom_event",
        "id": bloom_event.id,
        "title": bloom_event.title,
        "description": bloom_event.description,
        "species_full_name": bloom_event.species.full_name if bloom_event.species_id else None,
        "area_name": bloom_event.area.name if bloom_event.area_id else None,
        "area_code": bloom_event.area.code if bloom_event.area_id else None,
        "bloom_start": bloom_event.bloom_start.isoformat() if bloom_event.bloom_start else None,
        "bloom_end": bloom_event.bloom_end.isoformat() if bloom_event.bloom_end else None,
        "url": bloom_event.url,
    }


def _serialize_species_image(species_image: SpeciesImage) -> dict:
    image_url = None
    if getattr(species_image.image, "file", None):
        image_url = species_image.image.file.url

    return {
        "object_type": "species_image",
        "id": species_image.id,
        "species_full_name": species_image.species.full_name,
        "caption": species_image.caption,
        "copyright": species_image.copyright,
        "image_id": species_image.image_id,
        "image_url": image_url,
    }


def _serialize_location(location: Location) -> dict:
    return {
        "object_type": "location",
        "id": location.id,
        "latitude": str(location.latitude),
        "longitude": str(location.longitude),
    }


@require_GET
def plants_data(request):
    auth_error = _auth_or_error(request)
    if auth_error is not None:
        return auth_error

    query = (request.GET.get("q") or "").strip()
    in_bloom_only = _get_bool_param(request, "in_bloom", default=False)
    limit = _get_limit(request, default=5)

    if not query and not in_bloom_only:
        return _json_error("q is required unless in_bloom=true is provided.", 400)

    today = timezone.localdate()

    family_query = Family.objects.all()
    genus_query = Genus.objects.select_related("family")
    species_query = Species.objects.select_related("genus__family")
    collection_query = Collection.objects.select_related(
        "species", "species__genus__family", "garden", "location"
    )
    garden_area_query = GardenArea.objects.all()
    bloom_event_query = BloomEvent.objects.select_related("species", "area")
    species_image_query = SpeciesImage.objects.select_related("species", "image")

    if query:
        family_query = family_query.filter(
            Q(name__icontains=query) | Q(vernacular_name__icontains=query)
        )
        genus_query = genus_query.filter(
            Q(name__icontains=query)
            | Q(family__name__icontains=query)
            | Q(family__vernacular_name__icontains=query)
        )
        species_query = species_query.filter(
            Q(full_name__icontains=query)
            | Q(vernacular_name__icontains=query)
            | Q(genus__name__icontains=query)
            | Q(genus__family__name__icontains=query)
            | Q(habit__icontains=query)
            | Q(water_regime__icontains=query)
            | Q(exposure__icontains=query)
            | Q(flower_color__icontains=query)
            | Q(autolink_aliases__icontains=query)
        )
        collection_query = collection_query.filter(
            Q(plant_id__icontains=query)
            | Q(species__full_name__icontains=query)
            | Q(species__vernacular_name__icontains=query)
            | Q(garden__name__icontains=query)
            | Q(garden__area__icontains=query)
            | Q(commemoration_person__icontains=query)
            | Q(commemoration_category__icontains=query)
        )
        garden_area_query = garden_area_query.filter(
            Q(area__icontains=query) | Q(name__icontains=query) | Q(code__icontains=query)
        )
        bloom_event_query = bloom_event_query.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(species__full_name__icontains=query)
            | Q(area__name__icontains=query)
            | Q(area__area__icontains=query)
        )
        species_image_query = species_image_query.filter(
            Q(species__full_name__icontains=query)
            | Q(caption__icontains=query)
            | Q(copyright__icontains=query)
        )

    if in_bloom_only:
        bloom_event_query = bloom_event_query.filter(
            bloom_start__lte=today,
            bloom_end__gte=today,
        )

    location_results = []
    location_candidates = Location.objects.all().order_by("id")[: limit * 20]
    if query:
        normalized_query = query.lower()
        for location in location_candidates:
            location_text = f"{location.latitude} {location.longitude}".lower()
            if normalized_query in location_text:
                location_results.append(_serialize_location(location))
                if len(location_results) >= limit:
                    break

    payload = {
        "query": query,
        "in_bloom": in_bloom_only,
        "families": [_serialize_family(item) for item in family_query.order_by("name")[:limit]],
        "genera": [_serialize_genus(item) for item in genus_query.order_by("name")[:limit]],
        "species": [
            _serialize_species(item, request)
            for item in species_query.order_by("full_name")[:limit]
        ],
        "collections": [
            _serialize_collection(item, request)
            for item in collection_query.order_by("plant_id")[:limit]
        ],
        "garden_areas": [
            _serialize_garden_area(item)
            for item in garden_area_query.order_by("name")[:limit]
        ],
        "bloom_events": [
            _serialize_bloom_event(item)
            for item in bloom_event_query.order_by("bloom_start", "title")[:limit]
        ],
        "species_images": [
            _serialize_species_image(item)
            for item in species_image_query.order_by("id")[:limit]
        ],
        "locations": location_results,
    }
    payload["counts"] = {
        key: len(value)
        for key, value in payload.items()
        if isinstance(value, list)
    }

    return JsonResponse(payload)
