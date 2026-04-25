from html import escape

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

    def assertFrontendSpeciesLink(self, linked_html, species, link_text):
        species_url = reverse("plants:species-detail", args=[species.pk])
        preview_url = reverse("plants:species-preview", args=[species.pk])
        self.assertIn(f'href="{species_url}"', linked_html)
        self.assertIn('class="species-preview-link"', linked_html)
        self.assertIn(f'data-species-preview-url="{preview_url}"', linked_html)
        self.assertIn(link_text, linked_html)

    def test_link_html_wraps_species_mentions(self):
        linker = SpeciesAutoLinker.from_database()

        linked_html = linker.link_html("<p>Acer rubrum is planted near the pond.</p>")

        self.assertFrontendSpeciesLink(linked_html, self.species, "Acer rubrum</a>")

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

    def test_link_html_leaves_existing_partial_species_anchor_alone(self):
        family = get_family(name="Rosaceae")
        genus = get_genus(family, name="Prunus")
        base_species = get_species(
            genus,
            name="maackii",
            full_name="Prunus maackii",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar=None,
            vernacular_name="Amur Cherry",
        )
        cultivar = get_species(
            genus,
            name="maackii",
            full_name="Prunus maackii",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar="Jefree",
            vernacular_name="Goldrush Amur Cherry",
        )
        linker = SpeciesAutoLinker.from_database()
        base_url = reverse("plants:species-detail", args=[base_species.pk])

        linked_html = linker.link_html(
            f'<p><a href="{base_url}">Prunus maackii</a> &#x27;Jefree&#x27;</p>'
        )

        self.assertIn(f'<a href="{base_url}">Prunus maackii</a>', linked_html)
        self.assertNotIn(reverse("plants:species-detail", args=[cultivar.pk]), linked_html)

    def test_link_html_wraps_italic_species_name_with_valid_nesting(self):
        linker = SpeciesAutoLinker.from_database()

        linked_html = linker.link_html("<p><i>Acer rubrum</i> is planted nearby.</p>")

        self.assertIn(
            f'<a href="{reverse("plants:species-detail", args=[self.species.pk])}" '
            f'class="species-preview-link" '
            f'data-species-preview-url="{reverse("plants:species-preview", args=[self.species.pk])}">'
            "<i>Acer rubrum</i></a>",
            linked_html,
        )

    def test_link_html_uses_aliases(self):
        self.species.autolink_aliases = "red maple"
        self.species.save(update_fields=["autolink_aliases"])

        linker = SpeciesAutoLinker.from_database()
        linked_html = linker.link_html("<p>The red maple is turning color.</p>")

        self.assertFrontendSpeciesLink(linked_html, self.species, "red maple</a>")

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

    def test_get_unique_match_targets_loads_autolink_fields_in_one_query(self):
        self.species.subspecies = "drummondii"
        self.species.variety = "trilobum"
        self.species.subvariety = "example"
        self.species.forma = "rubrum"
        self.species.subforma = "minor"
        self.species.cultivar = "October Glory"
        self.species.save(
            update_fields=[
                "subspecies",
                "variety",
                "subvariety",
                "forma",
                "subforma",
                "cultivar",
            ]
        )

        with self.assertNumQueries(1):
            SpeciesAutoLinker.get_unique_match_targets_from_database()

    def test_from_database_reuses_cached_autolinker_until_species_changes(self):
        SpeciesAutoLinker.clear_cached_autolinkers()

        with self.assertNumQueries(1):
            first_linker = SpeciesAutoLinker.from_database()

        with self.assertNumQueries(0):
            second_linker = SpeciesAutoLinker.from_database()

        self.assertIs(first_linker, second_linker)

        self.species.autolink_aliases = "scarlet maple"
        self.species.save(update_fields=["autolink_aliases"])

        with self.assertNumQueries(1):
            refreshed_linker = SpeciesAutoLinker.from_database()

        self.assertIsNot(first_linker, refreshed_linker)

    def test_link_html_prefers_more_specific_taxon_names(self):
        cases = [
            {
                "label": "subspecies",
                "family": "Hydrangeaceae",
                "genus": "Hydrangea",
                "name": "anomala",
                "field": "subspecies",
                "value": "petiolaris",
                "term": "Hydrangea anomala subsp. petiolaris",
            },
            {
                "label": "variety",
                "family": "Rosaceae",
                "genus": "Crataegus",
                "name": "crus-galli",
                "field": "variety",
                "value": "inermis",
                "term": "Crataegus crus-galli var. inermis",
            },
            {
                "label": "subvariety",
                "family": "Sapindaceae",
                "genus": "Acer",
                "name": "glabrum",
                "field": "subvariety",
                "value": "diffusum",
                "term": "Acer glabrum subvar. diffusum",
            },
            {
                "label": "forma",
                "family": "Rosaceae",
                "genus": "Rosa",
                "name": "sericea",
                "field": "forma",
                "value": "pteracantha",
                "term": "Rosa sericea f. pteracantha",
            },
            {
                "label": "subforma",
                "family": "Pinaceae",
                "genus": "Picea",
                "name": "pungens",
                "field": "subforma",
                "value": "glauca",
                "term": "Picea pungens subf. glauca",
            },
            {
                "label": "cultivar",
                "family": "Rosaceae",
                "genus": "Prunus",
                "name": "maackii",
                "field": "cultivar",
                "value": "Jefree",
                "term": "Prunus maackii 'Jefree'",
            },
        ]

        for case in cases:
            with self.subTest(case["label"]):
                family = get_family(name=case["family"])
                genus = get_genus(family, name=case["genus"])
                base_name = f"{case['genus']} {case['name']}"
                common_kwargs = {
                    "subspecies": None,
                    "variety": None,
                    "subvariety": None,
                    "forma": None,
                    "subforma": None,
                    "cultivar": None,
                }
                get_species(
                    genus,
                    name=case["name"],
                    full_name=base_name,
                    vernacular_name=f"{case['label']} base",
                    **common_kwargs,
                )
                specific_kwargs = common_kwargs | {case["field"]: case["value"]}
                specific_taxon = get_species(
                    genus,
                    name=case["name"],
                    full_name=base_name,
                    vernacular_name=f"{case['label']} specific",
                    **specific_kwargs,
                )

                linker = SpeciesAutoLinker.from_database()
                linked_html = linker.link_html(f"<p>{case['term']} grows here.</p>")

                self.assertFrontendSpeciesLink(
                    linked_html,
                    specific_taxon,
                    f"{escape(case['term'])}</a>",
                )

    def test_link_html_supports_cross_symbol_variants(self):
        family = get_family(name="Orchidaceae")
        genus = get_genus(family, name="Cypripedium")
        cross = get_species(
            genus,
            name="",
            full_name="Cypripedium × 'Sabine'",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar="Sabine",
            vernacular_name="Sabine lady's slipper",
        )

        linker = SpeciesAutoLinker.from_database()
        linked_html = linker.link_html("<p>Cypripedium x 'Sabine' flowers here.</p>")

        self.assertFrontendSpeciesLink(
            linked_html,
            cross,
            "Cypripedium x &#x27;Sabine&#x27;</a>",
        )

    def test_link_html_detects_specific_taxon_across_inline_formatting(self):
        family = get_family(name="Rosaceae")
        genus = get_genus(family, name="Prunus")
        base_species = get_species(
            genus,
            name="maackii",
            full_name="Prunus maackii",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar=None,
            vernacular_name="Amur Cherry",
        )
        cultivar = get_species(
            genus,
            name="maackii",
            full_name="Prunus maackii",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar="Jefree",
            vernacular_name="Goldrush Amur Cherry",
        )

        linker = SpeciesAutoLinker.from_database()
        linked_html = linker.link_html(
            "<p><b>Goldrush</b> <b>Amur Cherry (</b>"
            "<b><i>Prunus maackii</i></b> <b>&#x27;Jefree&#x27;)</b></p>"
        )

        self.assertIn(
            f'<a href="{reverse("plants:species-detail", args=[cultivar.pk])}" '
            f'class="species-preview-link" '
            f'data-species-preview-url="{reverse("plants:species-preview", args=[cultivar.pk])}">'
            "<i>Prunus maackii</i> &#x27;Jefree&#x27;</a>",
            linked_html,
        )
        self.assertEqual(
            linked_html.count(
                f'href="{reverse("plants:species-detail", args=[cultivar.pk])}"'
            ),
            1,
        )
        self.assertNotIn(reverse("plants:species-detail", args=[base_species.pk]), linked_html)
