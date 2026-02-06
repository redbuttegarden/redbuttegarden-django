from django import forms


class MembershipSelectorForm(forms.Form):
    cardholders = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Cardholders",
        widget=forms.NumberInput(
            attrs={"class": "form-control", "min": "1", "aria-label": "Cardholders"}
        ),
    )

    admissions = forms.IntegerField(
        min_value=1,
        initial=2,
        label="Admissions per visit",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "aria-label": "Admissions per visit",
            }
        ),
    )

    member_tickets = forms.IntegerField(
        min_value=0,
        initial=2,
        label="Member-sale tickets",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "aria-label": "Member-sale tickets",
            }
        ),
    )
