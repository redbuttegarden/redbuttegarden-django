"""
This block gets its own file to avoid circular imports
"""

from django.urls import reverse
from django.utils.crypto import get_random_string
from wagtail import blocks

from .forms import MembershipSelectorForm
from .widget_config import MembershipWidgetConfig


class MembershipWidgetBlock(blocks.StructBlock):
    def get_context(self, value, parent_context=None):
        ctx = super().get_context(value, parent_context=parent_context)

        target_id = f"search-results-{get_random_string(8)}"

        post_url = reverse("members:membership_selector")

        cfg = MembershipWidgetConfig.get_solo()
        form = MembershipSelectorForm(cfg=cfg)

        ctx.update(
            {
                "target_id": target_id,
                "post_url": post_url,
                "cfg": cfg,
                "form": form,
            }
        )
        return ctx

    class Meta:
        template = "blocks/membership_widget.html"
        icon = "search"
        label = "Membership widget"
