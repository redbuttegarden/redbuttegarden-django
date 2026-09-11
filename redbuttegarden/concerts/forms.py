"""Forms used by the concerts application."""

from __future__ import annotations

import datetime
from urllib.parse import urlsplit

from django import forms
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

from .models import ConcertDonorClubPackage, Concert, ConcertDonorClubMember


class ImageURLCheckForm(forms.Form):
    """Validate inputs used by the HTMX concert image check."""

    image_url = forms.URLField(
        max_length=2048,
        validators=[URLValidator(schemes=("http", "https"))],
        assume_scheme="https",
    )
    concert_name = forms.CharField(max_length=300, required=False)

    def clean_image_url(self) -> str:
        """Return an explicitly HTTP(S) image URL with no embedded credentials."""

        image_url: str = self.cleaned_data["image_url"]
        submitted_url = self.data.get("image_url", "")
        parsed = urlsplit(submitted_url)
        if parsed.scheme.lower() not in {"http", "https"}:
            raise forms.ValidationError("Enter an absolute HTTP(S) URL.")
        if parsed.username is not None or parsed.password is not None:
            raise forms.ValidationError("URL credentials are not allowed.")
        return image_url


class ConcertDonorClubMemberForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False, disabled=True)
    email = forms.EmailField(required=False)
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)

    class Meta:
        model = ConcertDonorClubMember
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'packages', 'active', 'constant_contact_id', 'chat_access_token']

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance and instance.user:
            initial = kwargs.get('initial', {})
            initial.update({
                'username': instance.user.username,
                'email': instance.user.email,
                'first_name': instance.user.first_name,
                'last_name': instance.user.last_name,
            })
            kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super().save(commit=False)
        user = instance.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
            instance.save()
        return instance


class ConcertDonorClubPackageForm(forms.ModelForm):
    class Meta:
        model = ConcertDonorClubPackage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            package = self.instance
            self.fields['concerts'].queryset = Concert.objects.filter(begin__year=package.year)


class UserAndConcertDonorClubMemberCreationForm(forms.Form):
    """
    Form for creating a new User and ConcertDonorClubMember.

    Useful for creating CDC members that can't be created automatically because they have no Etix Tickets of their own.
    """
    username = forms.CharField(label='Username', max_length=150)
    email = forms.EmailField(label='Email')
    phone_number = forms.CharField(max_length=150, required=False)
    first_name = forms.CharField(label='First Name', max_length=50, required=False)
    last_name = forms.CharField(label='Last Name', max_length=50)
    current_year = datetime.date.today().year
    concert_donor_club_packages = forms.ModelChoiceField(
        queryset=ConcertDonorClubPackage.objects.filter(year=current_year),
        label='Concert Donor Club Package(s) (optional)', required=False
    )
    cdc_group_members = forms.ModelChoiceField(
        queryset=ConcertDonorClubMember.objects.filter(active=True),
        label=_('Select other CDC members to make their package tickets visible to one another (optional)'),
        required=False
    )

    def clean_email(self):
        data = self.cleaned_data['email']
        if ConcertDonorClubMember.objects.filter(user__email=data).exists():
            raise forms.ValidationError(_('A CDC member with this email address already exists.'))

        return data
