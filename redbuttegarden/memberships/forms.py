from django import forms

from .widget_config import MembershipWidgetConfig


def validate_even(value):
    if value % 2 != 0:
        raise forms.ValidationError("Please choose 0, 2, 4, or 6.")


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
        validators=[validate_even],
        label="Concert Series Pre-Sale Member Tickets",
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "min": "0",
                "max": "6",
                "step": "2",
                "aria-label": "Concert Series Pre-Sale Member Tickets",
            }
        ),
    )

    def __init__(self, *args, cfg=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cfg = cfg or MembershipWidgetConfig.get_solo()

        if self.cfg.cardholder_label:
            self.fields["cardholders"].label = self.cfg.cardholder_label
            self.fields["cardholders"].widget.attrs[
                "aria-label"
            ] = self.cfg.cardholder_label

        if self.cfg.admissions_label:
            self.fields["admissions"].label = self.cfg.admissions_label
            self.fields["admissions"].widget.attrs[
                "aria-label"
            ] = self.cfg.admissions_label

        if self.cfg.member_tickets_label:
            self.fields["member_tickets"].label = self.cfg.member_tickets_label
            self.fields["member_tickets"].widget.attrs[
                "aria-label"
            ] = self.cfg.member_tickets_label

    def clean(self):
        cleaned = super().clean()
        cardholders = cleaned.get("cardholders")
        admissions = cleaned.get("admissions")
        tickets = cleaned.get("member_tickets")

        if cardholders is None or admissions is None or tickets is None:
            return cleaned

        if tickets in {2, 4, 6} and (cardholders + admissions) < tickets:
            msg = self.cfg.presale_qualification_error_message_template.format(
                tickets=tickets
            )
            raise forms.ValidationError(msg)

        return cleaned
