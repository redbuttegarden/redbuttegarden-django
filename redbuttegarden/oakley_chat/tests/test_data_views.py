from datetime import timedelta

import pytest

from django.contrib.auth import get_user_model
from django.utils import timezone
from wagtail.models import Page

from events.models import EventCategory, EventGeneralPage, EventIndexPage, EventPage
from plants.models import BloomEvent
from plants.tests.utils import get_collection, get_family, get_genus, get_garden_area, get_species


@pytest.mark.django_db
def test_garden_events_data_requires_api_key(client, settings):
    settings.OAKLEY_DATA_API_KEY = "shared-secret"

    response = client.get("/oakley-chat/data/events/")

    assert response.status_code == 403
    assert response.json()["detail"] == "Unauthorized"


@pytest.mark.django_db
def test_garden_events_data_returns_normalized_results(client, settings):
    settings.OAKLEY_DATA_API_KEY = "shared-secret"
    root_page = Page.objects.get(id=2)
    user = get_user_model().objects.create_user("oakley-editor")
    event_index = EventIndexPage(title="Events", slug="oakley-events", owner=user)
    root_page.add_child(instance=event_index)
    event_index.save_revision().publish()

    category = EventCategory.objects.create(name="Classes", slug="classes")
    start_datetime = timezone.now() + timedelta(days=7)
    event_page = EventPage(
        title="Botanical Watercolor Class",
        slug="botanical-watercolor-class",
        owner=user,
        location="Orangerie",
        instructor="Jane Doe",
        event_dates="May 15, 2026",
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=2),
        sub_heading="Paint among the blooms",
        search_description="A watercolor workshop in the Garden.",
        purchase_url="https://example.com/register",
    )
    event_index.add_child(instance=event_page)
    event_page.event_categories.add(category)
    event_page.save_revision().publish()

    general_page = EventGeneralPage(
        title="Spring Plant Sale",
        slug="spring-plant-sale",
        owner=user,
        event_dates="All weekend",
        notes="<p>Member preview on Friday.</p>",
        search_description="Seasonal sale event",
    )
    event_index.add_child(instance=general_page)
    general_page.event_categories.add(category)
    general_page.save_revision().publish()

    response = client.get(
        "/oakley-chat/data/events/",
        {"limit": 5},
        HTTP_X_API_KEY="shared-secret",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 2
    titles = [item["title"] for item in payload["results"]]
    assert "Botanical Watercolor Class" in titles
    assert "Spring Plant Sale" in titles

    watercolor = next(
        item for item in payload["results"] if item["title"] == "Botanical Watercolor Class"
    )
    assert watercolor["page_type"] == "event_page"
    assert watercolor["location"] == "Orangerie"
    assert watercolor["instructor"] == "Jane Doe"
    assert watercolor["categories"] == ["Classes"]
    assert watercolor["purchase_url"] == "https://example.com/register"


@pytest.mark.django_db
def test_garden_events_data_treats_generic_prompt_as_browse_request(client, settings):
    settings.OAKLEY_DATA_API_KEY = "shared-secret"
    root_page = Page.objects.get(id=2)
    user = get_user_model().objects.create_user("oakley-browse-editor")
    event_index = EventIndexPage(title="Events", slug="oakley-browse-events", owner=user)
    root_page.add_child(instance=event_index)
    event_index.save_revision().publish()

    start_datetime = timezone.now() + timedelta(days=5)
    event_page = EventPage(
        title="Evening Garden Walk",
        slug="evening-garden-walk",
        owner=user,
        location="Visitor Center",
        event_dates="May 20, 2026",
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=1),
        search_description="A guided walk through the spring garden.",
    )
    event_index.add_child(instance=event_page)
    event_page.save_revision().publish()

    response = client.get(
        "/oakley-chat/data/events/",
        {"q": "What non-concert events are coming up at Red Butte Garden?"},
        HTTP_X_API_KEY="shared-secret",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["title"] == "Evening Garden Walk"


@pytest.mark.django_db
def test_garden_events_data_matches_prompt_terms_to_event_page_content(client, settings):
    settings.OAKLEY_DATA_API_KEY = "shared-secret"
    root_page = Page.objects.get(id=2)
    user = get_user_model().objects.create_user("oakley-search-editor")
    event_index = EventIndexPage(title="Events", slug="oakley-search-events", owner=user)
    root_page.add_child(instance=event_index)
    event_index.save_revision().publish()

    classes = EventCategory.objects.create(name="Classes", slug="classes-token")
    start_datetime = timezone.now() + timedelta(days=9)
    event_page = EventPage(
        title="Botanical Watercolor Class",
        slug="botanical-watercolor-class-token",
        owner=user,
        location="Orangerie",
        instructor="Jane Doe",
        event_dates="May 25, 2026",
        start_datetime=start_datetime,
        end_datetime=start_datetime + timedelta(hours=2),
        search_description="A hands-on watercolor workshop with native plants.",
    )
    event_index.add_child(instance=event_page)
    event_page.event_categories.add(classes)
    event_page.save_revision().publish()

    response = client.get(
        "/oakley-chat/data/events/",
        {"q": "Are there any watercolor classes coming up soon?"},
        HTTP_X_API_KEY="shared-secret",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["title"] == "Botanical Watercolor Class"


@pytest.mark.django_db
def test_plants_data_returns_grouped_results(client, settings):
    settings.OAKLEY_DATA_API_KEY = "shared-secret"

    family = get_family(name="Rosaceae")
    family.vernacular_name = "Rose family"
    family.save(update_fields=["vernacular_name"])
    genus = get_genus(family, name="Rosa")
    species = get_species(
        genus,
        name="woodsii",
        full_name="Rosa woodsii",
        vernacular_name="Woods rose",
        habit="Shrub",
        deer_resist=True,
        rabbit_resist=True,
        bee_friend=True,
    )
    garden_area = get_garden_area(area="Rose Walk", name="Rose Garden", code="RG-01")
    collection = get_collection(
        family_name=family.name,
        genus_name=genus.name,
        species_name=species.name,
        full_name=species.full_name,
        vernacular_name=species.vernacular_name,
        habit=species.habit,
        plant_id="RG-42",
        area=garden_area.area,
        ga_name=garden_area.name,
        code=garden_area.code,
    )
    bloom_event = BloomEvent.objects.create(
        title="Rose Bloom Watch",
        description="Peak bloom for the rose walk.",
        species=species,
        area=garden_area,
        bloom_start=timezone.localdate() - timedelta(days=1),
        bloom_end=timezone.localdate() + timedelta(days=3),
    )

    response = client.get(
        "/oakley-chat/data/plants/",
        {"q": "rose", "in_bloom": "true", "limit": 5},
        HTTP_X_API_KEY="shared-secret",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["families"][0]["name"] == "Rosaceae"
    assert payload["genera"][0]["name"] == "Rosa"
    assert payload["species"][0]["full_name"] == "Rosa woodsii"
    assert payload["collections"][0]["plant_id"] == collection.plant_id
    assert payload["garden_areas"][0]["name"] == "Rose Garden"
    assert payload["bloom_events"][0]["title"] == bloom_event.title
    assert payload["counts"]["species"] >= 1
