from collections import OrderedDict

from django import forms
from django.db import models
from django.forms import CheckboxInput
from django.utils.dates import MONTHS
from wagtail.admin.forms import WagtailAdminModelForm
from wagtail.admin.widgets import AdminDateInput

from plants.models import Family, Species, Collection, GardenArea, BloomEvent


class CollectionSearchForm(forms.Form):
    scientific_name = forms.CharField(max_length=100, required=False)
    common_name = forms.CharField(max_length=150, required=False)
    family_name = forms.ChoiceField(choices=[], required=False)
    garden_name = forms.ChoiceField(choices=[], required=False)
    habits = forms.ChoiceField(choices=[], required=False)
    exposures = forms.ChoiceField(choices=[], required=False)
    water_needs = forms.ChoiceField(choices=[], required=False)
    bloom_months = forms.ChoiceField(choices=[], required=False)
    flower_colors = forms.ChoiceField(choices=[], required=False)
    memorial_person = forms.ChoiceField(choices=[], required=False)

    utah_native = forms.BooleanField(required=False)
    plant_select = forms.BooleanField(required=False)
    deer_resistant = forms.BooleanField(required=False)
    rabbit_resistant = forms.BooleanField(required=False)
    bee_friendly = forms.BooleanField(required=False)
    high_elevation = forms.BooleanField(required=False)
    available_memorial = forms.BooleanField(required=False)

    field_order = [
        "scientific_name",
        "common_name",
        "family_name",
        "garden_name",
        "habits",
        "exposures",
        "water_needs",
        "bloom_months",
        "flower_colors",
        "memorial_person",
        "utah_native",
        "plant_select",
        "deer_resistant",
        "rabbit_resistant",
        "bee_friendly",
        "high_elevation",
        "available_memorial",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        family_choices = [
            (str(f["id"]), f["name"]) for f in Family.objects.values("id", "name")
        ]
        garden_name_choices = [
            (g["name"], g["name"]) for g in GardenArea.objects.values("name").distinct()
        ]
        habit_choices = [
            (s["habit"], s["habit"])
            for s in Species.objects.order_by("habit").values("habit").distinct()
            if s["habit"]
        ]
        exposure_choices = [
            (s["exposure"], s["exposure"])
            for s in Species.objects.order_by("exposure").values("exposure").distinct()
            if s["exposure"]
        ]
        water_need_choices = [
            (s["water_regime"], s["water_regime"])
            for s in Species.objects.order_by("water_regime")
            .values("water_regime")
            .distinct()
            if s["water_regime"]
        ]
        bloom_month_choices = [(v, v) for _, v in MONTHS.items()]

        flower_colors_split = [
            s["flower_color"].split(",")
            for s in Species.objects.order_by("flower_color")
            .values("flower_color")
            .distinct()
            if s["flower_color"]
        ]
        flower_colors_split = [
            (c.strip(), c.strip())
            for colors in flower_colors_split
            for c in colors
            if c.strip()
        ]
        flower_color_choices = sorted(list(OrderedDict.fromkeys(flower_colors_split)))

        commemoration_people_choices = [
            (c["commemoration_person"], c["commemoration_person"])
            for c in Collection.objects.order_by("commemoration_person")
            .values("commemoration_person")
            .distinct()
            if c["commemoration_person"]
        ]

        # IMPORTANT: use "" as the empty value for ChoiceField
        def with_empty(choices):
            return [("", "")] + choices

        self.fields["family_name"].choices = with_empty(family_choices)
        self.fields["garden_name"].choices = with_empty(garden_name_choices)
        self.fields["habits"].choices = with_empty(habit_choices)
        self.fields["exposures"].choices = with_empty(exposure_choices)
        self.fields["water_needs"].choices = with_empty(water_need_choices)
        self.fields["bloom_months"].choices = with_empty(bloom_month_choices)
        self.fields["flower_colors"].choices = with_empty(flower_color_choices)
        self.fields["memorial_person"].choices = with_empty(
            commemoration_people_choices
        )

        for visible in self.visible_fields():
            if not isinstance(visible.field.widget, CheckboxInput):
                visible.field.widget.attrs["class"] = "form-control"

    def to_query_params(self) -> dict:
        """
        Produce a querystring-safe dict:
        - drop empty strings and None
        - drop False booleans (unchecked)
        """
        params = {}
        for k, v in self.cleaned_data.items():
            if v in ("", None, False):
                continue
            params[k] = v
        return params


class FeedbackReportForm(forms.Form):
    """
    Form used to report problems with a particular Species or Collection.
    """

    species_or_collection_object = forms.ModelChoiceField(
        queryset=Collection.objects.none(), disabled=True, empty_label=None
    )
    subject = forms.CharField(
        max_length=100, widget=forms.TextInput(attrs={"placeholder": "Subject"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"placeholder": "Your feedback"})
    )
    sender = forms.EmailField(
        required=False,
        widget=forms.TextInput(attrs={"placeholder": "Your email address - Optional!"}),
    )
    cc_myself = forms.BooleanField(required=False, label="CC Me")

    def __init__(self, species_id, collection_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if species_id:
            self.fields["species_or_collection_object"].queryset = (
                Species.objects.filter(id=species_id)
            )
            self.fields["species_or_collection_object"].initial = species_id
        elif collection_id:
            self.fields["species_or_collection_object"].queryset = (
                Collection.objects.filter(id=collection_id)
            )
            self.fields["species_or_collection_object"].initial = collection_id
        else:
            raise forms.ValidationError("Missing ID to Species or Collection")

        for visible in self.visible_fields():
            if isinstance(visible.field.widget, CheckboxInput):
                pass
            else:
                visible.field.widget.attrs["class"] = "form-control"


class BloomEventSnippetForm(forms.ModelForm):
    """
    Form used to create a Bloom Event.
    """

    class Meta:
        model = BloomEvent
        fields = "__all__"

        widgets = {
            "bloom_start": AdminDateInput(),
            "bloom_end": AdminDateInput(),
        }

    class Media:
        js = ["admin/js/bloom_event_collection_qs.js"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        species_id = None
        if self.data and "species" in self.data:
            species_id = self.data.get("species")
        elif self.instance and self.instance.pk:
            species_id = self.instance.species_id

        if species_id:
            self.fields["collections"].queryset = Collection.objects.filter(
                species=species_id
            ).order_by("plant_id")
        else:
            self.fields["collections"].queryset = Collection.objects.all()
