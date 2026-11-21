"""Focused regression tests for accessibility-management command helpers."""

from __future__ import annotations

import json
from io import StringIO
from types import SimpleNamespace

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from wagtail.images import get_image_model
from wagtail.images.blocks import ImageBlock
from wagtail.images.tests.utils import get_test_image_file
from wagtail.documents import get_document_model

from axe.a11y import get_image_alt_text_field, is_blank_text
from axe.management.commands.audit_a11y_documents import get_document_flags
from axe.management.commands.audit_a11y_imageblocks import iter_image_block_values
from axe.models import DocumentAccessibilityReview
from axe.wagtail_hooks import (
    DocumentAccessibilityReviewFormPermissionMixin,
    DocumentAccessibilityReviewViewSet,
    register_document_accessibility_review_viewset,
)
from plants.models import SpeciesImage


def test_active_image_model_uses_a_supported_shared_text_field() -> None:
    """The project image model exposes the field selected by the audit command."""

    field_name = get_image_alt_text_field()

    assert field_name in {field.name for field in get_image_model()._meta.get_fields()}


def test_blank_text_treats_none_and_whitespace_as_missing() -> None:
    """Legacy whitespace-only text remains an audit candidate."""

    assert is_blank_text(None)
    assert is_blank_text(" \n\t")
    assert not is_blank_text("A flowering plant")


def test_document_flags_remain_database_only_triage() -> None:
    """The document audit flags title concerns without asserting PDF compliance."""

    flags = get_document_flags("Document", "uploads/annual-report.pdf")

    assert "generic_title" in flags
    assert "embedded_metadata_unverified" in flags


def test_imageblock_audit_skips_decorative_images() -> None:
    """Blank contextual text is valid when an ImageBlock is marked decorative."""

    block = ImageBlock()
    decorative = {"image": 5, "alt_text": "", "decorative": True}
    informative = {"image": 6, "alt_text": "", "decorative": False}

    values = list(iter_image_block_values(block, decorative))
    values.extend(iter_image_block_values(block, informative))

    missing_ids = [value["image"] for _, value in values if not value["decorative"]]
    assert missing_ids == [6]


def test_document_review_viewset_registers_without_constructor_arguments() -> None:
    """The Wagtail 7 hook constructs the admin viewset using its supported API."""

    assert isinstance(
        register_document_accessibility_review_viewset(), DocumentAccessibilityReviewViewSet
    )


@pytest.mark.django_db
def test_image_audit_paginates_and_reports_unambiguous_botanical_context(species) -> None:
    """The shared-image audit remains bounded and adds the linked scientific name."""

    image_model = get_image_model()
    first_image = image_model.objects.create(
        title="First image", file=get_test_image_file(), description=""
    )
    second_image = image_model.objects.create(
        title="Second image", file=get_test_image_file(), description=""
    )
    SpeciesImage.objects.create(species=species, image=first_image, sort_order=0)

    first_output = StringIO()
    call_command("audit_a11y_images", "--limit", "1", stdout=first_output)
    first_records = [json.loads(line) for line in first_output.getvalue().splitlines()]
    assert first_records[1]["image_id"] == first_image.pk
    assert first_records[1]["botanical_names"] == [species.full_name]

    second_output = StringIO()
    call_command("audit_a11y_images", "--limit", "1", "--offset", "1", stdout=second_output)
    second_records = [json.loads(line) for line in second_output.getvalue().splitlines()]
    assert second_records[1]["image_id"] == second_image.pk


@pytest.mark.django_db
def test_document_flag_command_creates_a_persistent_review_record() -> None:
    """A title-related PDF finding creates one review record for staff follow-up."""

    document = get_document_model().objects.create(
        title="Document",
        file=SimpleUploadedFile("accessibility.pdf", b"%PDF-1.4", "application/pdf"),
    )

    call_command("flag_a11y_documents", "--limit", "1")

    review = DocumentAccessibilityReview.objects.get(document_id=document.pk)
    assert review.needs_accessibility_review is True


def test_document_review_form_filters_document_chooser_to_collection_permissions(monkeypatch) -> None:
    """The Wagtail form never presents documents outside the editor's collections."""

    permitted_documents = object()
    fake_user = object()

    class BaseView:
        request = SimpleNamespace(user=fake_user)

        def get_form(self, form_class=None):
            return SimpleNamespace(fields={"document": SimpleNamespace(queryset=None)})

    class TestView(DocumentAccessibilityReviewFormPermissionMixin, BaseView):
        pass

    monkeypatch.setattr(
        "axe.wagtail_hooks.document_permission_policy.instances_user_has_any_permission_for",
        lambda user, actions: permitted_documents,
    )

    form = TestView().get_form()

    assert form.fields["document"].queryset is permitted_documents
