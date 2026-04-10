from django.utils.html import format_html
from django.urls import path
from wagtail import hooks
from wagtail.admin.rich_text.converters.editor_html import LinkTypeRule
from wagtail.admin.rich_text.editors.draftail import features as draftail_features
from wagtail.rich_text import features as rich_text_features_registry
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from django.urls import reverse_lazy

from .chooser import (
    CollectionLinkChooserViewSet,
    SpeciesAutolinkTermsView,
    SpeciesLinkChooserViewSet,
)
from .forms import BloomEventSnippetForm
from .models import Collection, Species, Genus, Family, BloomEvent
from .rich_text import (
    CollectionEditorHTMLLinkHandler,
    CollectionLinkElementHandler,
    CollectionLinkHandler,
    SpeciesEditorHTMLLinkHandler,
    SpeciesLinkElementHandler,
    SpeciesLinkHandler,
    plant_link_entity,
)

class FamilyAdmin(SnippetViewSet):
    model = Family
    menu_label = 'Family'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    list_display = ('name', 'vernacular_name')
    search_fields = ('name', 'vernacular_name')


class GenusAdmin(SnippetViewSet):
    model = Genus
    menu_label = 'Genus'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    list_display = ('family', 'name')
    list_filter = ('family',)
    search_fields = ('family__name', 'name')
    ordering = ('family', 'name')

    def get_queryset(self, request):
        qs = self.model._default_manager.select_related(
            'family'
        )

        return qs


class SpeciesAdmin(SnippetViewSet):
    model = Species
    menu_label = 'Species'  # ditch this to use verbose_name_plural from model
    menu_icon = 'tag'  # change as required
    list_display = ('genus', 'name', 'cultivar', 'autolink_enabled')
    list_filter = ('genus',)
    search_fields = ('genus__family__name', 'genus__name', 'name', 'cultivar', 'vernacular_name', 'autolink_aliases')
    ordering = ('genus', 'name')

    def get_queryset(self, request):
        qs = self.model._default_manager.select_related(
            'genus__family'
        )

        return qs


class CollectionsAdmin(SnippetViewSet):
    model = Collection
    menu_label = 'Collections'
    menu_icon = 'tag'
    list_display = ('species', 'plant_id')
    list_filter = ('species__genus',)
    search_fields = ('species__genus__family__name', 'species__genus__name', 'species__name', 'plant_id',)
    ordering = ('species__genus',)

    def get_queryset(self, request):
        qs = self.model._default_manager.select_related(
            'species__genus__family'
        )

        return qs


class BloomEventAdmin(SnippetViewSet):
    model = BloomEvent
    menu_label = 'Blooms'  # ditch this to use verbose_name_plural from model
    menu_icon = 'calendar'  # change as required
    list_display = ('title', 'bloom_start', 'bloom_end', 'species')
    list_filter = ('species__genus__family__name', 'species__genus__name', 'species__name')
    search_fields = ('title', 'description', 'species__genus__family__name', 'species__genus__name', 'species__name')

    def get_form_class(self, for_update=False):
        return BloomEventSnippetForm


class PlantGroup(SnippetViewSetGroup):
    menu_label = 'Plants'
    menu_icon = 'snippet'
    menu_order = 200  # will put in 3rd place (000 being 1st, 100 2nd)
    items = (FamilyAdmin, GenusAdmin, SpeciesAdmin, CollectionsAdmin, BloomEventAdmin)


species_link_chooser_viewset = SpeciesLinkChooserViewSet()
collection_link_chooser_viewset = CollectionLinkChooserViewSet()


@hooks.register("register_admin_viewset")
def register_species_link_chooser_viewset():
    return species_link_chooser_viewset


@hooks.register("register_admin_viewset")
def register_collection_link_chooser_viewset():
    return collection_link_chooser_viewset


@hooks.register("register_admin_urls")
def register_species_autolink_admin_urls():
    return [
        path(
            "species-autolink-terms/",
            SpeciesAutolinkTermsView.as_view(),
            name="species_autolink_terms",
        ),
    ]


def _register_plant_link_features(features):
    features.register_link_type(SpeciesLinkHandler)
    features.register_link_type(CollectionLinkHandler)
    features.register_converter_rule(
        "editorhtml",
        "plant-links",
        [
            LinkTypeRule("species", SpeciesEditorHTMLLinkHandler),
            LinkTypeRule("collection", CollectionEditorHTMLLinkHandler),
        ],
    )
    if "plant-links" not in features.default_features:
        features.default_features.append("plant-links")
    features.register_editor_plugin(
        "draftail",
        "plant-links",
        draftail_features.PluginFeature({}),
    )
    features.register_editor_plugin(
        "draftail",
        "link",
        draftail_features.EntityFeature(
        {
            "type": "LINK",
            "icon": "link",
            "description": "Link",
            "attributes": ["url", "id", "parentId", "linkType"],
            "allowlist": {
                "href": "^(http:|https:|undefined$)",
            },
                "chooserUrls": {
                    "pageChooser": reverse_lazy("wagtailadmin_choose_page"),
                    "externalLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_external_link"
                    ),
                    "emailLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_email_link"
                    ),
                    "phoneLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_phone_link"
                    ),
                    "anchorLinkChooser": reverse_lazy(
                        "wagtailadmin_choose_page_anchor_link"
                    ),
                    "speciesChooser": reverse_lazy("species_link_chooser:choose"),
                    "collectionChooser": reverse_lazy("collection_link_chooser:choose"),
                },
            },
            js=[
                "wagtailadmin/js/page-chooser-modal.js",
            ],
        ),
    )
    features.register_converter_rule(
        "contentstate",
        "plant-links",
        {
            "from_database_format": {
                'a[linktype="species"]': SpeciesLinkElementHandler("LINK"),
                'a[linktype="collection"]': CollectionLinkElementHandler("LINK"),
            },
            "to_database_format": {"entity_decorators": {"LINK": plant_link_entity}},
        },
    )


@hooks.register("register_rich_text_features")
def register_plant_link_features(features):
    _register_plant_link_features(features)


if rich_text_features_registry.has_scanned_for_features:
    _register_plant_link_features(rich_text_features_registry)


@hooks.register("insert_global_admin_js")
def include_rich_text_link_chooser_js():
    return format_html(
        '<script src="{}"></script>',
        "/static/plants/js/rich_text_link_chooser_modal.js",
    )


# Now you just need to register your customised ModelAdmin class with Wagtail
register_snippet(PlantGroup)
