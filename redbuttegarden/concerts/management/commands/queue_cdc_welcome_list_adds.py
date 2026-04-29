import logging

from django.core.management.base import BaseCommand, CommandError

from concerts.models import ConcertDonorClubWelcomeListAdd
from concerts.services.cdc_welcome_list import (
    CDCWelcomeListError,
    queue_active_cdc_members_for_welcome_list,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Queue active CDC members for one-time Constant Contact welcome list enrollment."

    def add_arguments(self, parser):
        parser.add_argument("--list-id", help="Constant Contact list id. Defaults to the Wagtail CDC list setting.")
        parser.add_argument(
            "--source",
            default=ConcertDonorClubWelcomeListAdd.Source.MANUAL,
            choices=[choice[0] for choice in ConcertDonorClubWelcomeListAdd.Source.choices],
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        logger.info(
            "Running queue_cdc_welcome_list_adds command: list_id=%s source=%s dry_run=%s",
            options["list_id"],
            options["source"],
            options["dry_run"],
        )
        try:
            result = queue_active_cdc_members_for_welcome_list(
                list_id=options["list_id"],
                source=options["source"],
                dry_run=options["dry_run"],
            )
        except CDCWelcomeListError as exc:
            logger.error("queue_cdc_welcome_list_adds failed: %s", exc)
            raise CommandError(str(exc)) from exc

        prefix = "Would queue" if result.dry_run else "Queued"
        logger.info(
            "Finished queue_cdc_welcome_list_adds command: list_id=%s dry_run=%s active_checked=%s queued=%s existing=%s skipped=%s",
            result.list_id,
            result.dry_run,
            result.total_active_members,
            result.queued,
            result.existing,
            result.skipped,
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix} {result.queued} active CDC members for Constant Contact list {result.list_id}. "
                f"Existing: {result.existing}, skipped: {result.skipped}, active checked: {result.total_active_members}."
            )
        )
