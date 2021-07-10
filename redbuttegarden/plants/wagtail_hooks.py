from wagtail.contrib.modeladmin.options import (
    ModelAdmin, modeladmin_register, ModelAdminGroup)
from .models import Collection, Species


class SpeciesAdmin(ModelAdmin):
    model = Species
    menu_label = 'Species'  # ditch this to use verbose_name_plural from model
    menu_icon = 'pilcrow'  # change as required
    list_display = ('genus', 'name')
    list_filter = ('genus',)
    search_fields = ('genus__family__name', 'genus__name', 'name', 'cultivar', 'vernacular_name')
    ordering = ('-genus', 'name')


class CollectionsAdmin(ModelAdmin):
    model = Collection
    menu_label = 'Collections'
    menu_icon = 'pilcrow'
    list_display = ('species',)
    list_filter = ('species',)
    search_fields = ('species',)


class PlantGroup(ModelAdminGroup):
    menu_label = 'Plants'
    menu_icon = 'folder-open-inverse'  # change as required
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (SpeciesAdmin, CollectionsAdmin)

# Now you just need to register your customised ModelAdmin class with Wagtail
modeladmin_register(PlantGroup)
