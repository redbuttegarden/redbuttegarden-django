import pytest
from django.core.exceptions import ValidationError
from django.shortcuts import reverse

from plants.tests.utils import get_collection
from plants.utils import filter_by_parameter


@pytest.mark.django_db
def test_filter_by_parameter(rf):
    utah_nonnative_collection = get_collection(utah_native=False, plant_id='1')
    utah_native_collection = get_collection(utah_native=True, plant_id='2')
    string_search = {
        'scientific_name': 'test',
        'common_name': 'test',
        'family': 'test',
        'garden_name': 'test',
        'habit': 'test',
        'exposure': 'test',
        'water_need': 'test',
        'bloom_month': 'test',
        'flower_color': 'test',
        'memorial_person': 'test',
        'utah_native': 'test',
        'plant_select': 'test',
        'deer_resistant': 'test',
        'rabbit_resistant': 'test',
        'bee_friendly': 'test',
        'high_elevation': 'test',
        'available_memorial': 'test'
    }
    request = rf.get(reverse('plants:collection-search'), string_search)
    with pytest.raises(ValidationError):
        filter_by_parameter(request)

    utah_nonnative_search = {
        'utah_native': False,
    }

    request = rf.get(reverse('plants:collection-search'), utah_nonnative_search)
    collections = filter_by_parameter(request)
    assert collections.count() == 1
    assert collections[0] == utah_nonnative_collection

    utah_native_search = {
        'utah_native': True,
    }

    request = rf.get(reverse('plants:collection-search'), utah_native_search)
    collections = filter_by_parameter(request)
    assert collections.count() == 1
    assert collections[0] == utah_native_collection
