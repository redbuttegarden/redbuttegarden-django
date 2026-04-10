from django.test import TestCase
from django.urls import reverse

from plants.species_autolinks import SpeciesAutoLinker
from plants.tests.utils import get_family, get_genus, get_species


class SpeciesAutoLinkerTests(TestCase):
    def setUp(self):
        family = get_family(name="Sapindaceae")
        genus = get_genus(family, name="Acer")
        self.species = get_species(
            genus,
            name="rubrum",
            full_name="Acer rubrum",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar=None,
            vernacular_name="Red Maple",
        )

    def test_link_html_wraps_species_mentions(self):
        linker = SpeciesAutoLinker.from_database()

        linked_html = linker.link_html("<p>Acer rubrum is planted near the pond.</p>")

        self.assertIn(
            f'<a href="{reverse("plants:species-detail", args=[self.species.pk])}">Acer rubrum</a>',
            linked_html,
        )

    def test_rich_text_storage_linker_uses_species_linktype_markup(self):
        linker = SpeciesAutoLinker.for_rich_text_storage()

        linked_html = linker.link_html("<p>Acer rubrum is planted near the pond.</p>")

        self.assertIn(
            f'<a linktype="species" id="{self.species.pk}">Acer rubrum</a>',
            linked_html,
        )

    def test_link_html_skips_existing_anchor_tags(self):
        linker = SpeciesAutoLinker.from_database()
        species_url = reverse("plants:species-detail", args=[self.species.pk])

        linked_html = linker.link_html(
            f'<p><a href="{species_url}">Acer rubrum</a> is already linked.</p>'
        )

        self.assertEqual(linked_html.count('href="'), 1)

    def test_link_html_uses_aliases(self):
        self.species.autolink_aliases = "red maple"
        self.species.save(update_fields=["autolink_aliases"])

        linker = SpeciesAutoLinker.from_database()
        linked_html = linker.link_html("<p>The red maple is turning color.</p>")

        self.assertIn(
            f'<a href="{reverse("plants:species-detail", args=[self.species.pk])}">red maple</a>',
            linked_html,
        )

    def test_link_html_ignores_disabled_species(self):
        self.species.autolink_enabled = False
        self.species.save(update_fields=["autolink_enabled"])

        linker = SpeciesAutoLinker.from_database()
        linked_html = linker.link_html("<p>Acer rubrum is planted near the pond.</p>")

        self.assertNotIn("<a href=", linked_html)

    def test_link_html_skips_ambiguous_aliases(self):
        self.species.autolink_aliases = "maple"
        self.species.save(update_fields=["autolink_aliases"])

        second_species = get_species(
            self.species.genus,
            name="saccharum",
            full_name="Acer saccharum",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar=None,
            vernacular_name="Sugar Maple",
        )
        second_species.autolink_aliases = "maple"
        second_species.save(update_fields=["autolink_aliases"])

        linker = SpeciesAutoLinker.from_database()
        linked_html = linker.link_html("<p>The maple is leafing out.</p>")

        self.assertNotIn("<a href=", linked_html)
