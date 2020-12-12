from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('social-media/', views.social_media, name='social-media'),
]
