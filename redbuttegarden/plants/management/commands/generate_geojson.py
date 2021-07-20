from django.core.management.base import BaseCommand, CommandError

from geojson import Feature, Point, FeatureCollection, dump

from plants.models import Collection

class Command(BaseCommand):
    help = 'Generates geojson file of Collection objects'

    def handle(self, *args, **options):
        try:
            collections = Collection.objects.all()

            features = []
            for collection in collections:
                feature = Feature(geometry=Point((collection.location.longitude,
                                                  collection.location.latitude)),
                                  properties={
                                      'id': collection.id,
                                      'family_name': collection.species.genus.family.name,
                                      'genus_name': collection.species.genus.name,
                                      'species_name': collection.species.name,
                                      'cultivar': collection.species.cultivar,
                                      'vernacular_name': collection.species.vernacular_name,
                                      'habit': collection.species.habit,
                                      'hardiness': collection.species.hardiness,
                                      'water_regime': collection.species.water_regime,
                                      'exposure': collection.species.exposure,
                                      'boom_time': collection.species.bloom_time,
                                      'plant_size': collection.species.plant_size,
                                      'planted_on': collection.plant_date.strftime('%m/%d/%Y')
                                        if collection.plant_date else None,
                                  })
                features.append(feature)

            feature_collection = FeatureCollection(features)

            with open('collections.geojson', 'w') as f:
                dump(feature_collection, f)
        except Exception as e:
            raise CommandError(f'Broken: {e}')

