from django.db import IntegrityError
from django.test import TestCase

from plants.models import Species
from plants.tests.utils import get_family, get_genus, get_species


class SpeciesModelTestCase(TestCase):
    def setUp(self) -> None:
        self.family = get_family()
        self.genus = get_genus(self.family)
        self.species = get_species(
            self.genus,
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar=None,
        )

    def test_create_species_with_only_cultivar(self):
        Species.objects.create(genus=self.genus, cultivar='cultivar_name', full_name='Genus species',
                               vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(cultivar='cultivar_name').exists())

    def test_create_species_with_only_vernacular_name(self):
        Species.objects.create(genus=self.genus, full_name='Genus species', vernacular_name='vernacular_name')
        self.assertTrue(Species.objects.filter(vernacular_name='vernacular_name').exists())

    def test_cannot_create_species_without_any_names(self):
        self.assertRaises(IntegrityError, Species.objects.create, genus=self.genus)

    def test_get_autolink_terms_includes_full_name_and_aliases(self):
        self.species.autolink_aliases = "Red maple\n  Acer rubrum  \n"

        self.assertEqual(
            self.species.get_autolink_terms(),
            ["Genus species", "Red maple", "Acer rubrum"],
        )

    def test_get_autolink_terms_includes_generated_taxon_name(self):
        self.species.subspecies = "subspecies"
        self.species.variety = "variety"
        self.species.subvariety = "subvariety"
        self.species.forma = "forma"
        self.species.subforma = "subforma"
        self.species.cultivar = "Cultivar"

        self.assertIn(
            "Genus species subsp. subspecies var. variety subvar. subvariety "
            "f. forma subf. subforma 'Cultivar'",
            self.species.get_autolink_terms(),
        )

    def test_get_autolink_terms_does_not_duplicate_complete_full_name(self):
        self.species.full_name = "Genus species subsp. subspecies 'Cultivar'"
        self.species.subspecies = "subspecies"
        self.species.variety = None
        self.species.subvariety = None
        self.species.forma = None
        self.species.subforma = None
        self.species.cultivar = "Cultivar"

        self.assertEqual(
            self.species.get_autolink_terms(),
            ["Genus species subsp. subspecies 'Cultivar'"],
        )

    def test_get_autolink_terms_includes_cross_symbol_variants(self):
        self.species.full_name = "Cypripedium × 'Sabine'"
        self.species.cultivar = "Sabine"

        self.assertEqual(
            self.species.get_autolink_terms(),
            ["Cypripedium × 'Sabine'", "Cypripedium x 'Sabine'"],
        )
