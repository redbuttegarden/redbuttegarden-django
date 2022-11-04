import logging

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import render

from wagtail.models import Page
from wagtail.search.models import Query

logger = logging.getLogger(__name__)


def search(request):
    search_query = request.GET.get('query', None)
    page = request.GET.get('page', 1)

    # Search
    if search_query:
        search_results = Page.objects.live().public().search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    # Remove duplicate pages / aliased pages
    seen_titles = set()
    filtered_results = []
    for result in search_results:
        if result.title not in seen_titles:
            filtered_results.append(result)
            seen_titles.add(result.title)

    # Pagination
    paginator = Paginator(filtered_results, 10)
    try:
        search_results = paginator.page(page)
    except PageNotAnInteger:
        search_results = paginator.page(1)
    except EmptyPage:
        search_results = paginator.page(paginator.num_pages)

    return render(request, 'search/search.html', {
        'search_query': search_query,
        'search_results': search_results,
    })
