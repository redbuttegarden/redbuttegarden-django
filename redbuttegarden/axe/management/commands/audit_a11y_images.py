"""Audit shared Wagtail image accessibility text without changing content."""

from __future__ import annotations

import json
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from axe.a11y import get_blank_image_queryset, get_botanical_context, get_image_alt_text_field


MAX_BATCH_SIZE = 20


class Command(BaseCommand):
    """Report a bounded page of images missing shared accessibility text."""

    help = "Audit Wagtail images with missing shared accessibility text."

    def add_arguments(self, parser: Any) -> None:
        """Register bounded, resumable audit arguments."""

        parser.add_argument("--limit", type=int, default=MAX_BATCH_SIZE)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--after-id", type=int)
        parser.add_argument("--alt-field")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Accepted for operational consistency; this audit is always read-only.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Write one compact JSON record per missing-text image."""

        limit = self._get_limit(options["limit"])
        offset = options["offset"]
        after_id = options.get("after_id")
        if offset < 0:
            raise CommandError("--offset must be zero or greater.")
        if after_id is not None and after_id < 0:
            raise CommandError("--after-id must be zero or greater.")
        if offset and after_id is not None:
            raise CommandError("Use either --offset or --after-id, not both.")
        try:
            alt_field = get_image_alt_text_field(options.get("alt_field"))
        except ValueError as error:
            raise CommandError(str(error)) from error

        queryset = get_blank_image_queryset(alt_field=alt_field, after_id=after_id)
        if offset:
            queryset = queryset[offset:]
        images = list(queryset[:limit].iterator(chunk_size=MAX_BATCH_SIZE))
        botanical_context = get_botanical_context([image.pk for image in images])
        self.stdout.write(
            json.dumps(
                {"alt_field": alt_field, "count": len(images), "read_only": True},
                sort_keys=True,
            )
        )
        for image in images:
            names = sorted(botanical_context.get(image.pk, set()))
            self.stdout.write(
                json.dumps(
                    {
                        "image_id": image.pk,
                        "title": getattr(image, "title", ""),
                        "botanical_names": names,
                        "botanical_context": (
                            "single" if len(names) == 1 else "ambiguous" if names else "none"
                        ),
                    },
                    sort_keys=True,
                )
            )

    @staticmethod
    def _get_limit(value: int) -> int:
        """Validate the hard production batch bound."""

        if not 1 <= value <= MAX_BATCH_SIZE:
            raise CommandError(f"--limit must be between 1 and {MAX_BATCH_SIZE}.")
        return value
