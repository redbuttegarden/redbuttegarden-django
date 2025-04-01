from django import forms
from .models import ConcertDonorClubPackage, Concert


class ConcertDonorClubPackageForm(forms.ModelForm):
    class Meta:
        model = ConcertDonorClubPackage
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            package = self.instance
            self.fields['concerts'].queryset = Concert.objects.filter(begin__year=package.year)
