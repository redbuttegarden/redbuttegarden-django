"""Wagtail administration integration for broadcast notifications."""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import QuerySet
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseBadRequest
from django.urls import URLPattern
from django.utils import timezone
from wagtail import hooks
from wagtail.admin.panels import ObjectList
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.bulk_actions.delete import DeleteBulkAction
from wagtail.snippets.views.snippets import CreateView, EditView, SnippetViewSet

from .forms import PushNotificationForm, TERMINAL_STATUSES
from .models import PushNotification
from .permissions import PushNotificationPermissionPolicy


class PushNotificationEditorViewMixin:
    """Apply explicit editor actions without exposing system lifecycle states."""

    ACTION_SAVE_DRAFT = "action-save-draft"
    ACTION_SCHEDULE = "action-schedule"
    ACTION_SEND_NOW = "action-send-now"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Provide template state for guidance, action buttons, and locked records."""

        context = super().get_context_data(**kwargs)
        notification = getattr(self, "object", None)
        if notification is None:
            form = kwargs.get("form") or getattr(self, "form", None)
            notification = form.instance if form is not None else PushNotification()
        context["notification_is_locked"] = bool(
            notification.pk and notification.status in TERMINAL_STATUSES
        )
        context["notification_status_label"] = notification.get_status_display()
        context["notification_index_url"] = self.get_success_url()
        return context

    def form_valid(self, form: PushNotificationForm) -> HttpResponse:
        """Apply the selected draft, schedule, or send-now action before saving."""

        action = next(
            (
                requested_action
                for requested_action in (
                    self.ACTION_SAVE_DRAFT,
                    self.ACTION_SCHEDULE,
                    self.ACTION_SEND_NOW,
                )
                if self.request.POST.get(requested_action)
            ),
            None,
        )
        if action is None:
            return HttpResponseBadRequest("Choose a notification action.")

        with transaction.atomic():
            # UUID primary keys are assigned before an unsaved model instance
            # reaches CreateView, so `_state.adding` is the reliable persisted
            # record check here.
            if not form.instance._state.adding:
                current = PushNotification.objects.select_for_update().get(pk=form.instance.pk)
                if current.status in TERMINAL_STATUSES:
                    # A scheduler claim may have happened after this editor opened the form.
                    # Preserve that current state rather than saving stale form data over it.
                    form.instance.status = current.status
                    self.object = current
                    form.add_error(
                        None,
                        "This notification is now being processed or is complete and cannot be edited.",
                    )
                    return self.form_invalid(form)

            if action == self.ACTION_SAVE_DRAFT:
                form.instance.status = PushNotification.Status.DRAFT
                form.instance.scheduled_time = None
            elif action == self.ACTION_SCHEDULE:
                form.instance.status = PushNotification.Status.SCHEDULED
            else:
                form.instance.status = PushNotification.Status.SCHEDULED
                form.instance.scheduled_time = timezone.now()

            try:
                form.instance.clean()
            except ValidationError as error:
                if hasattr(error, "message_dict"):
                    for field, messages in error.message_dict.items():
                        for message in messages:
                            form.add_error(
                                field if field in form.fields else None, message)
                else:
                    form.add_error(None, error)
                return self.form_invalid(form)

            return super().form_valid(form)


class PushNotificationCreateView(PushNotificationEditorViewMixin, CreateView):
    """Create notifications with editor-owned delivery actions."""


class PushNotificationEditView(PushNotificationEditorViewMixin, EditView):
    """Edit notifications and expose aggregate-only analytics to authorized editors."""

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add the notification instance used by the analytics dashboard template."""

        context = super().get_context_data(**kwargs)
        context["analytics_notification"] = self.object
        return context


class DisabledPushNotificationBulkDeleteAction(DeleteBulkAction):
    """Block the globally registered snippet bulk-delete action for audit history."""

    models = [PushNotification]

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        """Make bulk deletion unavailable even when the generic Wagtail route exists."""

        raise Http404


class PushNotificationViewSet(SnippetViewSet):
    """Configure the editor-facing history and edit experience."""

    model = PushNotification
    edit_handler = ObjectList(PushNotification.panels,
                              base_form_class=PushNotificationForm)
    permission_policy = PushNotificationPermissionPolicy(PushNotification)
    icon = "mail"
    menu_label = "Notifications"
    menu_order = 260
    add_to_admin_menu = True
    list_display = [
        "title",
        "scheduled_time",
        "sent_at",
        "status",
        "subscriber_count_at_send",
        "accepted_count",
        "click_count",
        UpdatedAtColumn(),
    ]
    list_filter = {"status": ["exact"],
                   "scheduled_time": ["date"], "sent_at": ["date"]}
    search_fields = ("title", "body")
    ordering = ("-created_at",)
    copy_view_enabled = False
    # Analytics are shown in the controlled edit view; the generic inspect view
    # is not needed and could expose operational fields to additional users.
    inspect_view_enabled = False
    add_view_class = PushNotificationCreateView
    edit_view_class = PushNotificationEditView
    create_template_name = "push_notifications/wagtail/create.html"
    edit_template_name = "push_notifications/wagtail/edit.html"

    def get_permissions_to_register(self) -> QuerySet[Permission]:
        """Expose only the custom notification permission in Groups UI."""

        content_type = ContentType.objects.get_for_model(self.model)
        return Permission.objects.filter(
            content_type=content_type,
            codename="manage_push_notifications",
        )

    def get_urlpatterns(self) -> list[URLPattern]:
        """Remove the destructive single-notification route from this viewset."""

        return [
            pattern for pattern in super().get_urlpatterns() if pattern.name != "delete"
        ]


register_snippet(PushNotificationViewSet)
hooks.register("register_bulk_action", DisabledPushNotificationBulkDeleteAction)
