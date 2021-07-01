from django.core.management.base import BaseCommand, CommandError

from geojson import Feature, Point, FeatureCollection, dump

from plants.models import Collection
from plants.serializers import CollectionSerializer

class Command(BaseCommand):
    help = 'Generates geojson file of Collection objects'

    def handle(self, *args, **options):
        try:
            collections = Collection.objects.all()

            features = []
            for collection in collections:
                serialized_collection = CollectionSerializer(collection)
                feature = Feature(geometry=Point((collection.location.longitude,
                                                  collection.location.latitude)),
                                  properties=serialized_collection.data)
                features.append(feature)

            feature_collection = FeatureCollection(features)

            with open('collections.geojson', 'w') as f:
                dump(feature_collection, f)
        except Exception as e:
            raise CommandError(f'Broken: {e}')

