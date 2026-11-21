"""Audit contextual ImageBlock alt text in published Wagtail StreamFields."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from typing import Any

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from wagtail.blocks import ListBlock, StreamBlock, StructBlock
from wagtail.fields import StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.models import Page

from axe.a11y import is_blank_text


MAX_BATCH_SIZE = 20


def block_contains_image_block(block: Any) -> bool:
    """Return whether a StreamField block tree contains a Wagtail ImageBlock."""

    if isinstance(block, ImageBlock):
        return True
    if isinstance(block, (StreamBlock, StructBlock)):
        return any(block_contains_image_block(child) for child in block.child_blocks.values())
    if isinstance(block, ListBlock):
        return block_contains_image_block(block.child_block)
    return False


def get_raw_stream_data(field: StreamField, page: Page) -> Any:
    """Return serialized StreamField data without resolving referenced images."""

    value = field.value_from_object(page)
    raw_data = getattr(value, "raw_data", None)
    if raw_data is not None:
        return raw_data
    return field.get_prep_value(value)


def iter_image_block_values(
    block: Any, value: Any, path: tuple[str, ...] = ()
) -> Iterator[tuple[tuple[str, ...], Mapping[str, Any]]]:
    """Yield raw ImageBlock values and their stable StreamField paths."""

    if isinstance(block, ImageBlock):
        if isinstance(value, Mapping):
            yield path, value
        return
    if isinstance(block, StreamBlock) and isinstance(value, list):
        for index, item in enumerate(value):
            if not isinstance(item, Mapping):
                continue
            block_type = item.get("type")
            child = block.child_blocks.get(block_type)
            if child is not None:
                yield from iter_image_block_values(
                    child, item.get("value"), (*path, f"{block_type}[{index}]")
                )
        return
    if isinstance(block, StructBlock) and isinstance(value, Mapping):
        for name, child in block.child_blocks.items():
            if name in value:
                yield from iter_image_block_values(child, value[name], (*path, name))
        return
    if isinstance(block, ListBlock) and isinstance(value, list):
        for index, item in enumerate(value):
            item_value = item.get("value") if isinstance(item, Mapping) and "value" in item else item
            yield from iter_image_block_values(block.child_block, item_value, (*path, f"[{index}]"))


def get_raw_image_id(value: Mapping[str, Any]) -> int | str | None:
    """Extract an image primary key from current and legacy ImageBlock JSON."""

    image_value = value.get("image")
    if isinstance(image_value, Mapping):
        image_value = image_value.get("id")
    if isinstance(image_value, (int, str)):
        return image_value
    return None


class Command(BaseCommand):
    """Report contextual image uses that need editor-authored alt text."""

    help = "Audit non-decorative Wagtail ImageBlocks with blank contextual alt text."

    def add_arguments(self, parser: Any) -> None:
        """Register bounded live-page audit arguments."""

        parser.add_argument("--limit", type=int, default=MAX_BATCH_SIZE)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--after-id", type=int)
        parser.add_argument("--include-drafts", action="store_true")
        parser.add_argument(
            "--page-model",
            help="Restrict a resumable run to one page model label, for example home.GeneralPage.",
        )
        parser.add_argument(
            "--scan-limit",
            type=int,
            default=MAX_BATCH_SIZE,
            help="Maximum page rows inspected; must be between 1 and 20.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Write a compact JSON record for each missing contextual alt text value."""

        limit = options["limit"]
        offset = options["offset"]
        after_id = options.get("after_id")
        scan_limit = options["scan_limit"]
        if not 1 <= limit <= MAX_BATCH_SIZE:
            raise CommandError(f"--limit must be between 1 and {MAX_BATCH_SIZE}.")
        if not 1 <= scan_limit <= MAX_BATCH_SIZE:
            raise CommandError(f"--scan-limit must be between 1 and {MAX_BATCH_SIZE}.")
        if offset < 0 or (after_id is not None and after_id < 0):
            raise CommandError("--offset and --after-id must be zero or greater.")
        if offset and after_id is not None:
            raise CommandError("Use either --offset or --after-id, not both.")
        sources = self._get_streamfield_sources()
        if options["page_model"]:
            sources = [
                source for source in sources if source[0]._meta.label == options["page_model"]
            ]
            if not sources:
                raise CommandError("--page-model does not identify an auditable StreamField page model.")
        emitted = 0
        skipped = 0
        scanned_pages = 0
        last_page: Page | None = None
        for model, field in sources:
            queryset = model.objects.only("pk", field.name).order_by("pk")
            if not options["include_drafts"] and any(
                model_field.name == "live" for model_field in model._meta.get_fields()
            ):
                queryset = queryset.filter(live=True)
            if after_id is not None:
                queryset = queryset.filter(pk__gt=after_id)
            for page in queryset.iterator(chunk_size=MAX_BATCH_SIZE):
                scanned_pages += 1
                last_page = page
                raw_data = get_raw_stream_data(field, page)
                for path, image_value in iter_image_block_values(field.stream_block, raw_data):
                    if image_value.get("decorative") is True:
                        continue
                    if not is_blank_text(image_value.get("alt_text")):
                        continue
                    if skipped < offset:
                        skipped += 1
                        continue
                    self.stdout.write(
                        json.dumps(
                            {
                                "page_id": page.pk,
                                "page_model": model._meta.label,
                                "streamfield": field.name,
                                "block_path": ".".join(path),
                                "image_id": get_raw_image_id(image_value),
                            },
                            sort_keys=True,
                        )
                    )
                    emitted += 1
                    if emitted >= limit:
                        self._write_summary(emitted, scanned_pages, last_page)
                        return
                if scanned_pages >= scan_limit:
                    self._write_summary(emitted, scanned_pages, last_page)
                    return
        self._write_summary(emitted, scanned_pages, last_page)

    def _write_summary(
        self, emitted: int, scanned_pages: int, last_page: Page | None
    ) -> None:
        """Write bounded-scan progress suitable for a model-aware resume."""

        summary: dict[str, int | str | None] = {
            "count": emitted,
            "scanned_pages": scanned_pages,
            "last_page_id": last_page.pk if last_page else None,
            "last_page_model": last_page._meta.label if last_page else None,
        }
        self.stdout.write(json.dumps(summary, sort_keys=True))

    @staticmethod
    def _get_streamfield_sources() -> list[tuple[type[Page], StreamField]]:
        """Return concrete page StreamFields whose definitions contain ImageBlocks."""

        sources: list[tuple[type[Page], StreamField]] = []
        seen_sources: set[tuple[str, str]] = set()
        for model in apps.get_models():
            if not issubclass(model, Page) or model is Page or model._meta.proxy:
                continue
            for field in model._meta.get_fields():
                if isinstance(field, StreamField) and block_contains_image_block(field.stream_block):
                    owner = field.model
                    source_key = (owner._meta.label, field.name)
                    if source_key not in seen_sources:
                        sources.append((owner, field))
                        seen_sources.add(source_key)
        return sources
