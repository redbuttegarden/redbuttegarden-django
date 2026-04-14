from django.core.management.base import BaseCommand

from concerts.models import ConcertDonorClubMember


class Command(BaseCommand):
    help = (
        "Mark all active Concert Donor Club members inactive so the current "
        "season's ticket sync can reactivate only members seen in fresh Etix data."
    )

    def handle(self, *args, **options):
        deactivated_count = 0

        for cdc_member in ConcertDonorClubMember.objects.filter(active=True).iterator():
            cdc_member.active = False
            cdc_member.save(update_fields=["active"])
            deactivated_count += 1

        self.stdout.write(
            self.style.SUCCESS(f"Deactivated {deactivated_count} Concert Donor Club members.")
        )
