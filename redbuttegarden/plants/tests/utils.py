import pytest
from django.contrib.auth import get_user_model

from plants.models import Collection, Family, GardenArea, Genus, Location, Species


def get_custom_user(username='username', password='password'):
    return get_user_model().objects.create_user(username=username, password=password)


def get_collection(latitude=40, longitude=-111,  # Location
                   area="Butterfly Walk", ga_name="Children's Garden", code="CG-06",  # GardenArea
                   family_name="family",  # Family
                   genus_name="genus",  # Genus
                   # Species
                   species_name="praecox", full_name="Cytisus × praecox 'Allgold'", subspecies=None,
                   variety=None, subvariety=None, forma=None, subforma=None, cultivar="Allgold",
                   vernacular_name="Allgold Warminster Broom", habit="Deciduous Shrub", hardiness=None,
                   water_regime="Low", exposure="Full Sun to Part Shade", bloom_time=None,
                   plant_size="5' h x 5' w", flower_color="Yellow", utah_native=False, plant_select=False,
                   deer_resist=True, rabbit_resist=True, bee_friend=False, high_elevation=False,
                   plant_date="2000-5-1", plant_id="2000-1024*1", commemoration_category=None,
                   commemoration_person=None):
    if hardiness is None:
        hardiness = [5, 6, 7, 8]
    if bloom_time is None:
        bloom_time = ["Mid April", "May", "Mid June"]

    location = get_location(latitude=latitude, longitude=longitude)
    garden = get_garden_area(area=area, name=ga_name, code=code)
    family = get_family(name=family_name)
    genus = get_genus(family, name=genus_name)
    species = get_species(genus, name=species_name, full_name=full_name, subspecies=subspecies,
                          variety=variety, subvariety=subvariety, forma=forma, subforma=subforma,
                          cultivar=cultivar, vernacular_name=vernacular_name, habit=habit,
                          hardiness=hardiness, water_regime=water_regime, exposure=exposure,
                          bloom_time=bloom_time, plant_size=plant_size, flower_color=flower_color,
                          utah_native=utah_native, plant_select=plant_select, deer_resist=deer_resist,
                          rabbit_resist=rabbit_resist, bee_friend=bee_friend,
                          high_elevation=high_elevation)

    return Collection.objects.create(location=location, garden=garden, species=species,
                                     plant_date=plant_date,
                                     plant_id=plant_id, commemoration_category=commemoration_category,
                                     commemoration_person=commemoration_person)


def get_garden_area(area="Butterfly Walk", name="Children's Garden", code="CG-06"):
    garden_area, _ = GardenArea.objects.get_or_create(area=area, name=name, code=code)
    return garden_area


def get_location(latitude=40, longitude=-111):
    location, _ = Location.objects.get_or_create(latitude=latitude, longitude=longitude)
    return location


@pytest.fixture
def family():
    family, _ = Family.objects.get_or_create(name='Family')
    return family


def get_family(name='Family'):
    family, _ = Family.objects.get_or_create(name=name)
    return family


@pytest.fixture
def genus(family):
    genus, _ = Genus.objects.get_or_create(family=family, name='Genus')
    return genus


def get_genus(family, name='Genus'):
    genus, _ = Genus.objects.get_or_create(family=family, name=name)
    return genus


@pytest.fixture
def species(genus):
    species, _ = Species.objects.get_or_create(genus=genus, name='species', full_name='Genus species',
                                               vernacular_name='vernacular_name')
    return species


def get_species(genus, name='species', full_name='Genus species', subspecies='subspecies',
                variety='variety', subvariety='subvariety', forma='forma', subforma='subforma',
                cultivar='cultivar', vernacular_name='vernacular_name', habit='habit',
                hardiness=None, water_regime='water regime', exposure='exposure',
                bloom_time=None, plant_size='1\' h x 2" w', flower_color='color',
                utah_native=True, plant_select=True, deer_resist=True, rabbit_resist=True,
                bee_friend=True, high_elevation=True, arborist_rec=True):
    if hardiness is None:
        hardiness = [1, 2, 3, 4]
    if bloom_time is None:
        bloom_time = ["Early January", "Mid February", "Late March"]

    species, _ = Species.objects.get_or_create(genus=genus, name=name, full_name=full_name, subspecies=subspecies,
                                               variety=variety, subvariety=subvariety, forma=forma,
                                               subforma=subforma, cultivar=cultivar,
                                               vernacular_name=vernacular_name, habit=habit, hardiness=hardiness,
                                               water_regime=water_regime, exposure=exposure, bloom_time=bloom_time,
                                               plant_size=plant_size, flower_color=flower_color,
                                               utah_native=utah_native, plant_select=plant_select,
                                               deer_resist=deer_resist, rabbit_resist=rabbit_resist,
                                               bee_friend=bee_friend, high_elevation=high_elevation,
                                               arborist_rec=arborist_rec)
    return species
