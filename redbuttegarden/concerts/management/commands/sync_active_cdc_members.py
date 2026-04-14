from django.core.management.base import BaseCommand, CommandError

from concerts.services.active_cdc_members import (
    ActiveCDCRosterSyncError,
    sync_active_cdc_members_from_intranet,
)


class Command(BaseCommand):
    help = (
        "Pull the full active Concert Donor Club roster snapshot from the intranet "
        "and reconcile local CDC member active/profile data."
    )

    def handle(self, *args, **options):
        try:
            result = sync_active_cdc_members_from_intranet()
        except ActiveCDCRosterSyncError as exc:
            raise CommandError(f"Failed to sync active CDC members: {exc}") from exc

        self.stdout.write(
            self.style.SUCCESS(
                "Synced {total} active CDC members from {source}. "
                "Created users: {created_users}, updated users: {updated_users}, "
                "created members: {created_members}, activated members: {activated_members}, "
                "deactivated members: {deactivated_members}.".format(
                    total=result.total_members,
                    source=result.source or "unknown source",
                    created_users=result.created_users,
                    updated_users=result.updated_users,
                    created_members=result.created_members,
                    activated_members=result.activated_members,
                    deactivated_members=result.deactivated_members,
                )
            )
        )
