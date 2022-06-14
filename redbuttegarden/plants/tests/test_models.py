from django.db import IntegrityError
from django.test import TestCase

from plants.models import Species
from plants.tests.utils import get_family, get_genus, get_species


class SpeciesModelTestCase(TestCase):
    def setUp(self) -> None:
        self.family = get_family()
        self.genus = get_genus(self.family)
        self.species = get_species(self.genus)

    def test_create_species_with_only_cultivar(self):
        Species.objects.create(genus=self.genus, cultivar='cultivar_name', full_name='Genus species',
                               vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(cultivar='cultivar_name').exists())

    def test_create_species_with_only_vernacular_name(self):
        Species.objects.create(genus=self.genus, full_name='Genus species', vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(vernacular_name='vernacular_name').exists())

    def test_cannot_create_species_without_any_names(self):
        self.assertRaises(IntegrityError, Species.objects.create, genus=self.genus)
