"""Wagtail editing rules for notification lifecycle fields."""

from __future__ import annotations

from django import forms

from .models import DEFAULT_ICON_PATH, PushNotification


TERMINAL_STATUSES = {
    PushNotification.Status.SENDING,
    PushNotification.Status.SENT,
    PushNotification.Status.FAILED,
    PushNotification.Status.CANCELLED,
}


class PushNotificationForm(forms.ModelForm):
    """Present plain-language, editor-owned notification fields only."""

    class Meta:
        model = PushNotification
        fields = ["title", "body", "icon_path", "destination_path", "scheduled_time"]

    def __init__(self, *args: object, **kwargs: object) -> None:
        """Apply editor guidance and lock finished notifications."""

        super().__init__(*args, **kwargs)
        self.fields["title"].help_text = (
            "The header text shown at the top of the push notification "
            "(e.g., 'Spring Bloom Alert!')."
        )
        self.fields["body"].help_text = (
            "The main message text (1-2 short sentences). Keep it concise so it fits on mobile screens."
        )
        self.fields["destination_path"].help_text = (
            "The page on redbuttegarden.org visitors go to when clicking the notification. "
            "Must start with a forward slash (for example, /events or /blooms)."
        )
        self.fields["icon_path"].help_text = (
            "Optional. The path to a custom icon image. Defaults to the garden's standard mobile app "
            "icon if left blank."
        )
        self.fields["icon_path"].required = False
        self.fields["scheduled_time"].help_text = (
            "The date and time this notification should be sent. The automated background system "
            "checks for due notifications every 5 minutes."
        )
        if self.instance.pk and self.instance.status in TERMINAL_STATUSES:
            for field in self.fields.values():
                field.disabled = True

    def clean_icon_path(self) -> str:
        """Use the standard PWA icon when an editor leaves this optional field blank."""

        return self.cleaned_data["icon_path"] or DEFAULT_ICON_PATH
