from collections import OrderedDict

from django import forms
from django.forms import CheckboxInput
from django.utils.dates import MONTHS

from plants.models import Family, Species, Collection, GardenArea


class CollectionSearchForm(forms.Form):
    family_choices = [(family['id'], family['name']) for family in Family.objects.values('id', 'name')]
    garden_area_choices = [(garden['id'], garden['name']) for garden in GardenArea.objects.values('id', 'name').distinct('name')]
    habit_choices = [(species['habit'], species['habit']) for species in
              Species.objects.order_by('habit').values('habit').distinct('habit')]
    exposure_choices = [(species['exposure'], species['exposure']) for species in
                 Species.objects.order_by('exposure').values('exposure').distinct('exposure')
                 if species['exposure'] is not '' and species['exposure'] is not None]
    water_need_choices = [(species['water_regime'], species['water_regime']) for species in
                   Species.objects.order_by('water_regime').values('water_regime').distinct('water_regime')]
    bloom_month_choices = [(v, v) for _, v in MONTHS.items()]
    # Flower color list of lists
    flower_colors_split = [species['flower_color'].split(',') for species in
                     Species.objects.order_by('flower_color').values('flower_color').distinct('flower_color')
                     if species['flower_color'] is not '' and species['flower_color'] is not None]
    flower_colors_split = [(color.strip(), color.strip()) for colors in flower_colors_split for color in colors]  # Flattens list of lists
    flower_color_choices = sorted(list(OrderedDict.fromkeys(flower_colors_split)))  # Removes duplicates
    commemoration_people_choices = [(collection['commemoration_person'], collection['commemoration_person']) for collection in
                            Collection.objects.order_by('commemoration_person').values('commemoration_person').distinct('commemoration_person')
                            if collection['commemoration_person'] is not ''
                            and collection['commemoration_person'] is not None]

    # Insert empty choice to lists that don't already have an empty option
    family_choices.insert(0, (None, ''))
    garden_area_choices.insert(0, (None, ''))
    habit_choices.insert(0, (None, ''))
    exposure_choices.insert(0, (None, ''))
    water_need_choices.insert(0, (None, ''))
    bloom_month_choices.insert(0, (None, ''))
    flower_color_choices.insert(0, (None, ''))
    commemoration_people_choices.insert(0, (None, ''))

    scientific_name = forms.CharField(max_length=100, required=False)
    common_name = forms.CharField(max_length=150, required=False)
    family_name = forms.ChoiceField(choices=family_choices, required=False)
    garden_area = forms.ChoiceField(choices=garden_area_choices, required=False)
    habits = forms.ChoiceField(choices=habit_choices, required=False)
    exposures = forms.ChoiceField(choices=exposure_choices, required=False)
    water_needs = forms.ChoiceField(choices=water_need_choices, required=False)
    bloom_months = forms.ChoiceField(choices=bloom_month_choices, required=False)
    flower_colors = forms.ChoiceField(choices=flower_color_choices, required=False)
    memorial_person = forms.ChoiceField(choices=commemoration_people_choices, required=False)
    utah_native = forms.BooleanField(required=False)
    plant_select = forms.BooleanField(required=False)
    deer_resistant = forms.BooleanField(required=False)
    rabbit_resistant = forms.BooleanField(required=False)
    bee_friendly = forms.BooleanField(required=False)
    high_elevation = forms.BooleanField(required=False)
    available_memorial = forms.BooleanField(required=False)

    field_order = ['scientific_name',
                   'common_name',
                   'family_name',
                   'garden_area',
                   'habits',
                   'exposures',
                   'water_needs',
                   'bloom_months',
                   'flower_colors',
                   'memorial_person',
                   'utah_native',
                   'plant_select',
                   'deer_resistant',
                   'rabbit_resistant',
                   'bee_friendly',
                   'high_elevation',
                   'available_memorial']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            if isinstance(visible.field.widget, CheckboxInput):
                pass
            else:
                visible.field.widget.attrs['class'] = 'form-control'


class FeedbackReportForm(forms.Form):
    """
    Form used to report problems with a particular Species or Collection.
    """
    species_or_collection_object = forms.ModelChoiceField(queryset=Collection.objects.none(), disabled=True,
                                                          empty_label=None)
    subject = forms.CharField(max_length=100)
    message = forms.CharField(widget=forms.Textarea)
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)

    def __init__(self, species_id, collection_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if species_id:
            self.fields['species_or_collection_object'].queryset = Species.objects.filter(id=species_id)
            self.fields['species_or_collection_object'].initial = species_id
        elif collection_id:
            self.fields['species_or_collection_object'].queryset = Collection.objects.filter(id=collection_id)
            self.fields['species_or_collection_object'].initial = collection_id
        else:
            raise forms.ValidationError('Missing ID to Species or Collection')

        for visible in self.visible_fields():
            if isinstance(visible.field.widget, CheckboxInput):
                pass
            else:
                visible.field.widget.attrs['class'] = 'form-control'
