from django.urls import path

from . import views

app_name = 'altru'
urlpatterns = [
    path('auth/', views.altru_auth, name='auth'),
    path('api/callback', views.callback, name='api-callback'),
    path('constituent/notes/', views.create_constituent_notes, name='constituent_notes')
]
