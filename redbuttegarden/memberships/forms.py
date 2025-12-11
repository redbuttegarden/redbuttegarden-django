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
        initial=1,
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

    # Weighting / prioritization: user can assign importance to each factor (0–10)
    # Render sliders by using NumberInput with type='range'.
    admissions_weight = forms.IntegerField(
        min_value=0,
        max_value=10,
        initial=5,
        label="Admissions weight (priority)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-range",
                "type": "range",
                "min": "0",
                "max": "10",
                "step": "1",
                "id": "id_admissions_weight",
                "aria-label": "Admissions weight",
            }
        ),
    )

    cardholders_weight = forms.IntegerField(
        min_value=0,
        max_value=10,
        initial=3,
        label="Cardholders weight (priority)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-range",
                "type": "range",
                "min": "0",
                "max": "10",
                "step": "1",
                "id": "id_cardholders_weight",
                "aria-label": "Cardholders weight",
            }
        ),
    )

    tickets_weight = forms.IntegerField(
        min_value=0,
        max_value=10,
        initial=1,
        label="Tickets weight (priority)",
        widget=forms.NumberInput(
            attrs={
                "class": "form-range",
                "type": "range",
                "min": "0",
                "max": "10",
                "step": "1",
                "id": "id_tickets_weight",
                "aria-label": "Tickets weight",
            }
        ),
    )

    def clean(self):
        cleaned = super().clean()
        total = (
            cleaned.get("admissions_weight", 0)
            + cleaned.get("cardholders_weight", 0)
            + cleaned.get("tickets_weight", 0)
        )
        if total <= 0:
            raise forms.ValidationError(
                "Please assign at least one positive priority weight."
            )
        return cleaned
