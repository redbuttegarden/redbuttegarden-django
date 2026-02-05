import logging
import re

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import JsonResponse
from django.shortcuts import render

from wagtail.models import Page
from wagtail.contrib.search_promotions.models import Query

logger = logging.getLogger(__name__)

CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def search(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    search_query = request.GET.get('q', None)
    page_number = request.GET.get('page', 1)

    # build query_prefix preserving all current GET params except 'page'
    params = request.GET.copy()
    params.pop('page', None)
    query_prefix = params.urlencode()
    if query_prefix:
        # add trailing ampersand so include can just append page=...
        query_prefix = query_prefix + '&'


    # Search
    if search_query:
        search_query = CONTROL_CHARS.sub("", search_query).strip() or None
        logger.debug(f"Search query: {search_query}")
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
        paginated_results = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)

    if is_ajax:
        logger.debug(f'Search query: {search_query}')
        logger.debug(f'Filtered results: {filtered_results}')
        logger.debug(f'Paginated results: {filtered_results}')
        results = [{'title': result.title, 'url': result.url} for result in paginated_results]

        return JsonResponse({
            'results': results,
            'page': paginated_results.number,
            'pages': paginator.num_pages,
        })
    return render(request, 'search/search.html', {
        'search_query': search_query,
        'search_results': paginated_results,
        'query_prefix': query_prefix,
    })
