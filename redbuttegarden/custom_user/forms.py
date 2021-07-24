from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from wagtail.users.forms import UserEditForm, UserCreationForm


class CustomUserEditForm(UserEditForm):
    title = forms.CharField(required=True, label=_('Title'))


class CustomUserCreationForm(UserCreationForm):
    title = forms.CharField(required=True, label=_('Title'))


class NoStaffLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        perm = Permission.objects.get(codename='access_admin')
        wagtail_admin_users = get_user_model().objects.filter(Q(groups__permissions=perm) | Q(user_permissions=perm))
        if user in wagtail_admin_users:
            raise ValidationError(
                _("RBG staff are not permitted to use this login form.")
            )
