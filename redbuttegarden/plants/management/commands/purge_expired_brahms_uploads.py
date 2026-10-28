"""Remove expired direct-upload records after their 24-hour retention window."""

from django.core.management.base import BaseCommand

from plants.direct_uploads import purge_expired_pending_uploads


class Command(BaseCommand):
    """Purge database state for expired BRAHMS direct uploads."""

    help = "Delete expired BRAHMS direct-upload records."

    def handle(self, *args: object, **options: object) -> None:
        """Delete expired rows and report the count for scheduled-job observability."""

        deleted = purge_expired_pending_uploads()
        self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} expired pending upload(s)."))
