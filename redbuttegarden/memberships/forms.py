from django import forms

from .widget_config import MembershipWidgetConfig
from .services.recommendations import (
    DEFAULT_PRICE_FALLBACK_FORMULAS,
    DEFAULT_RECOMMENDATION_FORMULAS,
    get_default_price_fallback_formulas,
    validate_price_fallback_formula,
    validate_recommendation_formula,
)


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


FORMULA_FIELD_NAMES = (
    "downsell_1_formulas",
    "downsell_2_formulas",
    "upsell_1_formulas",
    "upsell_2_formulas",
)

FORMULA_FIELD_HELP_TEXT = (
    "One formula per line, evaluated top to bottom. Supported terms: C, G, T, "
    "prev(T), next(T), integers, +, and -."
)
PRICE_FALLBACK_FIELD_NAMES = (
    "downsell_1_price_fallback",
    "downsell_2_price_fallback",
    "upsell_1_price_fallback",
    "upsell_2_price_fallback",
)
PRICE_FALLBACK_HELP_TEXT = (
    "Enter one fallback rule in this field. Start with cheaper(n) or "
    "expensive(n), then optionally add ; match=... or ; prefer=... filters."
)


class MembershipRecommendationFormulaForm(MembershipSelectorForm):
    downsell_1_formulas = forms.CharField(
        label="Downsell 1 formulas",
        required=False,
        help_text=FORMULA_FIELD_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control font-monospace formula-lab-textarea",
                "rows": 6,
                "spellcheck": "false",
            }
        ),
    )
    downsell_2_formulas = forms.CharField(
        label="Downsell 2 formulas",
        required=False,
        help_text=FORMULA_FIELD_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control font-monospace formula-lab-textarea",
                "rows": 7,
                "spellcheck": "false",
            }
        ),
    )
    upsell_1_formulas = forms.CharField(
        label="Upsell 1 formulas",
        required=False,
        help_text=FORMULA_FIELD_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control font-monospace formula-lab-textarea",
                "rows": 6,
                "spellcheck": "false",
            }
        ),
    )
    upsell_2_formulas = forms.CharField(
        label="Upsell 2 formulas",
        required=False,
        help_text=FORMULA_FIELD_HELP_TEXT,
        widget=forms.Textarea(
            attrs={
                "class": "form-control font-monospace formula-lab-textarea",
                "rows": 7,
                "spellcheck": "false",
            }
        ),
    )
    downsell_1_price_fallback = forms.CharField(
        label="Downsell 1 price fallback",
        required=False,
        help_text=PRICE_FALLBACK_HELP_TEXT,
        widget=forms.TextInput(
            attrs={
                "class": "form-control font-monospace formula-lab-input",
                "spellcheck": "false",
            }
        ),
    )
    downsell_2_price_fallback = forms.CharField(
        label="Downsell 2 price fallback",
        required=False,
        help_text=PRICE_FALLBACK_HELP_TEXT,
        widget=forms.TextInput(
            attrs={
                "class": "form-control font-monospace formula-lab-input",
                "spellcheck": "false",
            }
        ),
    )
    upsell_1_price_fallback = forms.CharField(
        label="Upsell 1 price fallback",
        required=False,
        help_text=PRICE_FALLBACK_HELP_TEXT,
        widget=forms.TextInput(
            attrs={
                "class": "form-control font-monospace formula-lab-input",
                "spellcheck": "false",
            }
        ),
    )
    upsell_2_price_fallback = forms.CharField(
        label="Upsell 2 price fallback",
        required=False,
        help_text=PRICE_FALLBACK_HELP_TEXT,
        widget=forms.TextInput(
            attrs={
                "class": "form-control font-monospace formula-lab-input",
                "spellcheck": "false",
            }
        ),
    )

    def __init__(self, *args, cfg=None, **kwargs):
        super().__init__(*args, cfg=cfg, **kwargs)
        for field_name, formulas in DEFAULT_RECOMMENDATION_FORMULAS.items():
            form_field_name = f"{field_name}_formulas"
            self.fields[form_field_name].initial = "\n".join(formulas)
        for field_name, formula in DEFAULT_PRICE_FALLBACK_FORMULAS.items():
            form_field_name = f"{field_name}_price_fallback"
            self.fields[form_field_name].initial = formula

    def _clean_formula_field(self, field_name):
        raw_value = self.cleaned_data.get(field_name, "")
        lines = tuple(line.strip() for line in raw_value.splitlines() if line.strip())

        for index, formula in enumerate(lines, start=1):
            try:
                validate_recommendation_formula(formula)
            except ValueError as exc:
                raise forms.ValidationError(f"Line {index}: {exc}") from exc

        return lines

    def clean_downsell_1_formulas(self):
        return self._clean_formula_field("downsell_1_formulas")

    def clean_downsell_2_formulas(self):
        return self._clean_formula_field("downsell_2_formulas")

    def clean_upsell_1_formulas(self):
        return self._clean_formula_field("upsell_1_formulas")

    def clean_upsell_2_formulas(self):
        return self._clean_formula_field("upsell_2_formulas")

    def _clean_price_fallback_field(self, field_name):
        raw_value = (self.cleaned_data.get(field_name) or "").strip()
        slot_name = field_name.removesuffix("_price_fallback")
        if not raw_value:
            return get_default_price_fallback_formulas()[slot_name]

        try:
            validate_price_fallback_formula(raw_value)
        except ValueError as exc:
            raise forms.ValidationError(str(exc)) from exc

        return raw_value

    def get_formula_config(self):
        return {
            field_name.removesuffix("_formulas"): self.cleaned_data[field_name]
            for field_name in FORMULA_FIELD_NAMES
        }

    def clean_downsell_1_price_fallback(self):
        return self._clean_price_fallback_field("downsell_1_price_fallback")

    def clean_downsell_2_price_fallback(self):
        return self._clean_price_fallback_field("downsell_2_price_fallback")

    def clean_upsell_1_price_fallback(self):
        return self._clean_price_fallback_field("upsell_1_price_fallback")

    def clean_upsell_2_price_fallback(self):
        return self._clean_price_fallback_field("upsell_2_price_fallback")

    def get_price_fallback_config(self):
        return {
            field_name.removesuffix("_price_fallback"): self.cleaned_data[field_name]
            for field_name in PRICE_FALLBACK_FIELD_NAMES
        }
