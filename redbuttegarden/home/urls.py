from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('directions/', views.directions, name='directions'),
    path('general-info/', views.general_info, name='general-info'),
]
