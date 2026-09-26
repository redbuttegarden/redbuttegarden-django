import logging
import re

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render

from wagtail.contrib.search_promotions.models import Query
from wagtail.models import Page, Site

logger = logging.getLogger(__name__)

CONTROL_CHARS = re.compile(r"[\x00-\x1f\x7f]")


def search(request: HttpRequest) -> HttpResponse:
    """Return public search results from the Wagtail site serving this request."""

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
    search_query = CONTROL_CHARS.sub("", search_query or "").strip() or None
    if search_query:
        site = Site.find_for_request(request)
        pages = (
            Page.objects.in_site(site)
            .live()
            .public()
            .filter(
                pk__in=Page.objects.filter(alias_of__isnull=True).values("pk")
            )
        )
        logger.debug("Search query: %s", search_query)
        search_results = pages.search(search_query)
        query = Query.get(search_query)

        # Record hit
        query.add_hit()
    else:
        search_results = Page.objects.none()

    # Pagination
    paginator = Paginator(search_results, 10)

    try:
        paginated_results = paginator.page(page_number)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)

    if is_ajax:
        logger.debug('Search query: %s', search_query)
        logger.debug('Paginated results: %s', paginated_results.object_list)
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
