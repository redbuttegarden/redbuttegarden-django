"""Create review-queue entries for PDFs with database metadata concerns."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand, CommandError
from wagtail.documents import get_document_model

from axe.models import DocumentAccessibilityReview
from axe.management.commands.audit_a11y_documents import MAX_BATCH_SIZE, get_document_flags


class Command(BaseCommand):
    """Add new document review records without resetting editorial decisions."""

    help = "Flag PDFs with blank or generic Wagtail titles for accessibility review."

    def add_arguments(self, parser: Any) -> None:
        """Register bounded, resumable mutation arguments."""

        parser.add_argument("--limit", type=int, default=MAX_BATCH_SIZE)
        parser.add_argument("--after-id", type=int)
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args: Any, **options: Any) -> None:
        """Create only missing records for PDFs that have title-related flags."""

        limit = options["limit"]
        after_id = options.get("after_id")
        if not 1 <= limit <= MAX_BATCH_SIZE:
            raise CommandError(f"--limit must be between 1 and {MAX_BATCH_SIZE}.")
        if after_id is not None and after_id < 0:
            raise CommandError("--after-id must be zero or greater.")
        document_model = get_document_model()
        queryset = document_model.objects.only("pk", "title", "file").filter(
            file__iendswith=".pdf"
        ).order_by("pk")
        if after_id is not None:
            queryset = queryset.filter(pk__gt=after_id)
        created = 0
        candidates = 0
        for document in queryset[:limit].iterator(chunk_size=MAX_BATCH_SIZE):
            filename = document.file.name if document.file else ""
            flags = get_document_flags(document.title, filename)
            if not {"blank_title", "generic_title", "filename_as_title"}.intersection(flags):
                continue
            candidates += 1
            if not options["dry_run"]:
                _, was_created = DocumentAccessibilityReview.objects.get_or_create(
                    document_id=document.pk,
                    defaults={"needs_accessibility_review": True},
                )
                created += int(was_created)
        self.stdout.write(
            self.style.SUCCESS(
                f"Processed {candidates} flagged PDFs; created {created} review records."
            )
        )
