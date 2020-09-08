from django.urls import path

from . import views

app_name = 'concerts'
urlpatterns = [
    path('concerts', views.concerts, name='concerts'),
]
