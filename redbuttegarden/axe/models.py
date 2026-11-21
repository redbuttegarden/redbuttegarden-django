"""Persistence used by the internal accessibility review workflow."""

from __future__ import annotations

from django.conf import settings
from django.db import models


class DocumentAccessibilityReview(models.Model):
    """Track an editor's accessibility review state for one Wagtail document."""

    document = models.OneToOneField(
        settings.WAGTAILDOCS_DOCUMENT_MODEL,
        on_delete=models.CASCADE,
        related_name="accessibility_review",
    )
    needs_accessibility_review = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("needs_accessibility_review", "document__title")
        verbose_name = "document accessibility review"
        verbose_name_plural = "document accessibility reviews"

    def __str__(self) -> str:
        """Return a concise editor-facing review label."""

        return f"Accessibility review: {self.document.title}"
