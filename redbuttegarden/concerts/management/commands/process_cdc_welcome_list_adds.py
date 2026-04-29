import logging

from django.core.management.base import BaseCommand, CommandError

from concerts.services.cdc_welcome_list import (
    CDCWelcomeListError,
    process_cdc_welcome_list_adds,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process queued one-time Constant Contact welcome list enrollments for CDC members."

    def add_arguments(self, parser):
        parser.add_argument("--list-id", help="Constant Contact list id. Defaults to the Wagtail CDC list setting.")
        parser.add_argument("--limit", type=int, default=25)
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--stale-processing-minutes", type=int, default=60)

    def handle(self, *args, **options):
        logger.info(
            "Running process_cdc_welcome_list_adds command: list_id=%s limit=%s dry_run=%s stale_processing_minutes=%s",
            options["list_id"],
            options["limit"],
            options["dry_run"],
            options["stale_processing_minutes"],
        )
        try:
            result = process_cdc_welcome_list_adds(
                list_id=options["list_id"],
                limit=options["limit"],
                dry_run=options["dry_run"],
                stale_processing_minutes=options["stale_processing_minutes"],
            )
        except CDCWelcomeListError as exc:
            logger.error("process_cdc_welcome_list_adds failed: %s", exc)
            raise CommandError(str(exc)) from exc

        verb = "Would process" if result.dry_run else "Processed"
        logger.info(
            "Finished process_cdc_welcome_list_adds command: list_id=%s dry_run=%s considered=%s processed=%s added=%s already_member=%s skipped=%s failed=%s",
            result.list_id,
            result.dry_run,
            result.considered,
            result.processed,
            result.added,
            result.already_member,
            result.skipped,
            result.failed,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} {result.considered} CDC welcome list rows for Constant Contact list {result.list_id}. "
                f"Added: {result.added}, already members: {result.already_member}, "
                f"skipped: {result.skipped}, failed: {result.failed}."
            )
        )
