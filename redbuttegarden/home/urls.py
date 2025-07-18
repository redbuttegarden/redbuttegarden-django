from django.urls import path

from . import views

app_name = 'home'
urlpatterns = [
    path('api/latest-weather/', views.latest_weather, name='latest-weather'),
    path('api/hours/<int:page_id>', views.get_hours, name='hours'),
    path('robots.txt', views.robots_txt, name='robots-txt'),
]
