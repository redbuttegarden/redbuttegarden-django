from django.urls import path

from . import views

app_name = 'concerts'
urlpatterns = [
    path('concerts', views.concerts, name='concerts'),
    path('thank-you/', views.concert_thank_you, name='thank-you'),
]
