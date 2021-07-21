import logging

from django.templatetags.static import static
from geojson import FeatureCollection, Feature, Point

logger = logging.getLogger(__name__)

MAP_ICONS = {
    'Annual': static('img/annual_icon.png'),
    'Bulb': static('img/bulb_icon.png'),
    'Deciduous Shrub': static('img/deciduous_shrub_icon.png'),
    'Deciduous Tree': static('img/deciduous_tree_icon.png'),
    'Deciduous Vine': static('img/deciduous_vine_icon.png'),
    'Evergreen Groundcover': static('img/evergreen_groundcover_icon.png'),
    'Evergreen Shrub': static('img/evergreen_shrub_icon.png'),
    'Evergreen Tree': static('img/evergreen_tree_icon.png'),
    'Evergreen Vine': static('img/evergreen_vine_icon.png'),
    'Grass': static('img/grass_icon.png'),
    'Perennial': static('img/perennial_icon.png'),
    'Succulent': static('img/succulent_icon.png'),
    'Tree': static('img/tree_icon.png')
}

def get_feature_collection(collections):
    features = []
    for collection in collections:
        try:
            icon = MAP_ICONS[collection.species.habit]
        except KeyError:
            logger.error(f'Habit {collection.species.habit} not mapped to an icon file')
            icon = None

        if collection.plant_date:
            plant_date = collection.plant_date.strftime('%m/%d/%Y')
        else:
            plant_date = None

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
                              'planted_on': plant_date,
                              'icon': icon
                              if collection.plant_date else None,
                          })
        features.append(feature)

    return FeatureCollection(features)
