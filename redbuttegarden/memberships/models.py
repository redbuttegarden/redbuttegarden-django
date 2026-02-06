from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import (
    FieldPanel,
)
from wagtail.blocks import RawHTMLBlock
from wagtail.images.blocks import ImageBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.search import index
from .blocks import LinkedCarouselBlock, PricingCardBlock

from home.abstract_models import AbstractBase
from home.models import (
    AlignedParagraphBlock, 
    ButtonBlock, 
    ButtonListDropdownInfo,
    EmphaticText, 
    Heading, 
    HeadingBlock,
    ImageInfoList,
    ImageLinkList,
    ImageListCardInfo,
    ImageListDropdownInfo,
    MultiColumnAlignedParagraphBlock,
    ThreeColumnDropdownInfoPanel
)


class MembershipLevel(models.Model):
    """
    A membership *type* (examples: Individual Garden 1, Individual Experience 4, Dual Garden 2).
    Encodes the entitlements for memberships of this level.
    """

    name = models.CharField(max_length=100, unique=True)
    description = RichTextField(
        blank=True, features=["link", "bold", "italic"]  # keep this minimal
    )
    tooltip = RichTextField(
        blank=True, features=["link", "bold", "italic"], help_text="Displayed on hover"
    )

    # Included cardholders (how many people are on the membership card)
    cardholders_included = models.PositiveSmallIntegerField(default=1)

    # Admissions: number of admissions allowed (per visit / per day / or global depending on rules)
    admissions_allowed = models.PositiveSmallIntegerField(default=1)

    # Number of concert tickets the membership may purchase during a member sale period
    member_sale_ticket_allowance = models.PositiveSmallIntegerField(default=0)

    price = models.DecimalField(
        max_digits=7,  # supports up to 99,999.99
        decimal_places=2,
        help_text="Price of the membership level in USD.",
    )

    purchase_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL where this membership level can be purchased.",
    )

    active = models.BooleanField(default=True)  # if you ever retire a level

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class MembershipPage(AbstractBase):
    body = StreamField(
        [
            ("carousel", LinkedCarouselBlock()),
            ("pricing_card", PricingCardBlock()),
            ("button", ButtonBlock()),
            ("custom_heading", HeadingBlock()),
            (
                "heading",
                Heading(
                    classname="full title",
                    help_text=_("Text will be green and centered"),
                ),
            ),
            (
                "emphatic_text",
                EmphaticText(
                    classname="full title",
                    help_text=_("Text will be red, italic and centered"),
                ),
            ),
            ("paragraph", AlignedParagraphBlock(required=True, classname="paragraph")),
            ("multi_column_paragraph", MultiColumnAlignedParagraphBlock()),
            ("image", ImageBlock(help_text=_("Centered image"))),
            ("html", RawHTMLBlock()),
            ("dropdown_image_list", ImageListDropdownInfo()),
            ("dropdown_button_list", ButtonListDropdownInfo()),
            ("card_info_list", ImageListCardInfo()),
            ("image_info_list", ImageInfoList()),
            ("image_link_list", ImageLinkList()),
            ("three_column_dropdown_info_panel", ThreeColumnDropdownInfoPanel()),
        ],
        block_counts={
            "pricing_card": {"max_num": 1},
        },
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
    ]
