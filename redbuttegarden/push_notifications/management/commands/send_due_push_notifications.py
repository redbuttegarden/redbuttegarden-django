"""Dispatch due Web Push notifications from a Zappa scheduled event."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from push_notifications.services import (
    claim_due_notifications,
    dispatch_notification,
    purge_inactive_subscribers,
    purge_request_rate_limits,
)


class Command(BaseCommand):
    """Run bounded due-notification work and inactive subscription cleanup."""

    help = "Dispatch due Web Push notifications and purge expired inactive subscriptions."

    def handle(self, *args: object, **options: object) -> None:
        """Claim work, dispatch each notification, and report aggregate results."""

        for notification_id, lease_token in claim_due_notifications():
            result = dispatch_notification(notification_id, lease_token)
            self.stdout.write(
                f"{notification_id}: accepted={result.accepted} failed={result.failed} expired={result.expired}"
            )
        purged = purge_inactive_subscribers()
        rate_limits_purged = purge_request_rate_limits()
        self.stdout.write(
            f"Purged {purged} inactive Web Push subscriptions and {rate_limits_purged} rate-limit records."
        )
