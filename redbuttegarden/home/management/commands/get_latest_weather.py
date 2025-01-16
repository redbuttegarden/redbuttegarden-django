import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from home.models import CurrentWeather


# TODO: Schedule this command to run every 15 minutes in zappa_settings.json
class Command(BaseCommand):
    help = 'Get latest weather and save it to the database'

    def handle(self, *args, **options):
        api_key = settings.OPENWEATHER_API_KEY

        response = requests.get(
            f'http://api.openweathermap.org/data/2.5/weather?lat=40.766643&lon=-111.8257078&appid={api_key}&units=imperial')

        if response.status_code == 200:
            data = response.json()

            weather = CurrentWeather(condition=data['weather'][0]['main'],
                                     temperature=data['main']['temp'])
            weather.save()

        else:
            raise CommandError('Failed to get the latest weather')
