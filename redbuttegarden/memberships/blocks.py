from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks import PageChooserBlock


class LinkedCarouselSlideBlock(blocks.StructBlock):
    image = ImageChooserBlock(required=True)
    caption = blocks.CharBlock(required=False, max_length=255)
    link_page = PageChooserBlock(required=False, help_text="Choose an internal page")
    link_url = blocks.URLBlock(
        required=False,
        help_text="Or enter an external URL (will be used if no internal page selected)",
    )
    open_in_new_tab = blocks.BooleanBlock(
        required=False, default=False, help_text="Open the link in a new tab"
    )

    class Meta:
        icon = "image"
        label = "Slide"


class LinkedCarouselBlock(blocks.ListBlock):
    def __init__(self, *args, **kwargs):
        super().__init__(LinkedCarouselSlideBlock(), *args, **kwargs)

    class Meta:
        icon = "placeholder"
        label = "Linked Image carousel"
        template = "blocks/linked_carousel_block.html"
