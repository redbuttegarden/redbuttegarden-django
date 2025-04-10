import datetime

from django import forms
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from wagtail.admin.forms import WagtailAdminModelForm

from .models import ConcertDonorClubPackage, Concert, ConcertDonorClubMember


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
