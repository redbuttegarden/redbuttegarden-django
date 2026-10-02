"""Public Web Push preference and analytics URLs."""

from django.urls import path

from . import views

app_name = "push_notifications"
urlpatterns = [
    path("", views.preferences, name="preferences"),
    path("subscriptions/", views.subscriptions, name="subscriptions"),
    path("click/", views.click, name="click"),
]
