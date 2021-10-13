from django.db import IntegrityError
from django.test import TestCase

from plants.models import Species
from plants.tests.utils import get_family, get_genus, get_species


class SpeciesModelTestCase(TestCase):
    def setUp(self) -> None:
        self.family = get_family()
        self.genus = get_genus(self.family)
        self.species = get_species(self.genus)

    def test_create_species_with_only_name(self):
        Species.objects.create(genus=self.genus, name='species_name', vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(name='species_name').exists())

    def test_create_species_with_only_cultivar(self):
        Species.objects.create(genus=self.genus, cultivar='cultivar_name', vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(cultivar='cultivar_name').exists())

    def test_create_species_with_only_vernacular_name(self):
        Species.objects.create(genus=self.genus, vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(vernacular_name='vernacular_name').exists())

    def test_cannot_create_species_without_any_names(self):
        self.assertRaises(IntegrityError, Species.objects.create, genus=self.genus)

    def test_species_string_representation_name_without_cultivar(self):
        self.assertEqual(str(self.species), 'genus species')

    def test_species_string_representation_name_with_cultivar(self):
        other_species = Species.objects.create(genus=self.genus, name='other_species', cultivar='cultivar',
                                               vernacular_name='vernacular_name')
        self.assertEqual(str(other_species), "genus other_species 'cultivar'")

    def test_species_string_representation_without_name_with_cultivar(self):
        other_species = Species.objects.create(genus=self.genus, cultivar='cultivar', vernacular_name='vernacular_name')
        self.assertEqual(str(other_species), "genus 'cultivar'")

    def test_species_string_representation_without_name_without_cultivar(self):
        other_species = Species.objects.create(genus=self.genus, vernacular_name='vernacular_name')
        self.assertEqual(str(other_species), "genus vernacular_name")
