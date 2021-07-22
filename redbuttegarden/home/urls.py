from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('social-media/', views.social_media, name='social-media'),
    path('vr-tours/', views.vr_tours, name='vr-tours'),
]
