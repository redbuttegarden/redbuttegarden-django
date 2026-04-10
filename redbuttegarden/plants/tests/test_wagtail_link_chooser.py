import json

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from wagtail.admin.rich_text.converters.contentstate import ContentstateConverter
from wagtail.admin.rich_text.converters.editor_html import EditorHTMLConverter
from wagtail.test.utils import get_user_model

from plants.tests.utils import get_collection, get_family, get_genus, get_species


class TestWagtailRichTextLinkChoosers(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "Test User", "test@email.com", "password"
        )
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        family = get_family(name="Rosaceae")
        genus = get_genus(family, name="Rosa")
        self.species = get_species(
            genus,
            name="woodsii",
            full_name="Rosa woodsii",
            vernacular_name="Woods' rose",
        )
        self.collection = get_collection(
            family_name=family.name,
            genus_name=genus.name,
            species_name=self.species.name,
            full_name=self.species.full_name,
            vernacular_name=self.species.vernacular_name,
            plant_id="RG-42",
        )

    def test_internal_link_modal_lists_species_and_collection_tabs(self):
        response = self.client.get(
            reverse("wagtailadmin_choose_page"),
            {
                "allow_external_link": 1,
                "allow_email_link": 1,
                "allow_phone_link": 1,
                "allow_anchor_link": 1,
            },
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        payload = json.loads(response.content)

        self.assertIn("Species links", payload["html"])
        self.assertIn("Plant Collection Links", payload["html"])
        self.assertIn(reverse("species_link_chooser:choose"), payload["html"])
        self.assertIn(reverse("collection_link_chooser:choose"), payload["html"])

    def test_species_link_chooser_can_search_species(self):
        response = self.client.get(
            reverse("species_link_chooser:choose"),
            {"q": "woodsii", "allow_external_link": 1},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        payload = json.loads(response.content)

        self.assertEqual(payload["step"], "species_link_choose")
        self.assertIn("Species links", payload["html"])
        self.assertIn(self.species.full_name, payload["html"])

    def test_collection_link_chooser_returns_custom_modal_step(self):
        response = self.client.get(
            reverse("collection_link_chooser:choose"),
            {"q": self.collection.plant_id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        payload = json.loads(response.content)

        self.assertEqual(payload["step"], "collection_link_choose")
        self.assertIn("Plant Collection Links", payload["html"])
        self.assertIn(self.collection.plant_id, payload["html"])

    def test_collection_link_results_returns_html_fragment(self):
        response = self.client.get(
            reverse("collection_link_chooser:choose_results"),
            {"q": self.collection.plant_id},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.collection.plant_id)
        self.assertNotIn('"step": "collection_link_choose"', response.content.decode())

    def test_species_link_chosen_returns_species_detail_url(self):
        response = self.client.get(
            reverse("species_link_chooser:chosen", args=[self.species.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        payload = json.loads(response.content)

        self.assertEqual(payload["step"], "page_chosen")
        self.assertEqual(payload["result"]["id"], self.species.pk)
        self.assertIsNone(payload["result"]["parentId"])
        self.assertEqual(payload["result"]["linkType"], "species")
        self.assertEqual(payload["result"]["url"], self.species.get_absolute_url())
        self.assertEqual(
            payload["result"]["title"], self.species.get_rich_text_link_title()
        )

    def test_collection_link_chosen_returns_collection_detail_url(self):
        response = self.client.get(
            reverse("collection_link_chooser:chosen", args=[self.collection.pk]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        payload = json.loads(response.content)

        self.assertEqual(payload["step"], "page_chosen")
        self.assertEqual(payload["result"]["id"], self.collection.pk)
        self.assertIsNone(payload["result"]["parentId"])
        self.assertEqual(payload["result"]["linkType"], "collection")
        self.assertEqual(payload["result"]["url"], self.collection.get_absolute_url())
        self.assertEqual(
            payload["result"]["title"], self.collection.get_rich_text_link_title()
        )

    def test_species_link_chooser_non_ajax_renders_html_page(self):
        response = self.client.get(reverse("species_link_chooser:choose"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Choose a species link")
        self.assertContains(response, "Species links")

    def test_species_db_link_is_exposed_to_editor_as_species_link(self):
        db_html = f'<p><a linktype="species" id="{self.species.pk}">Rosa woodsii</a></p>'
        editor_html = EditorHTMLConverter(features=["link", "plant-links"]).from_database_format(db_html)
        contentstate = json.loads(
            ContentstateConverter(features=["link", "plant-links"]).from_database_format(db_html)
        )

        self.assertIn('data-linktype="species"', editor_html)
        self.assertIn(f'data-id="{self.species.pk}"', editor_html)
        entity_data = next(iter(contentstate["entityMap"].values()))["data"]
        self.assertEqual(entity_data["linkType"], "species")
        self.assertEqual(entity_data["id"], self.species.pk)
        self.assertIsNone(entity_data["parentId"])

    def test_collection_db_link_is_exposed_to_editor_as_collection_link(self):
        db_html = (
            f'<p><a linktype="collection" id="{self.collection.pk}">'
            f"{self.collection.get_rich_text_link_title()}</a></p>"
        )
        editor_html = EditorHTMLConverter(features=["link", "plant-links"]).from_database_format(db_html)
        contentstate = json.loads(
            ContentstateConverter(features=["link", "plant-links"]).from_database_format(db_html)
        )

        self.assertIn('data-linktype="collection"', editor_html)
        self.assertIn(f'data-id="{self.collection.pk}"', editor_html)
        entity_data = next(iter(contentstate["entityMap"].values()))["data"]
        self.assertEqual(entity_data["linkType"], "collection")
        self.assertEqual(entity_data["id"], self.collection.pk)
        self.assertIsNone(entity_data["parentId"])
