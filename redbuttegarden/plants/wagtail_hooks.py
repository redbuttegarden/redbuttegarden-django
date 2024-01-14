from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register, ModelAdminGroup)

from .models import Collection, Species, Genus, Family

class FamilyAdmin(ModelAdmin):
    model = Family
    menu_label = 'Family'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    list_display = ('name', 'vernacular_name')
    search_fields = ('name', 'vernacular_name')


class GenusAdmin(ModelAdmin):
    model = Genus
    menu_label = 'Genus'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    list_display = ('family', 'name')
    list_filter = ('family',)
    search_fields = ('family__name', 'name')
    ordering = ('family', 'name')

    def get_queryset(self, request):
        qs = self.model._default_manager.select_related(
            'family'
        )
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        return qs


class SpeciesAdmin(ModelAdmin):
    model = Species
    menu_label = 'Species'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    list_display = ('genus', 'name', 'cultivar')
    list_filter = ('genus',)
    search_fields = ('genus__family__name', 'genus__name', 'name', 'cultivar', 'vernacular_name')
    ordering = ('genus', 'name')

    def get_queryset(self, request):
        qs = self.model._default_manager.select_related(
            'genus__family'
        )
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        return qs


class CollectionsAdmin(ModelAdmin):
    model = Collection
    menu_label = 'Collections'
    menu_icon = 'pilcrow'
    list_display = ('species', 'plant_id')
    list_filter = ('species__genus',)
    search_fields = ('species__genus__family__name', 'species__genus__name', 'species__name', 'plant_id',)
    ordering = ('species__genus',)

    def get_queryset(self, request):
        qs = self.model._default_manager.select_related(
            'species__genus__family'
        )
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)

        return qs


class PlantGroup(ModelAdminGroup):
    menu_label = 'Plants'
    menu_icon = 'snippet'
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (FamilyAdmin, GenusAdmin, SpeciesAdmin, CollectionsAdmin)

# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(PlantGroup)
