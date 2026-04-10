from django import forms
from django.contrib.admin.utils import quote
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import redirect
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.utils.decorators import method_decorator
from django.views import View
from wagtail.admin.auth import require_admin_access
from wagtail.admin.forms.choosers import BaseFilterForm
from wagtail.admin.ui.tables import Column, TitleColumn
from wagtail.snippets.views.chooser import (
    ChooseResultsView as SnippetChooseResultsView,
    ChooseView as SnippetChooseView,
    SnippetChooserViewSet,
    SnippetChosenView,
)

from .models import Collection, Species
from .species_autolinks import SpeciesAutoLinker


class SpeciesLinkChooserFilterForm(BaseFilterForm):
    q = forms.CharField(
        label=_("Search term"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Search species")}),
    )

    def filter(self, objects):
        objects = super().filter(objects)
        search_query = self.cleaned_data.get("q")
        if search_query:
            objects = objects.filter(
                Q(full_name__icontains=search_query)
                | Q(vernacular_name__icontains=search_query)
                | Q(genus__name__icontains=search_query)
                | Q(genus__family__name__icontains=search_query)
                | Q(autolink_aliases__icontains=search_query)
            ).distinct()
            self.is_searching = True
            self.search_query = search_query
        return objects


class CollectionLinkChooserFilterForm(BaseFilterForm):
    q = forms.CharField(
        label=_("Search term"),
        required=False,
        widget=forms.TextInput(attrs={"placeholder": _("Search collections")}),
    )

    def filter(self, objects):
        objects = super().filter(objects)
        search_query = self.cleaned_data.get("q")
        if search_query:
            objects = objects.filter(
                Q(plant_id__icontains=search_query)
                | Q(species__full_name__icontains=search_query)
                | Q(species__vernacular_name__icontains=search_query)
                | Q(garden__area__icontains=search_query)
                | Q(garden__name__icontains=search_query)
                | Q(garden__code__icontains=search_query)
            ).distinct()
            self.is_searching = True
            self.search_query = search_query
        return objects


class RichTextLinkChooserContextMixin:
    template_name = "plants/wagtailadmin/chooser/link_chooser.html"
    step_name = None

    def is_modal_request(self):
        return self.request.headers.get("x-requested-with") == "XMLHttpRequest"

    @property
    def preserved_link_chooser_query(self):
        return {
            "parent_page_id": self.request.GET.get("parent_page_id"),
            "allow_external_link": self.request.GET.get("allow_external_link"),
            "allow_email_link": self.request.GET.get("allow_email_link"),
            "allow_phone_link": self.request.GET.get("allow_phone_link"),
            "allow_anchor_link": self.request.GET.get("allow_anchor_link"),
        }

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(self.preserved_link_chooser_query)
        return context

    def get_response_json_data(self):
        return {
            "step": self.step_name,
        }

    def render_to_response(self):
        if self.is_modal_request():
            return super().render_to_response()
        return TemplateResponse(
            self.request,
            self.template_name,
            self.get_context_data(),
        )


class SpeciesLinkChooseView(RichTextLinkChooserContextMixin, SnippetChooseView):
    current = "species"
    step_name = "species_link_choose"
    filter_form_class = SpeciesLinkChooserFilterForm
    ordering = ("full_name",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current"] = self.current
        return context


class SpeciesLinkChooseResultsView(SnippetChooseResultsView):
    filter_form_class = SpeciesLinkChooserFilterForm
    ordering = ("full_name",)


class CollectionLinkChooseView(RichTextLinkChooserContextMixin, SnippetChooseView):
    current = "collection"
    step_name = "collection_link_choose"
    filter_form_class = CollectionLinkChooserFilterForm
    ordering = ("plant_id",)

    @property
    def title_column(self):
        return TitleColumn(
            "title",
            label=_("Collection"),
            accessor=lambda obj: obj.get_rich_text_link_title(),
            get_url=(
                lambda obj: self.append_preserved_url_parameters(
                    reverse(self.chosen_url_name, args=(quote(obj.pk),))
                )
            ),
            link_attrs={"data-chooser-modal-choice": True},
        )

    @property
    def columns(self):
        return [
            self.title_column,
            Column("species", label=_("Species"), accessor="species.full_name"),
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current"] = self.current
        return context


class CollectionLinkChooseResultsView(SnippetChooseResultsView):
    filter_form_class = CollectionLinkChooserFilterForm
    ordering = ("plant_id",)

    @property
    def title_column(self):
        return TitleColumn(
            "title",
            label=_("Collection"),
            accessor=lambda obj: obj.get_rich_text_link_title(),
            get_url=(
                lambda obj: self.append_preserved_url_parameters(
                    reverse(self.chosen_url_name, args=(quote(obj.pk),))
                )
            ),
            link_attrs={"data-chooser-modal-choice": True},
        )

    @property
    def columns(self):
        return [
            self.title_column,
            Column("species", label=_("Species"), accessor="species.full_name"),
        ]


class RichTextLinkChosenView(SnippetChosenView):
    chosen_response_name = "page_chosen"
    response_data_title_key = "title"
    link_type = None

    def get_display_title(self, instance):
        return instance.get_rich_text_link_title()

    def get_chosen_response_data(self, item):
        response_data = {
            "id": item.pk,
            "parentId": None,
            "url": item.get_absolute_url(),
            self.response_data_title_key: self.get_display_title(item),
        }
        if self.link_type:
            response_data["linkType"] = self.link_type
        return response_data

    def get_chosen_response(self, item):
        if self.request.headers.get("x-requested-with") != "XMLHttpRequest":
            return redirect(item.get_absolute_url())
        return super().get_chosen_response(item)


class SpeciesLinkChosenView(RichTextLinkChosenView):
    link_type = "species"


class CollectionLinkChosenView(RichTextLinkChosenView):
    link_type = "collection"


class SpeciesAutolinkTermsView(View):
    @method_decorator(require_admin_access)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return JsonResponse(
            {
                "terms": sorted(
                    SpeciesAutoLinker.get_unique_matches_from_database().keys(),
                    key=len,
                    reverse=True,
                )
            }
        )


class SpeciesLinkChooserViewSet(SnippetChooserViewSet):
    name = "species_link_chooser"
    model = Species
    icon = "link"
    page_title = _("Choose a species link")
    choose_view_class = SpeciesLinkChooseView
    choose_results_view_class = SpeciesLinkChooseResultsView
    chosen_view_class = SpeciesLinkChosenView
    preserve_url_parameters = [
        "multiple",
        "parent_page_id",
        "allow_external_link",
        "allow_email_link",
        "allow_phone_link",
        "allow_anchor_link",
    ]
    register_widget = False

    def get_object_list(self):
        return self.model.objects.select_related("genus__family")


class CollectionLinkChooserViewSet(SnippetChooserViewSet):
    name = "collection_link_chooser"
    model = Collection
    icon = "link"
    page_title = _("Choose a plant collection link")
    choose_view_class = CollectionLinkChooseView
    choose_results_view_class = CollectionLinkChooseResultsView
    chosen_view_class = CollectionLinkChosenView
    preserve_url_parameters = [
        "multiple",
        "parent_page_id",
        "allow_external_link",
        "allow_email_link",
        "allow_phone_link",
        "allow_anchor_link",
    ]
    register_widget = False

    def get_object_list(self):
        return self.model.objects.select_related("species__genus__family", "garden")
