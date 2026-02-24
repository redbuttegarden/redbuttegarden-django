# home/blocks.py
import json

from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.blocks import StructBlockValidationError


class LinkBlock(blocks.StructBlock):
    """
    One link that can point to exactly one of:
    - internal Wagtail page
    - external URL
    - Django named URL
    - RoutablePage sub-route (reverse_subpage)
    """

    label = blocks.CharBlock(required=True, max_length=80)
    description = blocks.CharBlock(
        required=False, max_length=140, help_text="Optional title/tooltip."
    )
    open_in_new_tab = blocks.BooleanBlock(required=False, default=False)

    # Destinations (choose exactly one)
    internal_page = blocks.PageChooserBlock(required=False)
    external_url = blocks.URLBlock(required=False)
    named_url = blocks.CharBlock(
        required=False,
        max_length=200,
        help_text="Django URL name, e.g. 'plants:plant-map'.",
    )

    # Routable support
    routable_page = blocks.PageChooserBlock(
        required=False, help_text="A page that implements RoutablePageMixin."
    )
    route_name = blocks.CharBlock(
        required=False,
        max_length=120,
        help_text="Routable route name, e.g. 'event_by_category'.",
    )
    route_args_json = blocks.TextBlock(
        required=False,
        help_text='JSON list of positional args, e.g. ["art-exhibits"].',
    )
    route_kwargs_json = blocks.TextBlock(
        required=False,
        help_text='JSON object of keyword args, e.g. {"slug": "art-exhibits"}.',
    )

    class Meta:
        icon = "link"
        label = "Link"

    def clean(self, value):
        cleaned = super().clean(value)

        is_internal = bool(cleaned.get("internal_page"))
        is_external = bool(cleaned.get("external_url"))
        is_named = bool(cleaned.get("named_url"))
        is_routable = bool(
            cleaned.get("routable_page")
            or cleaned.get("route_name")
            or cleaned.get("route_args_json")
            or cleaned.get("route_kwargs_json")
        )

        if sum([is_internal, is_external, is_named, is_routable]) != 1:
            raise StructBlockValidationError(
                {
                    "internal_page": ValidationError(
                        "Choose exactly one destination: internal page, external URL, named URL, or routable URL."
                    )
                }
            )

        # If routable mode, enforce required fields + JSON validation/normalization
        if is_routable:
            if not cleaned.get("routable_page") or not cleaned.get("route_name"):
                raise StructBlockValidationError(
                    {
                        "route_name": ValidationError(
                            "Routable links require both a routable page and a route name."
                        )
                    }
                )

            args = []
            kwargs = {}

            if cleaned.get("route_args_json"):
                try:
                    args = json.loads(cleaned["route_args_json"])
                    if not isinstance(args, list):
                        raise ValueError("route_args_json must be a JSON list")
                except Exception:
                    raise StructBlockValidationError(
                        {
                            "route_args_json": ValidationError(
                                'Must be valid JSON list, e.g. ["art-exhibits"].'
                            )
                        }
                    )

            if cleaned.get("route_kwargs_json"):
                try:
                    kwargs = json.loads(cleaned["route_kwargs_json"])
                    if not isinstance(kwargs, dict):
                        raise ValueError("route_kwargs_json must be a JSON object")
                except Exception:
                    raise StructBlockValidationError(
                        {
                            "route_kwargs_json": ValidationError(
                                'Must be valid JSON object, e.g. {"slug": "art-exhibits"}.'
                            )
                        }
                    )

            # Normalize JSON so edits are stable/diffable
            cleaned["route_args_json"] = json.dumps(args) if args else ""
            cleaned["route_kwargs_json"] = json.dumps(kwargs) if kwargs else ""

        return cleaned


class NavGroupBlock(blocks.StructBlock):
    heading = blocks.CharBlock(required=True, max_length=60)
    key = blocks.CharBlock(
        required=False, max_length=40, help_text="Optional identifier, e.g. 'visit'."
    )

    # IMPORTANT: this avoids storing None for an optional StructBlock child.
    # Empty is simply an empty stream (no blocks), which Wagtail handles reliably.
    group_link = blocks.StreamBlock(
        [("link", LinkBlock())],
        required=False,
        max_num=1,
        help_text="Optional: make the group heading link somewhere.",
    )

    links = blocks.ListBlock(LinkBlock(), min_num=1)

    class Meta:
        icon = "list-ul"
        label = "Nav group"
