from django.core.management.base import BaseCommand, CommandError

from geojson import dump

from plants.selectors import public_collections
from plants.utils import get_feature_collection


class Command(BaseCommand):
    help = 'Generates geojson file of Collection objects'

    def handle(self, *args, **options):
        try:
            # Get all collections with Locations
            feature_collection = get_feature_collection(public_collections().exclude(location=None))

            with open('collections.geojson', 'w') as f:
                dump(feature_collection, f)
        except Exception as e:
            raise CommandError(f'Broken: {e}')

