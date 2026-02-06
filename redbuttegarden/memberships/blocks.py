from django.core.exceptions import ValidationError
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock
from wagtail.blocks import PageChooserBlock, StructBlock, CharBlock, DecimalBlock, IntegerBlock, BooleanBlock, RichTextBlock


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

class PricingCardBlock(StructBlock):
    heading = CharBlock(
        required=False,
        default="Flexible Options for your Unique Situation",
        help_text="Main heading for the card"
    )

    first_cardholder_price = DecimalBlock(
        required=True, decimal_places=0, max_digits=10,
        help_text="Price for the first cardholder (numbers only, no $ sign)."
    )

    additional_cardholder_price = DecimalBlock(
        required=True, decimal_places=0, max_digits=10,
        help_text="Price for each additional cardholder."
    )
    additional_cardholder_max = IntegerBlock(
        required=False, default=3,
        help_text="Maximum number of additional cardholders (e.g. 3)."
    )

    guest_admission_price = DecimalBlock(
        required=True, decimal_places=0, max_digits=10,
        help_text="Price per guest for garden visits."
    )
    guest_admission_max = IntegerBlock(
        required=False, default=8,
        help_text="Maximum number of guests allowed (e.g. 8)."
    )

    # Concert access options: represent included + two upgrade levels
    # We keep "two tickets included" as informational flag and allow editors to set upgrade prices/qualifiers
    two_tickets_included = BooleanBlock(
        required=False, default=True,
        help_text="If unchecked, don't render the 'Two tickets per show: included' line."
    )

    four_tickets_price = DecimalBlock(
        required=False, decimal_places=0, max_digits=10,
        help_text="Price to increase to four tickets per show. Leave blank if not offered."
    )
    four_tickets_qualifier = CharBlock(
        required=False,
        help_text='Who qualifies for the 4-ticket upgrade (e.g. "Experience level memberships with 4 or more total visitors")'
    )

    six_tickets_price = DecimalBlock(
        required=False, decimal_places=0, max_digits=10,
        help_text="Price to increase to six tickets per show. Leave blank if not offered."
    )
    six_tickets_qualifier = CharBlock(
        required=False,
        help_text='Who qualifies for the 6-ticket upgrade (e.g. "Experience Plus level memberships with 6 or more total visitors")'
    )

    concert_access_footer_note = CharBlock(
        required=False,
        help_text="Small italic footer note (e.g. '*An upgraded Concert Access Level does not guarantee ticket availability.')"
    )

    membership_level_benefits_text = RichTextBlock(
        required=False,
        help_text="Explanation of membership level benefits"
    )
    cardholder_level_benefits_text = RichTextBlock(
        required=False,
        help_text="Explanation of cardholder level benefits"
    )
    primary_member_text = RichTextBlock(
        required=False,
        help_text="Explanation of primary member benefits"
    )
    additional_cardholders_text = RichTextBlock(
        required=False,
        help_text="Explanation of additional cardholders"
    )
    guests_text = RichTextBlock(
        required=False,
        help_text="Explanation of guest benefits"
    )

    def clean(self, value):
        cleaned = super().clean(value)

        # Validate money fields are non-negative
        money_fields = [
            'first_cardholder_price', 'additional_cardholder_price',
            'guest_admission_price', 'four_tickets_price', 'six_tickets_price'
        ]
        for k in money_fields:
            v = cleaned.get(k)
            if v is not None and v < 0:
                raise ValidationError({k: "Price must be zero or a positive number."})

        # Validate maxima sensible
        add_max = cleaned.get('additional_cardholder_max') or 0
        if add_max < 0 or add_max > 20:
            raise ValidationError({'additional_cardholder_max': "Enter a realistic maximum (0–20)."})

        guest_max = cleaned.get('guest_admission_max') or 0
        if guest_max < 0 or guest_max > 200:
            raise ValidationError({'guest_admission_max': "Enter a realistic maximum (0–200)."})

        # If price is provided for an upgrade, ensure it's > 0
        if cleaned.get('four_tickets_price') is not None and cleaned['four_tickets_price'] <= 0:
            raise ValidationError({'four_tickets_price': "Provide a positive price or leave blank."})
        if cleaned.get('six_tickets_price') is not None and cleaned['six_tickets_price'] <= 0:
            raise ValidationError({'six_tickets_price': "Provide a positive price or leave blank."})

        return cleaned

    class Meta:
        template = "blocks/pricing_card_block.html"
        icon = "list-ul"
        label = "Pricing / Options Card"
