from django.urls import path
from . import views

app_name = "members"
urlpatterns = [
    path("membership/", views.membership_selector_page, name="membership_selector"),
    path("membership/suggest/", views.membership_suggest, name="membership_suggest"),
]
