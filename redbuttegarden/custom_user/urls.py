from django.contrib.auth import views as auth_views
from django.urls import path, include

from custom_user.forms import NoStaffLoginForm

app_name = 'custom_user'
urlpatterns = [
    path('login/', auth_views.LoginView.as_view(authentication_form=NoStaffLoginForm), name='login'),
    path('', include('django.contrib.auth.urls')),
]
