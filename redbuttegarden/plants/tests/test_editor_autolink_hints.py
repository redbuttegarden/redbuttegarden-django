from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse
from wagtail.test.utils import get_user_model

from plants.tests.utils import get_family, get_genus, get_species


class TestEditorAutolinkHints(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            "Test User", "test@email.com", "password"
        )
        self.user.groups.add(Group.objects.get(name="Moderators"))
        self.client.force_login(self.user)

    def test_species_autolink_terms_endpoint_returns_unique_terms_only(self):
        family = get_family(name="Rosaceae")
        genus = get_genus(family, name="Amelanchier")
        primary_species = get_species(
            genus,
            name="utahensis",
            full_name="Amelanchier utahensis",
            vernacular_name="Utah serviceberry",
        )
        primary_species.autolink_aliases = "Serviceberry"
        primary_species.save(update_fields=["autolink_aliases"])

        duplicate_species = get_species(
            genus,
            name="alnifolia",
            full_name="Amelanchier alnifolia",
            vernacular_name="Saskatoon serviceberry",
        )
        duplicate_species.autolink_aliases = "Serviceberry"
        duplicate_species.save(update_fields=["autolink_aliases"])

        response = self.client.get(
            reverse("species_autolink_terms"),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        payload = response.json()

        self.assertIn("Amelanchier utahensis", payload["terms"])
        self.assertIn("Amelanchier alnifolia", payload["terms"])
        self.assertNotIn("Serviceberry", payload["terms"])
