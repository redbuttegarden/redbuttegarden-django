from __future__ import annotations

import json
from urllib.parse import urljoin

from django.db import models
from django.urls import NoReverseMatch, reverse
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSiteSetting, register_setting
from wagtail.fields import StreamField
from wagtail.models import Site

from .blocks import LinkBlock, NavGroupBlock


def _parse_json(value, default):
    """
    Accept either:
    - already-parsed list/dict (from older seed data / migrations)
    - JSON string
    - empty/None
    """
    if value in (None, "", [], {}):
        return default
    if isinstance(value, (list, dict)):
        return value
    try:
        return json.loads(value)
    except Exception:
        return default


@register_setting
class NavigationSettings(BaseSiteSetting):
    """
    Per-site navigation configuration.
    """

    navbar = StreamField(
        [("group", NavGroupBlock())],
        use_json_field=True,
        blank=True,
    )

    top_links = StreamField(
        [("link", LinkBlock())],
        use_json_field=True,
        blank=True,
        help_text="Optional links rendered on the right side (e.g. JOIN / GIVE).",
    )

    show_search = models.BooleanField(default=True)
    search_placeholder = models.CharField(max_length=60, default="Search")

    panels = [
        FieldPanel("navbar"),
        FieldPanel("top_links"),
        FieldPanel("show_search"),
        FieldPanel("search_placeholder"),
    ]

    def resolved_nav(self):
        """
        Returns a fully-resolved python structure with URLs computed.
        Safe to call from templates/context processors.
        """
        return {
            "groups": [self._resolve_group(block.value) for block in self.navbar],
            "top_links": [self._resolve_link(block.value) for block in self.top_links],
            "show_search": self.show_search,
            "search_placeholder": self.search_placeholder,
        }

    def _page_path_for_site(self, page) -> str:
        """
        Return a root-relative path for a page on this setting's site, e.g. '/events/'.
        Avoids preview/admin-relative issues by ensuring the result starts with '/'.
        """
        if not page:
            return "/"

        # get_url_parts returns (site_id, root_url, page_path) or None
        parts = page.get_url_parts()
        if parts and parts[2]:
            path = parts[2]
            return path if path.startswith("/") else f"/{path}"

        # Fallbacks
        try:
            url = page.get_url() or "/"
        except Exception:
            url = "/"

        return url if url.startswith("/") else f"/{url}"

    def _resolve_group(self, group_value):
        """
        group_link is a StreamBlock(max_num=1), so group_value['group_link'] is a StreamValue.
        If present, first item contains the LinkBlock value.
        """
        group_link_stream = group_value.get("group_link")
        group_link = None

        if group_link_stream:
            # StreamBlock item has .value containing the LinkBlock struct value
            group_link = self._resolve_link(group_link_stream[0].value)

        return {
            "heading": group_value.get("heading"),
            "key": group_value.get("key"),
            "group_link": group_link,
            "links": [
                self._resolve_link(link) for link in group_value.get("links", [])
            ],
        }

    def _resolve_link(self, link_value):
        """
        Convert a LinkBlock value dict into a renderable dict with a final URL.

        Routable links are normalized to root-relative URLs:
        '/events/' + 'e-cat/art-exhibits/' => '/events/e-cat/art-exhibits/'
        This prevents them being interpreted relative to preview/admin URLs.
        """
        if not link_value:
            return None

        label = link_value.get("label") or ""
        description = link_value.get("description") or ""
        new_tab = bool(link_value.get("open_in_new_tab"))

        internal_page = link_value.get("internal_page")
        external_url = link_value.get("external_url")
        named_url = link_value.get("named_url")

        routable_page = link_value.get("routable_page")
        route_name = link_value.get("route_name")
        route_args = _parse_json(link_value.get("route_args_json"), [])
        route_kwargs = _parse_json(link_value.get("route_kwargs_json"), {})

        url = "#"

        # Internal Wagtail page
        if internal_page:
            page = getattr(internal_page, "specific", internal_page)
            url = self._page_path_for_site(page)

        # External URL
        elif external_url:
            url = external_url

        # Django named URL
        elif named_url:
            try:
                url = reverse(named_url)
            except NoReverseMatch:
                url = "#"

        # Routable page URL
        elif routable_page and route_name:
            page = getattr(routable_page, "specific", routable_page)

            # If the page supports RoutablePageMixin, reverse_subpage gives a route path
            if hasattr(page, "reverse_subpage"):
                try:
                    route_path = page.reverse_subpage(
                        route_name, args=route_args, kwargs=route_kwargs
                    )
                except TypeError:
                    # Older signatures: reverse_subpage(name, *args, **kwargs)
                    route_path = page.reverse_subpage(
                        route_name, *route_args, **route_kwargs
                    )
                except Exception:
                    route_path = ""

                # reverse_subpage often returns a relative path like 'e-cat/art-exhibits/'
                route_path = (route_path or "").lstrip("/")

                base_path = self._page_path_for_site(page)
                if not base_path.endswith("/"):
                    base_path += "/"

                url = urljoin(base_path, route_path) if route_path else base_path
            else:
                url = self._page_path_for_site(page)

        return {
            "label": label,
            "description": description,
            "url": url,
            "new_tab": new_tab,
        }

    @classmethod
    def for_request(cls, request):
        site = Site.find_for_request(request)
        return cls.for_site(site)
