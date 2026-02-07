from django.templatetags.static import static
from django.utils.html import format_html
from wagtail.admin.ui.tables import UpdatedAtColumn
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup
from wagtail import hooks

from .models import MembershipLabel, MembershipLevel

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
    items = (MembershipLabelViewSet, MembershipLevelViewSet)
    menu_icon = "folder-inverse"
    menu_label = "Membership"
    menu_name = "membership"


register_snippet(MembershipViewSetGroup)
