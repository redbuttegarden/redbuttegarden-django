from django import forms


class MembershipSelectorForm(forms.Form):
    cardholders = forms.IntegerField(
        min_value=1,
        max_value=3,
        initial=1,
        label="Cardholders",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "max": "3",
                "aria-label": "Cardholders",
            }
        ),
    )

    admissions = forms.IntegerField(
        min_value=1,
        max_value=8,
        initial=2,
        label="Additional Admission Guest Entry",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "max": "8",
                "aria-label": "Additional Admission Guest Entry",
            }
        ),
    )

    member_tickets = forms.IntegerField(
        min_value=0,
        max_value=6,
        initial=2,
        label="Concert Series Pre-Sale Member Tickets",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "max": "6",
                "aria-label": "Concert Series Pre-Sale Member Tickets",
            }
        ),
    )
