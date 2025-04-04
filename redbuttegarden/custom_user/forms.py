from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Permission
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from wagtail.users.forms import UserEditForm, UserCreationForm

from home.templatetags.navigation_tags import is_active


class CustomUserEditForm(UserEditForm):
    title = forms.CharField(required=True, label=_('Title'))

    # This replaces the `WAGTAIL_USER_CUSTOM_FIELDS` setting.
    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"title"}


class CustomUserCreationForm(UserCreationForm):
    title = forms.CharField(required=True, label=_('Title'))

    # This replaces the `WAGTAIL_USER_CUSTOM_FIELDS` setting.
    class Meta(UserEditForm.Meta):
        fields = UserEditForm.Meta.fields | {"title"}


class NoStaffLoginForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        perm = Permission.objects.get(codename='access_admin')
        wagtail_admin_users = get_user_model().objects.filter(
            Q(groups__permissions=perm) | Q(user_permissions=perm) | Q(is_superuser=True),
            is_active=True).distinct()
        if user in wagtail_admin_users:
            admin_login_url = settings.WAGTAILADMIN_BASE_URL + '/admin/'
            raise ValidationError(
                format_html("RBG staff are required to login via the <a href='{}'>Wagtail Admin</a>.", admin_login_url),
            )
