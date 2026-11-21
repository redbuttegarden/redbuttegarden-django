"""Audit Wagtail PDF records using only inexpensive database metadata."""

from __future__ import annotations

import json
from pathlib import PurePosixPath
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from wagtail.documents import get_document_model


MAX_BATCH_SIZE = 20
GENERIC_TITLES = {"document", "pdf", "untitled"}


def get_document_flags(title: str | None, filename: str) -> list[str]:
    """Return low-cost triage flags without opening a PDF from object storage."""

    normalized_title = (title or "").strip()
    stem = PurePosixPath(filename).stem.strip()
    flags: list[str] = []
    if not normalized_title:
        flags.append("blank_title")
    elif normalized_title.casefold() in GENERIC_TITLES:
        flags.append("generic_title")
    elif stem and normalized_title.casefold() == stem.casefold():
        flags.append("filename_as_title")
    flags.append("embedded_metadata_unverified")
    return flags


class Command(BaseCommand):
    """Report a bounded page of PDFs needing low-cost accessibility triage."""

    help = "Audit Wagtail PDFs using database metadata without downloading files."

    def add_arguments(self, parser: Any) -> None:
        """Register bounded audit pagination arguments."""

        parser.add_argument("--limit", type=int, default=MAX_BATCH_SIZE)
        parser.add_argument("--offset", type=int, default=0)
        parser.add_argument("--after-id", type=int)

    def handle(self, *args: Any, **options: Any) -> None:
        """Write a JSON triage record for each selected PDF."""

        limit = options["limit"]
        offset = options["offset"]
        after_id = options.get("after_id")
        if not 1 <= limit <= MAX_BATCH_SIZE:
            raise CommandError(f"--limit must be between 1 and {MAX_BATCH_SIZE}.")
        if offset < 0 or (after_id is not None and after_id < 0):
            raise CommandError("--offset and --after-id must be zero or greater.")
        if offset and after_id is not None:
            raise CommandError("Use either --offset or --after-id, not both.")
        document_model = get_document_model()
        fields = ["pk", "title", "file"]
        model_fields = {field.name for field in document_model._meta.get_fields()}
        fields.extend(field for field in ("file_size", "created_at") if field in model_fields)
        queryset = document_model.objects.only(*fields).filter(file__iendswith=".pdf").order_by("pk")
        if after_id is not None:
            queryset = queryset.filter(pk__gt=after_id)
        if offset:
            queryset = queryset[offset:]
        documents = list(queryset[:limit].iterator(chunk_size=MAX_BATCH_SIZE))
        self.stdout.write(json.dumps({"count": len(documents), "read_only": True}, sort_keys=True))
        for document in documents:
            filename = document.file.name if document.file else ""
            self.stdout.write(
                json.dumps(
                    {
                        "document_id": document.pk,
                        "title": document.title,
                        "filename": filename,
                        "flags": get_document_flags(document.title, filename),
                    },
                    sort_keys=True,
                )
            )
