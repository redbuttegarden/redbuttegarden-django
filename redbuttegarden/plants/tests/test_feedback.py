from http import HTTPStatus

from django.contrib.auth.models import Group
from django.test import TestCase
from django.urls import reverse

from plants.tests.utils import get_custom_user, get_family, get_genus, get_species


class FeedbackTestCase(TestCase):
    def setUp(self) -> None:
        plant_curator_group = Group.objects.create(name='Plant Collection Curators')
        self.user = get_custom_user()
        plant_curator_group.user_set.add(self.user)

        self.family = get_family()
        self.genus = get_genus(self.family)
        self.species = get_species(self.genus)

    def test_feedback_form_species_display(self):
        response = self.client.get(reverse('plants:species-feedback', args=[self.species.id]))

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, f'<option value="{self.species.id}" selected>{str(self.species)}</option>')
