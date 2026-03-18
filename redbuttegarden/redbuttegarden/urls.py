import os

from django.conf import settings
from django.contrib import admin
from django.http import Http404
from django.templatetags.static import static
from django.urls import include, path
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from wagtail.admin import urls as wagtailadmin_urls

from wagtail.contrib.sitemaps import views as wagtail_sitemap_views
from wagtail.contrib.sitemaps.sitemap_generator import Sitemap as WagtailSitemap
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.models import Site

from search import views as search_views
from sitemaps.sitemaps import (
    PlantsStaticViewsSitemap,
    CollectionDetailSitemap,
    SpeciesDetailSitemap,
)

SITEMAPS = {
    "wagtail": WagtailSitemap,
    "plants-static": PlantsStaticViewsSitemap,
    "collections": CollectionDetailSitemap,
    "species": SpeciesDetailSitemap,
}

CACHE_SECONDS = 60 * 60  # 1 hour


def _force_default_site(request):
    default_site = Site.objects.get(is_default_site=True)

    # Only serve sitemap on the default hostname (keeps domains consistent)
    req_host = request.get_host().split(":")[0]
    if req_host != default_site.hostname:
        raise Http404()

    request._wagtail_site = default_site
    request.site = default_site
    return default_site


@cache_page(CACHE_SECONDS)
def sitemap_index(request):
    _force_default_site(request)
    return wagtail_sitemap_views.index(
        request,
        sitemaps=SITEMAPS,
        sitemap_url_name="sitemap-section",
    )


@cache_page(CACHE_SECONDS)
def sitemap_section(request, section):
    _force_default_site(request)
    return wagtail_sitemap_views.sitemap(request, sitemaps=SITEMAPS, section=section)


urlpatterns = []
"""
Needed to use this wonky method of defining urlpatterns to avoid having the local
environment try to authenticate using CAS.
"""
if not os.environ.get("DJANGO_SETTINGS_MODULE") in [
    "redbuttegarden.settings.local",
    "redbuttegarden.settings.testing",
]:
    import cas.views

    urlpatterns = [
        # CAS
        path("admin/login/", cas.views.login, name="login"),
        path("admin/logout/", cas.views.logout, name="logout"),
    ]

urlpatterns += [
    path("sitemap.xml", sitemap_index, name="sitemap-index"),
    path("sitemap-<str:section>.xml", sitemap_section, name="sitemap-section"),
    path("", include("home.urls", namespace="home")),
    # May need to temporarily comment out plants app urls to migrate fresh database
    path("plants/", include("plants.urls", namespace="plants")),
    path("accounts/", include("custom_user.urls", namespace="custom-user")),
    path("concerts/", include("concerts.urls", namespace="concerts")),
    path("shop/", include("shop.urls", namespace="shop")),
    path("members/", include("memberships.urls", namespace="members")),
    path("django-admin/", admin.site.urls),
    path("admin/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path("search/", search_views.search, name="search"),
    path("api-auth/", include("rest_framework.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    path(
        "apple-touch-icon.png",
        RedirectView.as_view(
            url=static("redbuttegarden/img/favicon/apple-touch-icon-152x152.png"),
            permanent=True,
        ),
    ),
    path(
        "apple-touch-icon-precomposed.png",
        RedirectView.as_view(
            url=static("redbuttegarden/img/favicon/apple-touch-icon-152x152.png"),
            permanent=True,
        ),
    ),
]

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns

    # Serve static and media files from development server
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    urlpatterns += [path("__debug__/", include(debug_toolbar.urls))]

urlpatterns = urlpatterns + [
    # For anything not caught by a more specific rule above, hand over to
    # Wagtail's page serving mechanism. This should be the last pattern in
    # the list:
    path("", include(wagtail_urls)),
    # Alternatively, if you want Wagtail pages to be served from a subpath
    # of your site, rather than the site root:
    #    url(r"^pages/", include(wagtail_urls)),
]
