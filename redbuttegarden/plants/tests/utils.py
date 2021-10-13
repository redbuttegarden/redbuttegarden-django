import pytest
from django.contrib.auth import get_user_model

from plants.models import Family, Genus, Species


def get_custom_user(username='username', password='password'):
    return get_user_model().objects.create_user(username=username, password=password)

@pytest.fixture
def family():
    return Family.objects.create(name='Family')

def get_family():
    return Family.objects.create(name='Family')

@pytest.fixture
def genus(family):
    return Genus.objects.create(family=family, name='genus')

def get_genus(family):
    return Genus.objects.create(family=family, name='genus')

@pytest.fixture
def species(genus):
    return Species.objects.create(genus=genus, name='species', vernacular_name='vernacular_name')

def get_species(genus):
    return Species.objects.create(genus=genus, name='species', vernacular_name='vernacular_name')
