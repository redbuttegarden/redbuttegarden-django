from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('general-info/', views.general_info, name='general-info'),
]
