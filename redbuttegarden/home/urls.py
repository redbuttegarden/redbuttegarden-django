from django.conf import settings
from django.urls import path

from . import views

app_name = "home"
urlpatterns = [
    path("api/latest-weather/", views.latest_weather, name="latest-weather"),
    path("api/hours/<int:page_id>", views.get_hours, name="hours"),
    path("robots.txt", views.robots_txt, name="robots-txt"),
    # The file name MUST be the key, according to the spec.
    path(
        f"{settings.INDEXNOW_KEY}.txt",
        views.indexnow_key_file,
        name="indexnow-key-file",
    ),
]
