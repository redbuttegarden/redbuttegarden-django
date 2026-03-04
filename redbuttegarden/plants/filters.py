from collections import OrderedDict

import django_filters
from django import forms
from django.http import QueryDict
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.utils.dates import MONTHS

from .models import Collection, Species, GardenArea, Family


TRUE_VALUES = {"1", "true", "t", "yes", "y", "on"}


class CollectionFilter(django_filters.FilterSet):
    """
    Backward/forward compatible FilterSet.

    Canonical keys (list page / old URLs):
      - plant_id, species_full_name, garden_name, garden_area, garden_code

    Aliases accepted (search form / map / legacy):
      - scientific_name -> species_full_name
      - common_name -> common_name (method)
      - plus boolean checkboxes (utah_native, etc.)
    """

    # ---------- Canonical list filters ----------
    plant_id = django_filters.CharFilter(
        method="filter_plant_id_contains",
        label="Plant ID contains",
        widget=forms.TextInput(),
    )

    species_full_name = django_filters.CharFilter(
        field_name="species__full_name",
        lookup_expr="icontains",
        label="Scientific name",
        widget=forms.TextInput(),
    )

    garden_area = django_filters.CharFilter(
        field_name="garden__area",
        lookup_expr="icontains",
        label="Garden area",
        widget=forms.TextInput(),
    )

    garden_code = django_filters.CharFilter(
        field_name="garden__code",
        lookup_expr="icontains",
        label="Garden code",
        widget=forms.TextInput(),
    )

    common_name = django_filters.CharFilter(
        method="filter_common_name", label="Common name"
    )

    # ---------- Choice-based filters (populated from DB in __init__) ----------
    family_name = django_filters.TypedChoiceFilter(
        field_name="species__genus__family_id",
        label="Family",
        choices=[],
        coerce=int,
        empty_value=None,
    )

    garden_name = django_filters.ChoiceFilter(
        field_name="garden__name",
        label="Garden name",
        choices=[],
        lookup_expr="iexact",
    )

    habits = django_filters.ChoiceFilter(
        field_name="species__habit",
        label="Habit",
        choices=[],
        lookup_expr="iexact",
    )

    exposures = django_filters.ChoiceFilter(
        field_name="species__exposure",
        label="Exposure",
        choices=[],
        lookup_expr="iexact",
    )

    water_needs = django_filters.ChoiceFilter(
        field_name="species__water_regime",
        label="Water needs",
        choices=[],
        lookup_expr="iexact",
    )

    bloom_months = django_filters.ChoiceFilter(
        method="filter_bloom_month",
        label="Bloom month",
        choices=[],
    )

    flower_colors = django_filters.ChoiceFilter(
        field_name="species__flower_color",
        lookup_expr="icontains",
        label="Flower color",
        choices=[],
    )

    memorial_person = django_filters.ChoiceFilter(
        field_name="commemoration_person",
        lookup_expr="iexact",
        label="Memorial person",
        choices=[],
    )

    # ---------- Boolean filters ----------
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
    PARAM_ALIASES = {
        "scientific_name": "species_full_name",
        "species": "species_full_name",
        "q": "species_full_name",
    }

    class Meta:
        model = Collection
        fields = [
            "plant_id",
            "species_full_name",
            "garden_name",
            "garden_area",
            "garden_code",
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
        data = self._canonicalize_querydict(data)
        super().__init__(data=data, *args, **kwargs)

        def _set_empty_label(field, label="---------"):
            if hasattr(field, "empty_label"):
                field.empty_label = label
            else:
                # ChoiceField: ensure first choice is the placeholder
                choices = list(field.choices)
                if not choices or choices[0][0] != "":
                    field.choices = [("", label)] + choices

        # IMPORTANT: do NOT prepend ("", "") to choices.
        # Let Django render the default "---------" empty option consistently.

        # Families
        family_choices = Family.objects.order_by("name").values_list("id", "name")
        self.form.fields["family_name"].choices = [
            (fid, name) for fid, name in family_choices
        ]
        _set_empty_label(self.form.fields["family_name"])

        # Garden names
        garden_choices = (
            GardenArea.objects.order_by("name")
            .values_list("name", flat=True)
            .distinct()
        )
        self.form.fields["garden_name"].choices = [(g, g) for g in garden_choices if g]

        # Habit / exposure / water regime
        habit_choices = (
            Species.objects.order_by("habit").values_list("habit", flat=True).distinct()
        )
        self.form.fields["habits"].choices = [(h, h) for h in habit_choices if h]

        exposure_choices = (
            Species.objects.order_by("exposure")
            .values_list("exposure", flat=True)
            .distinct()
        )
        self.form.fields["exposures"].choices = [(e, e) for e in exposure_choices if e]

        water_choices = (
            Species.objects.order_by("water_regime")
            .values_list("water_regime", flat=True)
            .distinct()
        )
        self.form.fields["water_needs"].choices = [(w, w) for w in water_choices if w]

        # Bloom months
        self.form.fields["bloom_months"].choices = [(v, v) for _, v in MONTHS.items()]

        # Flower colors: split, strip, unique, sorted
        raw_colors = (
            Species.objects.order_by("flower_color")
            .values_list("flower_color", flat=True)
            .distinct()
        )
        split_colors = []
        for s in raw_colors:
            if not s:
                continue
            split_colors.extend([c.strip() for c in s.split(",") if c.strip()])

        unique_colors = sorted(list(OrderedDict.fromkeys(split_colors)))
        self.form.fields["flower_colors"].choices = [(c, c) for c in unique_colors]

        # Memorial people
        people = (
            Collection.objects.order_by("commemoration_person")
            .values_list("commemoration_person", flat=True)
            .distinct()
        )
        self.form.fields["memorial_person"].choices = [(p, p) for p in people if p]

        # Widget class tweaks
        for field in self.form.fields.values():
            widget = field.widget
            if isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = (
                    widget.attrs.get("class", "") + " form-check-input"
                ).strip()
            else:
                widget.attrs["class"] = (
                    widget.attrs.get("class", "") + " form-control"
                ).strip()

    def _canonicalize_querydict(self, data):
        """
        Accept alternate param names but normalize them to canonical keys.
        If both are present, the canonical key wins.
        """
        if not data:
            return data

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
