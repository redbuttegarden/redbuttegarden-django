from django import forms


def validate_even(value):
    if value % 2 != 0:
        raise forms.ValidationError("Please choose 0, 2, 4, or 6.")


class MembershipSelectorForm(forms.Form):
    cardholders = forms.IntegerField(
        min_value=1,
        max_value=3,
        initial=1,
        label="Cardholders",
        validators=[validate_even],
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "1",
                "max": "3",
                "step": "2",
                "aria-label": "Cardholders",
            }
        ),
    )

    admissions = forms.IntegerField(
        min_value=0,
        max_value=8,
        initial=2,
        label="Additional Admission Guest Entry",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
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

    def __init__(self, *args, cfg=None, **kwargs):
        super().__init__(*args, **kwargs)
        if not cfg:
            return
        
        if cfg.cardholder_label:
            self.fields["cardholders"].label = cfg.cardholder_label
            self.fields["cardholders"].widget.attrs["aria-label"] = cfg.cardholder_label

        if cfg.admissions_label:
            self.fields["admissions"].label = cfg.admissions_label
            self.fields["admissions"].widget.attrs["aria-label"] = cfg.admissions_label

        if cfg.member_tickets_label:
            self.fields["member_tickets"].label = cfg.member_tickets_label
            self.fields["member_tickets"].widget.attrs["aria-label"] = cfg.member_tickets_label
