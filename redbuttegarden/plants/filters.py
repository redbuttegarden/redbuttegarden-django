import django_filters
from django import forms
from django.http import QueryDict
from django.contrib.postgres.search import SearchQuery, SearchVector

from .models import Collection, Species


TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}


class CollectionFilter(django_filters.FilterSet):
    """
    Backward/forward compatible FilterSet.

    Canonical keys (list page / old URLs):
      - plant_id, species_full_name, garden_name, garden_area, garden_code

    Aliases accepted (search form / map / legacy):
      - scientific_name -> species_full_name
      - common_name -> common_name (method)
      - family_name -> family_name (id)
      - habits -> habits, exposures -> exposures, water_needs -> water_needs
      - bloom_months -> bloom_months, flower_colors -> flower_colors
      - memorial_person -> memorial_person
      - plus boolean checkboxes (utah_native, etc.)
    """

    # ---------- Canonical list filters ----------
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
        widget=forms.TextInput(attrs={"placeholder": "GWL"}),
    )

    # ---------- Additional fields (from search form) ----------
    common_name = django_filters.CharFilter(
        method="filter_common_name", label="Common name"
    )

    family_name = django_filters.NumberFilter(
        field_name="species__genus__family_id", label="Family"
    )

    habits = django_filters.CharFilter(
        field_name="species__habit", lookup_expr="iexact", label="Habit"
    )
    exposures = django_filters.CharFilter(
        field_name="species__exposure", lookup_expr="iexact", label="Exposure"
    )
    water_needs = django_filters.CharFilter(
        field_name="species__water_regime", lookup_expr="iexact", label="Water needs"
    )

    bloom_months = django_filters.CharFilter(
        method="filter_bloom_month", label="Bloom month"
    )
    flower_colors = django_filters.CharFilter(
        field_name="species__flower_color",
        lookup_expr="icontains",
        label="Flower color",
    )

    memorial_person = django_filters.CharFilter(
        field_name="commemoration_person", lookup_expr="iexact", label="Memorial person"
    )

    utah_native = django_filters.BooleanFilter(
        method="filter_truthy",
        field_name="species__utah_native",
        widget=forms.CheckboxInput(),
        label="Utah native",
    )
    plant_select = django_filters.BooleanFilter(
        method="filter_truthy",
        field_name="species__plant_select",
        widget=forms.CheckboxInput(),
        label="Plant Select",
    )
    deer_resistant = django_filters.BooleanFilter(
        method="filter_truthy",
        field_name="species__deer_resist",
        widget=forms.CheckboxInput(),
        label="Deer resistant",
    )
    rabbit_resistant = django_filters.BooleanFilter(
        method="filter_truthy",
        field_name="species__rabbit_resist",
        widget=forms.CheckboxInput(),
        label="Rabbit resistant",
    )
    bee_friendly = django_filters.BooleanFilter(
        method="filter_truthy",
        field_name="species__bee_friend",
        widget=forms.CheckboxInput(),
        label="Bee friendly",
    )
    high_elevation = django_filters.BooleanFilter(
        method="filter_truthy",
        field_name="species__high_elevation",
        widget=forms.CheckboxInput(),
        label="High elevation",
    )

    available_memorial = django_filters.BooleanFilter(
        method="filter_available_memorial",
        widget=forms.CheckboxInput(),
        label="Available memorial",
    )

    # ---------- Aliases: accept other param names without duplicating logic ----------
    # NOTE: these are *query-param aliases*, not separate UI filters.
    PARAM_ALIASES = {
        # search-form / map keys -> canonical list keys
        "scientific_name": "species_full_name",
        # optional: if you ever used these variants elsewhere
        "species": "species_full_name",
        "q": "species_full_name",
    }

    class Meta:
        model = Collection
        fields = [
            # canonical list keys
            "plant_id",
            "species_full_name",
            "garden_name",
            "garden_area",
            "garden_code",
            # search-form keys
            "common_name",
            "family_name",
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

    def __init__(self, data=None, *args, **kwargs):
        # Remap aliases in GET params to canonical keys before django-filter parses them.
        data = self._canonicalize_querydict(data)
        super().__init__(data=data, *args, **kwargs)

        for field in self.form.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                existing = widget.attrs.get("class", "")
                if "form-check-input" not in existing:
                    widget.attrs["class"] = (existing + " form-check-input").strip()
                continue

            existing = widget.attrs.get("class", "")
            if "form-control" not in existing:
                widget.attrs["class"] = (existing + " form-control").strip()

    def _canonicalize_querydict(self, data):
        """
        Accept alternate param names but normalize them to canonical keys.
        If both are present, the canonical key wins.
        """
        if not data:
            return data

        # Works for QueryDict and dict-like
        if isinstance(data, QueryDict):
            qd = data.copy()
        else:
            qd = QueryDict(mutable=True)
            for k, v in dict(data).items():
                if isinstance(v, (list, tuple)):
                    for item in v:
                        qd.appendlist(k, item)
                else:
                    qd[k] = v

        for alias, canonical in self.PARAM_ALIASES.items():
            if canonical in qd:
                continue
            if alias in qd:
                # preserve multiple values if provided
                for v in qd.getlist(alias):
                    qd.appendlist(canonical, v)
        return qd

    # ---------- Methods ----------
    def filter_plant_id_contains(self, queryset, name, value):
        if not value:
            return queryset
        return queryset.filter(plant_id__icontains=value)

    def filter_common_name(self, qs, name, value):
        if not value:
            return qs
        vector = SearchVector("species__cultivar", "species__vernacular_name")
        query = SearchQuery(value)
        return qs.annotate(_search=vector).filter(_search=query)

    def filter_bloom_month(self, qs, name, value):
        if not value:
            return qs
        mods = ["Early", "Mid", "Late"]
        month_tokens = [" ".join([mod, value]) for mod in mods] + [value]
        return qs.filter(species__bloom_time__overlap=month_tokens)

    def filter_truthy(self, qs, field_name, value):
        # checkbox semantics: if present/truthy => True
        if value in (None, "", False):
            return qs
        if isinstance(value, str):
            value = value.strip().lower() in TRUE_VALUES
        return qs.filter(**{field_name: bool(value)})

    def filter_available_memorial(self, qs, name, value):
        if value in (None, "", False):
            return qs
        if isinstance(value, str):
            value = value.strip().lower() in TRUE_VALUES
        return qs.filter(commemoration_category="Available") if value else qs


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
