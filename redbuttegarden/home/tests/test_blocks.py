import json

from django.contrib.auth.models import Group
from wagtail.models import Page
from wagtail.images.tests.utils import get_image_model, get_test_image_file
from wagtail.test.utils import WagtailPageTests, get_user_model

from events.models import SingleListImage
from home.models import (
    AlignedParagraphBlock,
    ColumnBlock,
    GeneralPage,
    ImageInfo,
    MultiColumnAlignedParagraphBlock,
    RetailPartnerBlock,
    RetailPartnerPage,
    SingleListButtonDropdownInfo,
    SingleListCardDropdownInfo,
    SingleListImageCardInfo,
    SingleThreeColumnDropdownInfoPanel,
)
from plants.tests.utils import get_family, get_genus, get_species


class TestMultiColumnAlignedParagraphBlock(WagtailPageTests):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "Test User", "test@email.com", "password"
        )
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def assert_multi_column_paragraphs_rendered(self, html, paragraphs):
        self.assertIn(
            f'<div class="row row-cols-1 row-cols-sm-2 row-cols-md-{len(paragraphs)} left">',
            html,
        )
        self.assertEqual(
            html.count('<div class="col py-1 py-md-3 px-3">'),
            len(paragraphs),
        )
        for paragraph in paragraphs:
            self.assertIn(f"<p>{paragraph}</p>", html)

    def test_view_one_paragraph(self):
        general_page = GeneralPage(
            owner=self.user,
            slug="general-test-page",
            title="General Test Page",
            body=json.dumps(
                [
                    {
                        "type": "multi_column_paragraph",
                        "value": {
                            "alignment": "left",
                            "background_color": "default",
                            "paragraph": ["<p>Testing!</p>"],
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get("/general-test-page", follow=True)
        html = response.content.decode("utf8")
        self.assert_multi_column_paragraphs_rendered(html, ["Testing!"])

    def test_view_two_paragraphs(self):
        general_page = GeneralPage(
            owner=self.user,
            slug="general-test-page",
            title="General Test Page",
            body=json.dumps(
                [
                    {
                        "type": "multi_column_paragraph",
                        "value": {
                            "alignment": "left",
                            "background_color": "default",
                            "paragraph": [
                                "<p>Testing!</p>",
                                "<p>Second Test Paragraph</p>",
                            ],
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get("/general-test-page", follow=True)
        html = response.content.decode("utf8")
        self.assert_multi_column_paragraphs_rendered(
            html, ["Testing!", "Second Test Paragraph"]
        )

    def test_view_three_paragraphs(self):
        general_page = GeneralPage(
            owner=self.user,
            slug="general-test-page",
            title="General Test Page",
            body=json.dumps(
                [
                    {
                        "type": "multi_column_paragraph",
                        "value": {
                            "alignment": "left",
                            "background_color": "default",
                            "paragraph": [
                                "<p>Testing!</p>",
                                "<p>Second Test Paragraph</p>",
                                "<p>Third Test Paragraph</p>",
                            ],
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get("/general-test-page", follow=True)
        html = response.content.decode("utf8")
        self.assert_multi_column_paragraphs_rendered(
            html, ["Testing!", "Second Test Paragraph", "Third Test Paragraph"]
        )

    def test_view_four_paragraphs(self):
        general_page = GeneralPage(
            owner=self.user,
            slug="general-test-page",
            title="General Test Page",
            body=json.dumps(
                [
                    {
                        "type": "multi_column_paragraph",
                        "value": {
                            "alignment": "left",
                            "background_color": "default",
                            "paragraph": [
                                "<p>Testing!</p>",
                                "<p>Second Test Paragraph</p>",
                                "<p>Third Test Paragraph</p>",
                                "<p>Fourth Test Paragraph</p>",
                            ],
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get("/general-test-page", follow=True)
        html = response.content.decode("utf8")
        self.assert_multi_column_paragraphs_rendered(
            html,
            [
                "Testing!",
                "Second Test Paragraph",
                "Third Test Paragraph",
                "Fourth Test Paragraph",
            ],
        )

    def test_view_five_paragraphs(self):
        general_page = GeneralPage(
            owner=self.user,
            slug="general-test-page",
            title="General Test Page",
            body=json.dumps(
                [
                    {
                        "type": "multi_column_paragraph",
                        "value": {
                            "alignment": "left",
                            "background_color": "default",
                            "paragraph": [
                                "<p>Testing!</p>",
                                "<p>Second Test Paragraph</p>",
                                "<p>Third Test Paragraph</p>",
                                "<p>Fourth Test Paragraph</p>",
                                "<p>Fifth Test Paragraph</p>",
                            ],
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get("/general-test-page", follow=True)
        html = response.content.decode("utf8")
        self.assert_multi_column_paragraphs_rendered(
            html,
            [
                "Testing!",
                "Second Test Paragraph",
                "Third Test Paragraph",
                "Fourth Test Paragraph",
                "Fifth Test Paragraph",
            ],
        )

    def test_species_mentions_are_linked_in_multi_column_paragraphs(self):
        family = get_family(name="Sapindaceae")
        genus = get_genus(family, name="Acer")
        species = get_species(
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

        general_page = GeneralPage(
            owner=self.user,
            slug="species-link-test-page",
            title="Species Link Test Page",
            body=json.dumps(
                [
                    {
                        "type": "multi_column_paragraph",
                        "value": {
                            "alignment": "left",
                            "background_color": "default",
                            "paragraph": ["<p>Acer rubrum is planted near the pond.</p>"],
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=general_page)
        general_page.save_revision().publish()

        response = self.client.get("/species-link-test-page", follow=True)
        html = response.content.decode("utf8")

        self.assertIn(
            f'<a href="/plants/species/{species.pk}/">Acer rubrum</a>',
            html,
        )


class TestSpeciesAutolinkBlockCleaning(WagtailPageTests):
    def create_species(self, family_name, genus_name, name, full_name, vernacular_name):
        family = get_family(name=family_name)
        genus = get_genus(family, name=genus_name)
        return get_species(
            genus,
            name=name,
            full_name=full_name,
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar=None,
            vernacular_name=vernacular_name,
        )

    def test_aligned_paragraph_block_saves_species_link(self):
        species = self.create_species(
            family_name="Rosaceae",
            genus_name="Amelanchier",
            name="utahensis",
            full_name="Amelanchier utahensis",
            vernacular_name="Utah Serviceberry",
        )

        block = AlignedParagraphBlock()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "alignment": "left",
                    "background_color": "default",
                    "paragraph": "<p>Amelanchier utahensis is blooming.</p>",
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Amelanchier utahensis</a>',
            cleaned_value["paragraph"].source,
        )

    def test_multi_column_block_saves_species_links(self):
        species = self.create_species(
            family_name="Cupressaceae",
            genus_name="Juniperus",
            name="scopulorum",
            full_name="Juniperus scopulorum",
            vernacular_name="Rocky Mountain Juniper",
        )

        block = MultiColumnAlignedParagraphBlock()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "alignment": "left",
                    "background_color": "default",
                    "title": "",
                    "paragraph": [
                        "<p>Juniperus scopulorum handles dry sites well.</p>",
                        "<p>No species match here.</p>",
                    ],
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Juniperus scopulorum</a>',
            cleaned_value["paragraph"][0].source,
        )
        self.assertEqual(cleaned_value["paragraph"][1].source, "<p>No species match here.</p>")

    def test_event_list_image_block_saves_species_link(self):
        family = get_family(name="Asparagaceae")
        genus = get_genus(family, name="Ophiopogon")
        species = get_species(
            genus,
            name="planiscapus",
            full_name="Ophiopogon planiscapus",
            subspecies=None,
            variety=None,
            subvariety=None,
            forma=None,
            subforma=None,
            cultivar="Nigrescens",
            vernacular_name="Black Mondo Grass",
        )
        image = get_image_model().objects.create(
            title="Test image", file=get_test_image_file()
        )

        block = SingleListImage()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "image": image.pk,
                    "title": "Black foliage",
                    "sub_title": "Groundcover",
                    "text": "<p>Ophiopogon planiscapus thrives in partial shade.</p>",
                    "link_url": "",
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Ophiopogon planiscapus</a>',
            cleaned_value["text"].source,
        )

    def test_image_info_block_saves_species_links(self):
        species = self.create_species(
            family_name="Asteraceae",
            genus_name="Helianthus",
            name="annuus",
            full_name="Helianthus annuus",
            vernacular_name="Common Sunflower",
        )
        image = get_image_model().objects.create(
            title="Test image", file=get_test_image_file()
        )

        block = ImageInfo()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "image": image.pk,
                    "title": "Sunflower",
                    "subtitle": "Annual",
                    "info_title": "Display bed",
                    "info_subtitle": "Pollinator favorite",
                    "tan_bg_info": "<p>Helianthus annuus thrives in full sun.</p>",
                    "tan_bg_button_text": "",
                    "tan_bg_button_url": "",
                    "additional_info": "<p>Helianthus annuus can reseed freely.</p>",
                }
            )
        )

        expected_link = (
            f'<a linktype="species" id="{species.pk}">Helianthus annuus</a>'
        )
        self.assertIn(expected_link, cleaned_value["tan_bg_info"].source)
        self.assertIn(expected_link, cleaned_value["additional_info"].source)

    def test_image_card_block_saves_species_link(self):
        species = self.create_species(
            family_name="Fagaceae",
            genus_name="Quercus",
            name="gambelii",
            full_name="Quercus gambelii",
            vernacular_name="Gambel Oak",
        )

        block = SingleListImageCardInfo()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "image": None,
                    "text": "<p>Quercus gambelii provides wildlife habitat.</p>",
                    "button_text": "",
                    "button_url": "",
                    "force_full_width": False,
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Quercus gambelii</a>',
            cleaned_value["text"].source,
        )

    def test_button_dropdown_block_saves_species_link(self):
        species = self.create_species(
            family_name="Caprifoliaceae",
            genus_name="Sambucus",
            name="nigra",
            full_name="Sambucus nigra",
            vernacular_name="Black Elderberry",
        )

        block = SingleListButtonDropdownInfo()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "button_text": "Learn more",
                    "info_text": "<p>Sambucus nigra has edible cooked fruit.</p>",
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Sambucus nigra</a>',
            cleaned_value["info_text"].source,
        )

    def test_card_dropdown_block_saves_species_link(self):
        species = self.create_species(
            family_name="Rosaceae",
            genus_name="Prunus",
            name="virginiana",
            full_name="Prunus virginiana",
            vernacular_name="Chokecherry",
        )

        block = SingleListCardDropdownInfo()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "card_info": {
                        "alignment": "left",
                        "background_color": "default",
                        "paragraph": "<p>Card copy.</p>",
                    },
                    "info_text": "<p>Prunus virginiana supports pollinators.</p>",
                    "info_button_text": "",
                    "info_button_url": "",
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Prunus virginiana</a>',
            cleaned_value["info_text"].source,
        )

    def test_three_column_panel_saves_species_links(self):
        species = self.create_species(
            family_name="Pinaceae",
            genus_name="Pseudotsuga",
            name="menziesii",
            full_name="Pseudotsuga menziesii",
            vernacular_name="Douglas-fir",
        )

        block = SingleThreeColumnDropdownInfoPanel()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "background_color": "default-panel",
                    "col_one_header": "<p>Pseudotsuga menziesii</p>",
                    "col_two_header": "<p>Schedule</p>",
                    "col_three_header": "<p>Location</p>",
                    "class_info_subheaders": True,
                    "col_one_top_info": "<p>Native conifer.</p>",
                    "col_two_top_info": "<p>Open daily.</p>",
                    "col_three_top_info": "<p>Wasatch Range.</p>",
                    "middle_info": {
                        "alignment": "left",
                        "background_color": "default",
                        "paragraph": "<p>Middle panel text.</p>",
                    },
                    "button": {
                        "text": "Learn more",
                        "url": "https://example.com",
                        "color": "green",
                        "alignment": "center",
                        "embiggen": False,
                    },
                    "col_one_bottom_info": "<p>Pseudotsuga menziesii prefers mountain climates.</p>",
                    "col_two_bottom_info": "<p>Free.</p>",
                    "col_three_bottom_info": "<p>Visitor center.</p>",
                }
            )
        )

        expected_link = (
            f'<a linktype="species" id="{species.pk}">Pseudotsuga menziesii</a>'
        )
        self.assertIn(expected_link, cleaned_value["col_one_header"].source)
        self.assertIn(expected_link, cleaned_value["col_one_bottom_info"].source)

    def test_column_block_saves_species_link(self):
        species = self.create_species(
            family_name="Betulaceae",
            genus_name="Betula",
            name="occidentalis",
            full_name="Betula occidentalis",
            vernacular_name="Water Birch",
        )

        block = ColumnBlock()
        cleaned_value = block.clean(
            block.to_python(
                [
                    {
                        "type": "paragraph",
                        "value": "<p>Betula occidentalis grows along streams.</p>",
                    }
                ]
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Betula occidentalis</a>',
            cleaned_value[0].value.source,
        )

    def test_retail_partner_block_saves_species_link(self):
        species = self.create_species(
            family_name="Sapindaceae",
            genus_name="Acer",
            name="grandidentatum",
            full_name="Acer grandidentatum",
            vernacular_name="Bigtooth Maple",
        )

        block = RetailPartnerBlock()
        cleaned_value = block.clean(
            block.to_python(
                {
                    "name": "Native Plants Nursery",
                    "addresses": [],
                    "url": "",
                    "info": "<p>Acer grandidentatum is available seasonally.</p>",
                }
            )
        )

        self.assertIn(
            f'<a linktype="species" id="{species.pk}">Acer grandidentatum</a>',
            cleaned_value["info"].source,
        )


class TestRetailPartnerBlock(WagtailPageTests):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "Test User", "test@email.com", "password"
        )
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

        self.image = get_image_model().objects.create(
            title="Test image", file=get_test_image_file()
        )

    def test_retail_partner_without_address(self):
        retail_partner_page = RetailPartnerPage(
            owner=self.user,
            title="Retail Partner Test Page",
            banner=self.image,
            body=json.dumps([{"type": "green_heading", "value": "Testing!"}]),
            retail_partners=json.dumps(
                [
                    {
                        "type": "retail_partner",
                        "value": {
                            "name": "Test Partner",
                            "url": "https://example.com",
                            "info": "<p>Testing!</p>",
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=retail_partner_page)
        retail_partner_page.save_revision().publish()
        response = self.client.get("/retail-partner-test-page", follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf8")
        self.assertIn('<h3 class="green">Test Partner</h3>', html)

    def test_retail_partner_with_one_address(self):
        retail_partner_page = RetailPartnerPage(
            owner=self.user,
            title="Retail Partner Test Page",
            banner=self.image,
            body=json.dumps([{"type": "green_heading", "value": "Testing!"}]),
            retail_partners=json.dumps(
                [
                    {
                        "type": "retail_partner",
                        "value": {
                            "name": "Test Partner",
                            "addresses": [
                                {
                                    "street_address": "123 Test Lane",
                                    "city": "Test City",
                                    "zipcode": 12345,
                                    "phone": "(123) 123-1234",
                                }
                            ],
                            "url": "https://example.com",
                            "info": "<p>Testing!</p>",
                        },
                    }
                ]
            ),
        )
        Page.objects.get(slug="home").add_child(instance=retail_partner_page)
        retail_partner_page.save_revision().publish()
        response = self.client.get("/retail-partner-test-page", follow=True)
        self.assertEqual(response.status_code, 200)
        html = response.content.decode("utf8")
        self.assertIn('<h3 class="green">Test Partner</h3>', html)
        self.assertIn(
            """<div class="fs-6 fw-bold mb-2">\n  123 Test Lane, Test City\n  , 12345\n  <a href="tel:(123) 123-1234">(123) 123-1234</a>\n</div>\n\n\n\n<p><a href="https://example.com">https://example.com</a></p>\n\n<p>Testing!</p>""",
            html,
        )
