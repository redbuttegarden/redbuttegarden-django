from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from requests_oauthlib import OAuth2Session
from wagtail.models import Page

from altru.models import AltruAccessToken
from altru.utils import token_saver
from events.models import EventPage


class Command(BaseCommand):
    help = 'Create Wagtail Pages for Altru events'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Getting Altru events...'))

        try:
            altru_token = AltruAccessToken.objects.latest()
        except AltruAccessToken.DoesNotExist:
            raise CommandError('No token found.')

        blackbaud = OAuth2Session(settings.ALTRU_API_CLIENT_ID, token=altru_token.token,
                                  auto_refresh_url=settings.ALTRU_TOKEN_URL,
                                  token_updater=token_saver)
        response = blackbaud.get(f'{settings.ALTRU_API_BASE}/alt-evtmg/events/search?limit=100',
                                  headers={'Bb-Api-Subscription-Key': settings.ALTRU_API_SUBSCRIPTION_KEY,
                                           'REDatabaseToUse': settings.ALTRU_DATABASE_NAME}).json()

        self.stdout.write(self.style.SUCCESS(f'Retrieved Altru events: {response}'))

        event_index = Page.objects.get(title='Events')
        for event_info in response['value']:
            self.stdout.write(self.style.SUCCESS(f'Creating event page using info: {event_info}'))
            event_page = EventPage(title=event_info['name'])
            event_index.add_child(instance=event_page)
            event_page.save_revision().publish()

        self.stdout.write(self.style.SUCCESS('All Done!'))
