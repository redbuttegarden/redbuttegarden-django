import django_filters
from django import forms
from .models import Collection, Species


class CollectionFilter(django_filters.FilterSet):
    plant_id = django_filters.CharFilter(
        method="filter_plant_id_contains",
        label="Plant ID contains",
        widget=forms.TextInput(attrs={"placeholder": "e.g. 2025"}),
    )
    species_full_name = django_filters.CharFilter(
        field_name="species__full_name",
        lookup_expr="icontains",
        label="Scientific name",
        widget=forms.TextInput(attrs={"placeholder": "Acer rubrum"}),
    )
    garden_name = django_filters.CharFilter(
        field_name="garden__name",
        lookup_expr="icontains",
        label="Garden name",
        widget=forms.TextInput(attrs={"placeholder": "Courtyard"}),
    )
    garden_area = django_filters.CharFilter(
        field_name="garden__area",
        lookup_expr="icontains",
        label="Garden area",
        widget=forms.TextInput(attrs={"placeholder": "Wedding Lawn"}),
    )
    garden_code = django_filters.CharFilter(
        field_name="garden__code",
        lookup_expr="icontains",
        label="Garden code",
        widget=forms.TextInput(attrs={"placeholder": "Great Wall"}),
    )

    class Meta:
        model = Collection
        # only expose the fields you want to accept in GET params (helps form rendering)
        fields = [
            "plant_id",
            "species_full_name",
            "garden_name",
            "garden_area",
            "garden_code",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add bootstrap classes to all widgets
        for name, field in self.form.fields.items():
            widget = field.widget
            if hasattr(widget, "attrs"):
                existing = widget.attrs.get("class", "")
                if "form-control" not in existing:
                    widget.attrs["class"] = (existing + " form-control").strip()

    def filter_plant_id_contains(self, queryset, name, value):
        # allow searching the string representation of the pk (helpful if users type fragments)
        if not value:
            return queryset
        # if value is digits, keep both exact and contains matches
        try:
            int(value)
            return queryset.filter(plant_id__icontains=value)
        except Exception:
            # fallback to no-op
            return queryset.none()


class TopTreesSpeciesFilter(django_filters.FilterSet):
    # allow filtering by full name (scientific), common name, and habit (example)
    full_name = django_filters.CharFilter(
        field_name="full_name", lookup_expr="icontains", label="Scientific name"
    )
    vernacular_name = django_filters.CharFilter(
        field_name="vernacular_name", lookup_expr="icontains", label="Common name"
    )
    habit = django_filters.CharFilter(
        field_name="habit", lookup_expr="icontains", label="Habit"
    )

    class Meta:
        model = Species
        # these must match model fields or properties that can be used in ORM filters
        fields = ["full_name", "vernacular_name", "habit"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.form.fields.items():
            widget = field.widget
            if hasattr(widget, "attrs"):
                widget.attrs.setdefault("class", "")
                if "form-control" not in widget.attrs["class"]:
                    widget.attrs["class"] += " form-control"
