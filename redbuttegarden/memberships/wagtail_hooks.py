from django.shortcuts import redirect
from django.urls import reverse
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import MembershipLabel, MembershipLevel
from .widget_config import MembershipWidgetConfig


class MyViewConfigViewSet(SnippetViewSet):
    model = MembershipWidgetConfig

    menu_label = "Membership widget config"
    menu_icon = "cog"

    # Tighten capabilities in UI
    list_display = ("__str__",)
    search_fields = ()  # usually unnecessary for singleton

    def get_admin_urls_for_registration(self):
        """
        Override the index/list URL to redirect straight to edit page
        for the singleton record.
        """
        urls = super().get_admin_urls_for_registration()

        # The "index" name for this viewset is stable across Wagtail 5/6:
        # it's usually: wagtailsnippets_{app}_{model}:index
        # but we avoid hardcoding by overriding dispatch in index view instead.
        return urls

    def index_view(self, request):
        # Called when user clicks the menu item (list view)
        obj = MembershipWidgetConfig.get_solo()
        return redirect(self.get_edit_url(obj))

    def add_view(self, request):
        # Prevent creating a second row: redirect to edit existing
        obj = MembershipWidgetConfig.get_solo()
        return redirect(self.get_edit_url(obj))

    def get_edit_url(self, obj):
        # Construct the edit URL for this snippet within this viewset namespace.
        # Wagtail viewsets typically name it "<basename>:edit"
        return reverse(self.get_url_name("edit"), args=[obj.pk])

class MembershipLabelViewSet(SnippetViewSet):
    model = MembershipLabel
    icon = "clipboard-list"
    list_display = [
        "name",
        "cardholder_label",
        "admissions_label",
        "member_tickets_label",
        UpdatedAtColumn(),
    ]
    list_per_page = 50
    copy_view_enabled = False
    inspect_view_enabled = False
    admin_url_namespace = "membershiplabel_views"
    base_url_path = "internal/membershiplabel"
    list_filter = {
        "name": ["icontains"],
    }


class MembershipLevelViewSet(SnippetViewSet):
    model = MembershipLevel
    icon = "user"
    list_display = [
        "name",
        "cardholders_included",
        "admissions_allowed",
        "member_sale_ticket_allowance",
        "price",
        UpdatedAtColumn(),
    ]
    list_per_page = 50
    copy_view_enabled = False
    inspect_view_enabled = False
    admin_url_namespace = "membershiplevel_views"
    base_url_path = "internal/membershiplevel"
    list_filter = {
        "cardholders_included": ["exact"],
        "admissions_allowed": ["exact"],
        "member_sale_ticket_allowance": ["exact"],
        "name": ["icontains"],
    }


class MembershipViewSetGroup(SnippetViewSetGroup):
    items = (MyViewConfigViewSet, MembershipLabelViewSet, MembershipLevelViewSet)
    menu_icon = "folder-inverse"
    menu_label = "Membership"
    menu_name = "membership"


register_snippet(MembershipViewSetGroup)
