import os

from django.conf import settings
from django.urls import include, path
from django.contrib import admin
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps.views import sitemap
from wagtail import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from search import views as search_views

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
    path("sitemap.xml", sitemap),
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
