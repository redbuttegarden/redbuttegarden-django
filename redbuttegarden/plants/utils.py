import logging

from django.contrib.postgres.search import SearchVector
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.urls import reverse
from geojson import FeatureCollection, Feature, Point

from .models import Collection

logger = logging.getLogger(__name__)

MAP_ICONS = {
    'Annual': static('plants/img/annual_icon.png'),
    'Bulb': static('plants/img/bulb_icon.png'),
    'Deciduous Shrub': static('plants/img/deciduous_shrub_icon.png'),
    'Deciduous Tree': static('plants/img/deciduous_tree_icon.png'),
    'Deciduous Vine': static('plants/img/vine_icon.png'),
    'Evergreen Groundcover': static('plants/img/evergreen_groundcover_icon.png'),
    'Evergreen Shrub': static('plants/img/evergreen_shrub_icon.png'),
    'Evergreen Tree': static('plants/img/evergreen_tree_icon.png'),
    'Evergreen Vine': static('plants/img/vine_icon.png'),
    'Grass': static('plants/img/grass_icon.png'),
    'Perennial': static('plants/img/perennial_icon.png'),
    'Succulent': static('plants/img/succulent_icon.png'),
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
                              'species_id': collection.species.id,
                              'family_name': collection.species.genus.family.name,
                              'genus_name': collection.species.genus.name,
                              'species_name': collection.species.name,
                              'species_full_name': collection.species.full_name,
                              'vernacular_name': collection.species.vernacular_name,
                              'habit': collection.species.habit,
                              'hardiness': collection.species.hardiness,
                              'water_regime': collection.species.water_regime,
                              'exposure': collection.species.exposure,
                              'bloom_time': collection.species.bloom_time,
                              'plant_size': collection.species.plant_size,
                              'garden_area': collection.garden.area,
                              'garden_name': collection.garden.name,
                              'garden_code': collection.garden.code,
                              'planted_on': plant_date,
                              'icon': icon
                              if collection.plant_date else None,
                          })
        features.append(feature)

    return FeatureCollection(features)


def style_message(request, species, collection, original_message):
    if species:
        url = request.build_absolute_uri(reverse('plants:species-detail', args=[species.id]))
    elif collection:
        url = request.build_absolute_uri(reverse('plants:collection-detail', args=[collection.id]))
    else:
        logger.error('No species or collection provided')
        raise ValueError('No species or collection provided')

    return f"""The following feedback has been provided for this page: {url}
    
Be wary of the message contents since it's possible it could contain malicious content.

Message Contents:
    
    {original_message}"""


def filter_by_parameter(request, initial_queryset=None):
    if initial_queryset is None:
        collections = Collection.objects.all()
    else:
        collections = initial_queryset

    scientific_name = request.GET.get('scientific_name', None)
    common_name = request.GET.get('common_name', None)
    family = request.GET.get('family_name', None)
    garden_name = request.GET.get('garden_name', None)
    habit = request.GET.get('habits', None)
    exposure = request.GET.get('exposures', None)
    water_need = request.GET.get('water_needs', None)
    bloom_month = request.GET.get('bloom_months', None)
    flower_color = request.GET.get('flower_colors', None)
    memorial_person = request.GET.get('memorial_person', None)
    utah_native = request.GET.get('utah_native', None)
    plant_select = request.GET.get('plant_select', None)
    deer_resistant = request.GET.get('deer_resistant', None)
    rabbit_resistant = request.GET.get('rabbit_resistant', None)
    bee_friendly = request.GET.get('bee_friendly', None)
    high_elevation = request.GET.get('high_elevation', None)
    available_memorial = request.GET.get('available_memorial', None)

    try:
        if scientific_name:
            collections = collections.filter(species__full_name__icontains=scientific_name)
        if common_name:
            collections = collections.annotate(search=SearchVector('species__cultivar',
                                                                   'species__vernacular_name')).filter(search=common_name)
        if family:
            collections = collections.filter(species__genus__family_id=family)
        if garden_name:
            collections = collections.filter(garden__name=garden_name)
        if habit:
            collections = collections.filter(species__habit=habit)
        if exposure:
            collections = collections.filter(species__exposure=exposure)
        if water_need:
            collections = collections.filter(species__water_regime=water_need)
        if bloom_month:
            mods = ['Early', 'Mid', 'Late']
            month = [' '.join([mod, bloom_month]) for mod in mods]
            month.append(bloom_month)
            collections = collections.filter(species__bloom_time__overlap=month)
        if flower_color:
            collections = collections.filter(species__flower_color__icontains=flower_color)
        if memorial_person:
            collections = collections.filter(commemoration_person=memorial_person)
        if utah_native:
            collections = collections.filter(species__utah_native=utah_native)
        if plant_select:
            collections = collections.filter(species__plant_select=plant_select)
        if deer_resistant:
            collections = collections.filter(species__deer_resist=deer_resistant)
        if rabbit_resistant:
            collections = collections.filter(species__rabbit_resist=rabbit_resistant)
        if bee_friendly:
            collections = collections.filter(species__bee_friend=bee_friendly)
        if high_elevation:
            collections = collections.filter(species__high_elevation=high_elevation)
        if available_memorial:
            collections = collections.filter(commemoration_category='Available')
    except ValidationError as e:
        logger.error(f'ValidationError while parsing request: {request}\nError: {e}')
        raise

    return collections
