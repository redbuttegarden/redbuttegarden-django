import pytest
from django.urls import reverse

from plants.models import Collection
from plants.tests.utils import get_garden_area, get_location, get_species


@pytest.mark.django_db
def test_species_detail_shows_species_collections_table(client, genus):
    species = get_species(
        genus,
        name="woodsii",
        full_name="Rosa woodsii",
        vernacular_name="Woods rose",
    )
    other_species = get_species(
        genus,
        name="nutkana",
        full_name="Rosa nutkana",
        vernacular_name="Nootka rose",
    )
    garden = get_garden_area()
    location = get_location()

    collection = Collection.objects.create(
        location=location,
        garden=garden,
        species=species,
        plant_id="RG-42",
    )
    Collection.objects.create(
        location=location,
        garden=garden,
        species=other_species,
        plant_id="RG-99",
    )

    response = client.get(reverse("plants:species-detail", args=[species.id]))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'id="species-collections"' in content
    assert 'id="collection-list-table"' in content
    assert "RG-42" in content
    assert reverse("plants:collection-detail", args=[collection.id]) in content
    assert "RG-99" not in content


@pytest.mark.django_db
def test_species_detail_paginates_collections_table(client, genus):
    species = get_species(
        genus,
        name="paginata",
        full_name="Aster paginata",
        vernacular_name="Paged aster",
    )
    garden = get_garden_area()
    location = get_location()

    created_ids = []
    for index in range(51):
        collection = Collection.objects.create(
            location=location,
            garden=garden,
            species=species,
            plant_id=f"RG-{index:03d}",
        )
        created_ids.append(collection.plant_id)

    url = reverse("plants:species-detail", args=[species.id])

    page_one = client.get(url)
    assert page_one.status_code == 200
    table = page_one.context["collections_table"]
    assert table.page.number == 1
    assert len(table.page.object_list) == 50
    assert created_ids[0] not in page_one.content.decode("utf-8")

    page_two = client.get(url, {"page": 2})
    assert page_two.status_code == 200
    table = page_two.context["collections_table"]
    assert table.page.number == 2
    assert len(table.page.object_list) == 1
    assert created_ids[0] in page_two.content.decode("utf-8")


@pytest.mark.django_db
def test_species_detail_hides_collections_table_when_species_has_none(client, genus):
    species = get_species(
        genus,
        name="palustris",
        full_name="Aster palustris",
        vernacular_name="Saltmarsh aster",
    )

    response = client.get(reverse("plants:species-detail", args=[species.id]))

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'id="species-collections"' not in content
    assert 'id="collection-list-table"' not in content
