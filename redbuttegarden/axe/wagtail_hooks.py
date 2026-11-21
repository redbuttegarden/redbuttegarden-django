"""Wagtail admin registration for document accessibility-review records."""

from __future__ import annotations

from typing import Any

from django.core.exceptions import PermissionDenied
from wagtail import hooks
from wagtail.documents.permissions import permission_policy as document_permission_policy
from wagtail.snippets.views.snippets import (
    CreateView,
    DeleteView,
    EditView,
    IndexView,
    SnippetViewSet,
)

from .models import DocumentAccessibilityReview


class DocumentAccessibilityReviewFormPermissionMixin:
    """Restrict document chooser choices to the editor's collections."""

    def get_form(self, form_class: type[Any] | None = None) -> Any:
        """Return a form whose document field cannot disclose other collections."""

        form = super().get_form(form_class)
        document_field = form.fields.get("document")
        if document_field is not None:
            document_field.queryset = (
                document_permission_policy.instances_user_has_any_permission_for(
                    self.request.user, ["change"]
                )
            )
        return form


class DocumentAccessibilityReviewIndexView(IndexView):
    """Restrict the queue to documents the current editor may change."""

    def get_queryset(self) -> Any:
        """Return review records only for the editor's document collections."""

        queryset = super().get_queryset()
        permitted_documents = document_permission_policy.instances_user_has_any_permission_for(
            self.request.user, ["change"]
        )
        return queryset.filter(document__in=permitted_documents)


class DocumentAccessibilityReviewEditView(DocumentAccessibilityReviewFormPermissionMixin, EditView):
    """Block direct review URLs for documents outside an editor's collection scope."""

    def get_object(self, queryset: Any = None) -> DocumentAccessibilityReview:
        """Return an authorized review record or raise a permission error."""

        review = super().get_object(queryset)
        if not document_permission_policy.user_has_permission_for_instance(
            self.request.user, "change", review.document
        ):
            raise PermissionDenied
        return review

    def form_valid(self, form: Any) -> Any:
        """Prevent changing a review to reference an unauthorized document."""

        if not document_permission_policy.user_has_permission_for_instance(
            self.request.user, "change", form.instance.document
        ):
            raise PermissionDenied
        return super().form_valid(form)


class DocumentAccessibilityReviewCreateView(DocumentAccessibilityReviewFormPermissionMixin, CreateView):
    """Require collection-level document change access when creating a review."""

    def form_valid(self, form: Any) -> Any:
        """Reject attempts to attach a review to an unauthorized document."""

        document = form.instance.document
        if not document_permission_policy.user_has_permission_for_instance(
            self.request.user, "change", document
        ):
            raise PermissionDenied
        return super().form_valid(form)


class DocumentAccessibilityReviewDeleteView(DeleteView):
    """Require document collection access before deleting a review record."""

    def get_object(self, queryset: Any = None) -> DocumentAccessibilityReview:
        """Return an authorized review record or raise a permission error."""

        review = super().get_object(queryset)
        if not document_permission_policy.user_has_permission_for_instance(
            self.request.user, "change", review.document
        ):
            raise PermissionDenied
        return review


class DocumentAccessibilityReviewViewSet(SnippetViewSet):
    """Provide staff a compact Wagtail-admin queue for document review."""

    model = DocumentAccessibilityReview
    icon = "doc-full"
    menu_label = "Document accessibility reviews"
    menu_name = "document-accessibility-reviews"
    admin_url_namespace = "document_accessibility_reviews"
    base_url_path = "accessibility/document-reviews"
    list_display = ("document", "needs_accessibility_review", "updated_at")
    list_filter = ("needs_accessibility_review",)
    search_fields = ("document__title", "notes")
    copy_view_enabled = False
    inspect_view_enabled = False
    index_view_class = DocumentAccessibilityReviewIndexView
    edit_view_class = DocumentAccessibilityReviewEditView
    add_view_class = DocumentAccessibilityReviewCreateView
    delete_view_class = DocumentAccessibilityReviewDeleteView


@hooks.register("register_admin_viewset")
def register_document_accessibility_review_viewset() -> DocumentAccessibilityReviewViewSet:
    """Register the Wagtail-admin review queue."""

    return DocumentAccessibilityReviewViewSet()
