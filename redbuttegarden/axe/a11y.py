"""Shared, bounded helpers for accessibility management commands."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from typing import Any

from django.db.models import Model, Q, QuerySet
from django.db.models.functions import Trim
from wagtail.images import get_image_model

from plants.models import PlantImage, SpeciesImage


ALT_TEXT_FIELD_CANDIDATES = ("description", "alt_text", "alt")


def get_image_alt_text_field(override: str | None = None) -> str:
    """Return the configured image model field used for shared alt text.

    Wagtail installations differ in whether this value is called
    ``description``, ``alt_text``, or ``alt``.  The explicit command-line
    override is useful when a custom image model uses a project-specific
    field name.
    """

    image_model = get_image_model()
    field_names = {field.name for field in image_model._meta.get_fields()}
    candidates = (override,) if override else ALT_TEXT_FIELD_CANDIDATES
    for field_name in candidates:
        if field_name and field_name in field_names:
            return field_name
    available = ", ".join(sorted(field_names))
    raise ValueError(
        "The active Wagtail image model has no supported shared alt-text field. "
        f"Available fields: {available}"
    )


def blank_text_filter(field_name: str) -> Q:
    """Return a database filter matching null, empty, or whitespace-only text."""

    return Q(**{f"{field_name}__isnull": True}) | Q(**{f"{field_name}__exact": ""})


def get_blank_image_queryset(
    *, alt_field: str, after_id: int | None = None
) -> QuerySet[Model]:
    """Return active-image candidates with blank shared accessibility text.

    ``Trim`` catches legacy values that contain only whitespace while keeping
    selection in PostgreSQL instead of materialising the image table.
    """

    image_model = get_image_model()
    fields = ["pk", alt_field]
    model_field_names = {field.name for field in image_model._meta.get_fields()}
    for optional_field in ("title", "collection"):
        if optional_field in model_field_names:
            fields.append(optional_field)
    queryset: QuerySet[Model] = (
        image_model.objects.only(*fields)
        .annotate(_a11y_trimmed_text=Trim(alt_field))
        .filter(blank_text_filter(alt_field) | Q(_a11y_trimmed_text=""))
        .order_by("pk")
    )
    if after_id is not None:
        queryset = queryset.filter(pk__gt=after_id)
    return queryset


def get_botanical_context(image_ids: Iterable[int]) -> dict[int, set[str]]:
    """Return distinct scientific names attached to each supplied image ID.

    The two queries deliberately fetch only relation values, avoiding an
    image-by-image traversal of plant data.
    """

    ids = list(image_ids)
    context: dict[int, set[str]] = defaultdict(set)
    if not ids:
        return context
    for image_id, full_name in SpeciesImage.objects.filter(image_id__in=ids).values_list(
        "image_id", "species__full_name"
    ):
        if full_name:
            context[image_id].add(full_name)
    for image_id, full_name in PlantImage.objects.filter(image_id__in=ids).values_list(
        "image_id", "collection__species__full_name"
    ):
        if full_name:
            context[image_id].add(full_name)
    return context


def get_single_botanical_name(context: dict[int, set[str]], image_id: int) -> str | None:
    """Return a botanical name only when the image has one unambiguous match."""

    names = context.get(image_id, set())
    return next(iter(names)) if len(names) == 1 else None


def is_blank_text(value: Any) -> bool:
    """Return whether a value is absent or has no non-whitespace text."""

    return not isinstance(value, str) or not value.strip()
