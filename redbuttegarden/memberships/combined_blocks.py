"""
Helps avoid circular imports
"""

from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.images.blocks import ImageBlock

from .blocks import PricingCardBlock, LinkedCarouselBlock
from .widgets import MembershipWidgetBlock
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
    ThreeColumnDropdownInfoPanel,
)

CONTENT_BLOCKS = [
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
    ("html", blocks.RawHTMLBlock()),
    ("dropdown_image_list", ImageListDropdownInfo()),
    ("dropdown_button_list", ButtonListDropdownInfo()),
    ("card_info_list", ImageListCardInfo()),
    ("image_info_list", ImageInfoList()),
    ("image_link_list", ImageLinkList()),
    ("three_column_dropdown_info_panel", ThreeColumnDropdownInfoPanel()),
    ("membership_widget", MembershipWidgetBlock()),
]

BOOTSTRAP_GAP_CHOICES = [
    ("g-0", "No gap"),
    ("g-2", "Small"),
    ("g-3", "Default"),
    ("g-4", "Large"),
    ("g-5", "Extra large"),
]

VERTICAL_ALIGN_CHOICES = [
    ("align-items-start", "Top"),
    ("align-items-center", "Center"),
    ("align-items-end", "Bottom"),
]

COLUMN_WIDTH_CHOICES = [
    ("col-12 col-md-6", "6 (half)"),
    ("col-12 col-md-4", "4 (one-third)"),
    ("col-12 col-md-8", "8 (two-thirds)"),
    ("col-12 col-md-3", "3 (one-quarter)"),
    ("col-12 col-md-9", "9 (three-quarters)"),
]


class ContentStreamBlock(blocks.StreamBlock):
    pricing_card = PricingCardBlock()
    arousel = LinkedCarouselBlock()
    button = ButtonBlock()
    custom_heading = HeadingBlock()
    heading = Heading()
    emphatic_text = EmphaticText()
    paragraph = AlignedParagraphBlock()
    multi_column_paragraph = MultiColumnAlignedParagraphBlock()
    image = ImageBlock()
    html = blocks.RawHTMLBlock()
    dropdown_image_list = ImageListDropdownInfo()
    dropdown_button_list = ButtonListDropdownInfo()
    card_info_list = ImageListCardInfo()
    image_info_list = ImageInfoList()
    image_link_list = ImageLinkList()
    three_column_dropdown_info_panel = ThreeColumnDropdownInfoPanel()

    class Meta:
        label = "Content"


class Columns2Block(blocks.StructBlock):
    left_width = blocks.ChoiceBlock(
        choices=COLUMN_WIDTH_CHOICES, default="col-12 col-md-6"
    )
    right_width = blocks.ChoiceBlock(
        choices=COLUMN_WIDTH_CHOICES, default="col-12 col-md-6"
    )
    gap = blocks.ChoiceBlock(
        choices=BOOTSTRAP_GAP_CHOICES,
        default="g-3",
        required=True,
    )
    v_align = blocks.ChoiceBlock(
        choices=VERTICAL_ALIGN_CHOICES,
        default="align-items-start",
        required=True,
    )
    reverse_on_mobile = blocks.BooleanBlock(
        required=False,
        default=False,
        help_text="If checked, right column stacks above left on mobile.",
    )

    left = blocks.StreamBlock(
        CONTENT_BLOCKS,
        required=False,
        label="Left column content",
    )
    right = blocks.StreamBlock(
        CONTENT_BLOCKS,
        required=False,
        label="Right column content",
    )

    class Meta:
        template = "blocks/layout/columns_2.html"
        icon = "placeholder"
        label = "Two columns"
