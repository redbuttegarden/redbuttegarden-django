from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Create Wagtail Pages for each Altru event'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Searching for Altru events...'))
