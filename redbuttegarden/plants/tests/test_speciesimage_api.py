import io

import pytest
from django.contrib.auth.models import Group, Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from PIL import Image as PILImage
from rest_framework.test import APIClient
from wagtail.images import get_image_model
from wagtail.images.permissions import permission_policy as image_permission_policy
from wagtail.models import GroupCollectionPermission

from plants.models import SpeciesImage


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="user",
        email="user@example.com",
        password="pass12345",
    )


@pytest.fixture
def authed_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


def _make_test_image_file(name: str = "test.jpg", size=(50, 50)) -> SimpleUploadedFile:
    buf = io.BytesIO()
    img = PILImage.new("RGB", size)
    img.save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/jpeg")


@pytest.fixture
def wagtail_image(db):
    ImageModel = get_image_model()
    image_file = _make_test_image_file()

    # Most Wagtail installs require title + file.
    # Some use collection; default collection should exist in Wagtail test DB.
    return ImageModel.objects.create(title="Test image", file=image_file)


@pytest.fixture
def species_image(db, species, wagtail_image):
    return SpeciesImage.objects.create(
        species=species,
        image=wagtail_image,
        caption="",
        copyright="",
        sort_order=0,
    )


@pytest.mark.django_db
class TestSpeciesImageAPIAuth:
    def test_list_requires_auth(self, api_client):
        url = reverse("plants:speciesimage-list")
        resp = api_client.get(url)
        assert resp.status_code in (401, 403)

    def test_detail_requires_auth(self, api_client, species_image):
        url = reverse("plants:speciesimage-image-description", kwargs={"pk": species_image.pk})
        resp = api_client.get(url)
        assert resp.status_code in (401, 403)

    def test_patch_requires_auth(self, api_client, species_image):
        url = reverse("plants:speciesimage-image-description", kwargs={"pk": species_image.pk})
        resp = api_client.patch(
            url, data={"description_write": "New alt text"}, format="json"
        )
        assert resp.status_code in (401, 403)


@pytest.mark.django_db
class TestSpeciesImageAPILogic:
    def test_authed_user_can_get_list(self, authed_client, species_image):
        url = reverse("plants:speciesimage-list")
        resp = authed_client.get(url)
        assert resp.status_code == 200

        # Depending on pagination settings, response is dict with "results" or a list
        data = resp.json()
        if isinstance(data, dict) and "results" in data:
            items = data["results"]
        else:
            items = data

        assert any(item["id"] == species_image.id for item in items)

    def test_authed_user_can_get_detail_includes_species_full_name(
        self, authed_client, species_image
    ):
        url = reverse("plants:speciesimage-image-description", kwargs={"pk": species_image.pk})
        resp = authed_client.get(url)
        assert resp.status_code == 200
        data = resp.json()

        assert "species_full_name" in data
        assert data["species_full_name"] == species_image.species.full_name

        assert "image_id" in data
        assert data["image_id"] == species_image.image_id

        assert "description" in data  

    def test_patch_denied_without_wagtail_change_permission(
        self, authed_client, species_image
    ):
        url = reverse("plants:speciesimage-image-description", kwargs={"pk": species_image.pk})
        resp = authed_client.patch(
            url, data={"description_write": "Attempted change"}, format="json"
        )
        assert resp.status_code == 403


    def test_patch_updates_wagtail_image_description_with_permission(
        self, authed_client, user, species_image
    ):
        ImageModel = get_image_model()
        if not hasattr(ImageModel, "description"):
            pytest.skip("Wagtail Image model has no 'description' field in this project.")

        image = species_image.image
        assert image.collection_id is not None

        group = Group.objects.create(name="api-image-editors")
        user.groups.add(group)

        # Assign collection-scoped permission (Wagtail uses Django Permission records)
        change_perm = Permission.objects.get(
            content_type__app_label="wagtailimages",
            codename="change_image",
        )

        GroupCollectionPermission.objects.create(
            group=group,
            collection=image.collection,
            permission=change_perm,
        )

        # Sanity check: permission policy should allow change
        assert image_permission_policy.user_has_permission_for_instance(user, "change", image)

        url = reverse("plants:speciesimage-image-description", kwargs={"pk": species_image.pk})
        resp = authed_client.patch(url, data={"description_write": "Example alt text"}, format="json")
        assert resp.status_code == 200
        data = resp.json()

        assert data["species_full_name"] == species_image.species.full_name
        assert data["image_id"] == species_image.image_id
        assert data["description"] == "Example alt text"

        species_image.image.refresh_from_db()
        assert species_image.image.description == "Example alt text"