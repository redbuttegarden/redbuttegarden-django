import wagtail.admin.rich_text.editors.draftail.features as draftail_features
from django.http import HttpRequest, HttpResponse
from django.urls import reverse_lazy
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from wagtail.admin.rich_text.converters.html_to_contentstate import (
    InlineStyleElementHandler,
)
from wagtail import hooks
from wagtail.admin.menu import MenuItem
from wagtail.admin.userbar import BaseItem, ContentCheckerItem
from wagtail.models import Page
from wagtail.snippets.models import register_snippet

from home.views import RBGHoursViewSet


class RBGContentCheckerItem(ContentCheckerItem):
    """Extend Wagtail's native checker with a focused ambiguous-link rule."""

    def get_axe_run_only(self, request: HttpRequest) -> list[str]:
        """Return native rule IDs plus the RBG link-text rule."""

        return [*super().get_axe_run_only(request), "rbg-link-text-quality"]

    def get_axe_custom_rules(self, request: HttpRequest) -> list[dict]:
        """Return native Axe rules plus the RBG link selector."""

        return [
            *super().get_axe_custom_rules(request),
            {
                "id": "rbg-link-text-quality",
                "impact": "moderate",
                "selector": "a[href]",
                "tags": ["best-practice"],
                "any": ["check-rbg-link-text"],
                "enabled": True,
            },
        ]

    def get_axe_custom_checks(self, request: HttpRequest) -> list[dict]:
        """Return native checks plus exact ambiguous-link text options."""

        return [
            *super().get_axe_custom_checks(request),
            {
                "id": "check-rbg-link-text",
                "options": {
                    "antipattern": r"^(?:click here|here|more)$",
                },
            },
        ]

    def get_axe_messages(self, request: HttpRequest) -> dict:
        """Return native messages plus editorial guidance for ambiguous links."""

        return {
            **super().get_axe_messages(request),
            "rbg-link-text-quality": {
                "error_name": _("Ambiguous link text found"),
                "help_text": _("Describe where the link goes instead"),
            },
        }

    class Media:
        js = ("admin/js/rbg_content_checks.js",)


@hooks.register("construct_wagtail_userbar")
def customise_content_checker(
    request: HttpRequest,
    items: list[BaseItem],
    page: Page | None,
) -> None:
    """Replace Wagtail's checker while preserving editor-mode behavior."""

    items[:] = [
        RBGContentCheckerItem(in_editor=item.in_editor)
        if isinstance(item, ContentCheckerItem)
        else item
        for item in items
    ]


@hooks.register("insert_global_admin_js")
def include_sweetalert2():
    return format_html(
        """<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11.22.2/dist/sweetalert2.all.min.js" integrity="sha256-Ua8fKA4E1l7RSqT5HOjK0m/PrSwP41XFTs++qmtWey8=" crossorigin="anonymous"></script>"""
    )


@hooks.register("insert_global_admin_js")
def warn_on_pdf_upload():
    return format_html(
        '<script src="{}"></script>', "/static/admin/js/warn_pdf_upload.js"
    )


@hooks.register("register_rich_text_features")
def register_code_styling(features):
    """Add the code to the richtext editor"""
    feature_name = "code"
    type_ = "CODE"
    tag = "code"

    control = {"type": type_, "label": "</>", "description": "Code"}

    features.register_editor_plugin(
        "draftail", feature_name, draftail_features.InlineStyleFeature(control)
    )

    db_conversion = {
        "from_database_format": {tag: InlineStyleElementHandler(type_)},
        "to_database_format": {"style_map": {type_: {"element": tag}}},
    }

    features.register_converter_rule("contentstate", feature_name, db_conversion)


@hooks.register("register_rich_text_features")
def register_lead_feature(features):
    feature_name = "lead"
    type_ = "LEAD"

    control = {
        "type": type_,
        "label": "Ld",
        "description": "Lead text",
        "style": {
            "fontSize": "1.75rem",
            "lineHeight": "1.5",
        },
    }

    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.InlineStyleFeature(control),
    )

    features.register_converter_rule(
        "contentstate",
        feature_name,
        {
            "from_database_format": {
                'span[class="text-lead"]': InlineStyleElementHandler(type_),
            },
            "to_database_format": {
                "style_map": {
                    type_: 'span class="text-lead"',
                },
            },
        },
    )


@hooks.register("register_rich_text_features")
def register_species_autolink_hint_feature(features):
    feature_name = "species-autolink-hint"

    features.register_editor_plugin(
        "draftail",
        feature_name,
        draftail_features.PluginFeature(
            {
                "type": "SPECIES_AUTOLINK_HINT",
                "termsUrl": reverse_lazy("species_autolink_terms"),
            },
            js=["plants/js/species_autolink_hints.js"],
            css={"all": ["plants/css/species_autolink_hints.css"]},
        ),
    )

    features.default_features.append(feature_name)


@hooks.register("before_serve_document")
def serve_pdf(document, request):
    if document.file_extension != "pdf":
        return
    response = HttpResponse(document.file.read(), content_type="application/pdf")
    response["Content-Disposition"] = (
        'filename="' + document.file.name.split("/")[-1] + '"'
    )
    if request.GET.get("download", False) in [True, "True", "true"]:
        response["Content-Disposition"] = (
            "attachment; " + response["Content-Disposition"]
        )
    return response


@hooks.register("register_help_menu_item")
def register_rbg_style_guide_menu_item():
    return MenuItem(
        name="rbg_style_guide",
        label="RBG Style Guide",
        url="https://uofu.box.com/s/gb5psi7cn82tm62a8ndmouv53y47nre1",
        icon_name="link",
    )


register_snippet(RBGHoursViewSet)
