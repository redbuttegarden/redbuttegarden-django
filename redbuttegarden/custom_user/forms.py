from django import forms
from django.utils.translation import ugettext_lazy as _

from wagtail.users.forms import UserEditForm, UserCreationForm


class CustomUserEditForm(UserEditForm):
    title = forms.CharField(required=True, label=_('Title'))


class CustomUserCreationForm(UserCreationForm):
    title = forms.CharField(required=True, label=_('Title'))
