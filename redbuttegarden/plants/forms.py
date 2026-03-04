from django import forms
from django.forms import CheckboxInput
from django.utils.dates import MONTHS
from wagtail.admin.widgets import AdminDateInput

from plants.models import Species, Collection, BloomEvent


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
