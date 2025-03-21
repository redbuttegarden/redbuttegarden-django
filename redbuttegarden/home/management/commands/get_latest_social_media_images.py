import logging
from io import BytesIO

import requests
from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from wagtail.images.models import Image
from wagtail.models import Collection as WagtailCollection

logger = logging.getLogger(__name__)


# TODO: Schedule this command to run every day in zappa_settings.json
class Command(BaseCommand):
    help = 'Get latest social media images and save them to the database'

    def handle(self, *args, **options):
        FACEBOOK_BASE_URL = "https://graph.facebook.com"
        FACEBOOK_API_VERSION = "v22.0"
        INSTAGRAM_APP_ID = settings.INSTAGRAM_APP_ID
        TIMEOUT = 5

        access_token = settings.FB_API_TOKEN

        url = f"{FACEBOOK_BASE_URL}/{FACEBOOK_API_VERSION}/{INSTAGRAM_APP_ID}/media"
        params = (("access_token", access_token),
                  ("fields", "id,media_type,media_url,permalink,thumbnail_url,timestamp,username,caption"),
                  ("limit", 10))
        response = requests.get(url, params, timeout=TIMEOUT)
        media_json = response.json()

        if response.status_code == 200:
            for media_item in media_json["data"]:
                media_id = media_item["id"]
                if "thumbnail_url" in media_item:
                    media_thumbnail_url = media_item["thumbnail_url"]
                else:
                    media_thumbnail_url = None
                media_url = media_item["media_url"]
                media_permalink = media_item["permalink"]
                media_timestamp = media_item["timestamp"]

                img_response = requests.get(media_thumbnail_url if media_thumbnail_url else media_url, stream=True,
                                            timeout=TIMEOUT)
                img_response.raw.decode_content = True
                if img_response.status_code == 200:
                    image_data = BytesIO(img_response.raw.read())
                    img_title = f'Instagram Image {media_id}'
                    try:
                        image, img_created = Image.objects.get_or_create(
                            title=img_title,
                            defaults={'file': ImageFile(image_data, name=img_title.strip() + '.jpg'),
                                      'collection': WagtailCollection.objects.get(name='Instagram Data'),
                                      'description': media_permalink,
                                      'created_at': media_timestamp
                                      })

                        if img_created:
                            image.tags.add('Instagram')

                    except WagtailCollection.DoesNotExist:
                        logger.error(
                            '"Instagram Data" Collection is missing. Unable to save new images.')
        else:
            raise CommandError('Failed response while retrieving latest media data')
