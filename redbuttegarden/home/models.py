import json
import logging

from django import forms
from django.apps import apps
from django.core.paginator import Paginator
from django.core.validators import (
    ValidationError,
    RegexValidator,
    validate_slug,
    URLValidator,
)
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalKey
from wagtail import blocks
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    MultiFieldPanel,
    InlinePanel,
    PageChooserPanel,
    TabbedInterface,
    ObjectList,
    PublishingPanel,
    MultipleChooserPanel,
)
from wagtail.blocks.struct_block import StructBlockAdapter
from wagtail.contrib.settings.models import BaseSiteSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.embeds.blocks import EmbedBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.images.models import Image
from wagtail.models import (
    Page,
    Orderable,
    DraftStateMixin,
    RevisionMixin,
    PreviewableMixin,
    TranslatableMixin,
    Collection,
)
from wagtail.search import index
from wagtail.telepath import register

from home.abstract_models import AbstractBase
from home.custom_fields import ChoiceArrayField

logger = logging.getLogger(__name__)


class ImageInfo(blocks.StructBlock):
    image = ImageBlock()
    title = blocks.CharBlock(
        label="Image Title",
        help_text=_("Overlayed on image"),
        max_length=100,
        required=False,
    )
    subtitle = blocks.CharBlock(
        label="Image Sub-title",
        help_text=_("Overlayed on image below title"),
        max_length=100,
        required=False,
    )
    info_title = blocks.CharBlock(
        label="Information Title",
        help_text=_("Title heading for info displayed to the right of the image"),
        max_length=500,
        required=True,
    )
    info_subtitle = blocks.CharBlock(
        label="Information Sub-title",
        help_text=_("Subheading for info displayed beneath the Information Title"),
        max_length=500,
        required=False,
    )
    tan_bg_info = blocks.RichTextBlock(
        label="Tan background info text",
        help_text=_("Text is centered, bold and green inside a tan background element"),
    )
    tan_bg_button_text = blocks.CharBlock(
        label="Button text",
        help_text=_("Text for button within tan background element"),
        required=False,
    )
    tan_bg_button_url = blocks.URLBlock(help_text=_("URL for button"), required=False)
    additional_info = blocks.RichTextBlock(
        help_text=_("Text displayed below tan background element"), required=False
    )


class ImageInfoList(blocks.StructBlock):
    list_items = blocks.ListBlock(ImageInfo(), label="Image Information")

    class Meta:
        template = "blocks/image_info_list.html"


class ImageCarousel(blocks.StructBlock):
    images = blocks.ListBlock(
        ImageBlock(),
    )

    class Meta:
        template = "blocks/image_carousel.html"


class ImageLink(blocks.StructBlock):
    title = blocks.CharBlock(
        label="Title",
        max_length=200,
        required=False,
        help_text=_("Visible text title that is overlayed on the image"),
    )
    url = blocks.URLBlock(label="URL")
    url_title = blocks.CharBlock(
        label="URL Title",
        max_length=200,
        required=False,
        help_text=_(
            "Screen reader title used to describe the link. This is not displayed visually but is important for accessibility."
        ),
    )
    image = ImageBlock()


class ImageLinkList(blocks.StructBlock):
    list_items = blocks.ListBlock(ImageLink(), label="Image Links")

    class Meta:
        template = "blocks/image_link_list.html"


class AlignedParagraphBlock(blocks.StructBlock):
    alignment = blocks.ChoiceBlock(
        [("left", "Left"), ("text-center", "Center"), ("right", "Right")],
        default="left",
    )
    background_color = blocks.ChoiceBlock(
        [
            ("default", "Default"),
            ("tan-bg", "Tan"),
            ("green-bg", "Green"),
            ("dark-tan-bg", "Dark Tan"),
            ("white-bg", "White"),
            ("red-bg", "Red"),
            ("orange-bg", "Orange"),
        ],
        default="default",
    )
    paragraph = blocks.RichTextBlock()

    class Meta:
        template = "blocks/aligned_paragraph.html"


class MultiColumnAlignedParagraphBlock(AlignedParagraphBlock):
    title = blocks.CharBlock(
        max_length=100,
        required=False,
        help_text=_("Green centered heading above column content"),
    )
    paragraph = blocks.ListBlock(
        blocks.RichTextBlock(),
    )

    class Meta:
        template = "blocks/multi_col_aligned_paragraph.html"


class FAQItem(blocks.StructBlock):
    title_question = blocks.CharBlock(
        label="Title/Question",
        max_length=200,
    )
    text = AlignedParagraphBlock(label="Answer")


class FAQList(blocks.StructBlock):
    list_items = blocks.ListBlock(FAQItem(), label="Question & Answer")

    class Meta:
        template = "blocks/FAQ_list.html"


class SingleListImageDropdownInfo(blocks.StructBlock):
    image = ImageBlock(label="Image")
    title = blocks.CharBlock(
        label="Title",
        max_length=200,
    )
    text = blocks.RichTextBlock(label="Text")


class ImageListDropdownInfo(blocks.StructBlock):
    list_items = blocks.ListBlock(SingleListImageDropdownInfo(), label="List Item")

    class Meta:
        template = "blocks/image_list_dropdown_info.html"


class SingleListImageCardInfo(blocks.StructBlock):
    image = ImageBlock(
        label="Image",
        required=False,
    )
    text = blocks.RichTextBlock(
        label="Text",
        features=["h4", "h5", "bold", "italic", "link", "ul"],
        help_text=_(
            "Note that h4 elements will be colored green and h5 elements will be colored purple"
        ),
    )
    button_text = blocks.CharBlock(
        label="Button Text",
        required=False,
    )
    button_url = blocks.CharBlock(
        label="Button URL",
        required=False,
    )

    # per-item override: force this item to span the full width
    force_full_width = blocks.BooleanBlock(
        required=False,
        label="Force full width",
        help_text="If checked this card will be rendered full width regardless of selected layout.",
    )

    class Meta:
        icon = "form"


class ImageListCardInfo(blocks.StructBlock):
    layout = blocks.ChoiceBlock(
        choices=[
            ("two_column", "Two columns"),
            ("single_column", "Single column"),
            ("auto", "Auto (make long items full width)"),
        ],
        default="two_column",
        label="Layout",
        help_text="Choose how cards are laid out. 'Auto' makes very long items span full width.",
    )

    auto_threshold = blocks.IntegerBlock(
        required=False,
        label="Auto threshold (characters)",
        default=400,
        help_text="When layout is 'auto', items with more than this many non-HTML characters will be full width.",
    )

    list_items = blocks.ListBlock(
        SingleListImageCardInfo(), label="Image Card List Item"
    )

    class Meta:
        template = "blocks/image_list_card_info.html"
        icon = "list-ul"
        label = "Image list cards"


class SingleListButtonDropdownInfo(blocks.StructBlock):
    button_text = blocks.CharBlock(
        label="Button Text",
        max_length=200,
    )
    info_text = blocks.RichTextBlock(
        label="Info Text",
        features=["h4", "h5", "bold", "italic", "link", "document-link", "ul"],
    )


class ButtonListDropdownInfo(blocks.StructBlock):
    list_items = blocks.ListBlock(SingleListButtonDropdownInfo(), label="Button")

    class Meta:
        template = "blocks/button_list_dropdown_info.html"


class SingleListCardDropdownInfo(blocks.StructBlock):
    card_info = AlignedParagraphBlock(
        label="Card Text",
    )
    info_text = blocks.RichTextBlock(
        label="Info Text",
    )
    info_button_text = blocks.CharBlock(
        max_length=100,
        help_text=_("Button appears below Info Text"),
        required=False,
    )
    info_button_url = blocks.URLBlock(
        max_length=200, label="Button URL", required=False
    )


class TextAlignmentChoiceBlock(blocks.ChoiceBlock):
    choices = [
        ("center", "Center"),
        ("justify", "Justified"),
        ("left", "Left"),
        ("right", "Right"),
    ]


class ColorChoiceBlock(blocks.ChoiceBlock):
    GREEN = "green"
    TAN = "tan"
    DARK_TAN = "dk-tn"
    RED = "red"
    ORANGE = "orange"
    BLACK = "black"
    WHITE = "white"

    choices = [
        (DARK_TAN, "Dark Tan"),
        (GREEN, "Green"),
        (ORANGE, "Orange"),
        (RED, "Red"),
        (TAN, "Tan"),
        (BLACK, "Black"),
        (WHITE, "White"),
    ]


class HeadingBlock(blocks.StructBlock):
    """
    Block for choosing headings that allow a choice of alignment, color, and anchor ID.

    Intended to replace the "Heading" block.
    """

    title = blocks.CharBlock(label=_("Title"), required=True)
    heading_size = blocks.ChoiceBlock(
        [
            ("h2", "H2"),
            ("h3", "H3"),
            ("h4", "H4"),
            ("h5", "H5"),
            ("h6", "H6"),
        ],
        default="h2",
        label=_("Size"),
    )
    alignment = TextAlignmentChoiceBlock(label=_("Alignment"), default="center")
    color = ColorChoiceBlock(label=_("Color"), default="green")
    background_color = blocks.ChoiceBlock(
        [
            ("default", "Default"),
            ("tan-bg", "Tan"),
            ("green-bg", "Green"),
            ("dark-tan-bg", "Dark Tan"),
            ("white-bg", "White"),
            ("red-bg", "Red"),
            ("orange-bg", "Orange"),
        ],
        default="default",
    )
    anchor_id = blocks.CharBlock(
        label=_("Optional Anchor Identifier"),
        validators=[validate_slug],
        required=False,
    )

    class Meta:
        template = "blocks/heading_block.html"
        icon = "title"
        form_classname = "struct-block heading-block"
        label = _("Heading")


class HeadingBlockAdapter(StructBlockAdapter):
    @cached_property
    def media(self):
        return forms.Media(
            css={"all": ("admin/css/heading-block.css",)},
        )


class Heading(blocks.CharBlock):
    """Green centered h2 element"""

    class Meta:
        template = "blocks/heading.html"
        icon = "grip"
        label = "Green Centered Heading"


class EmphaticText(blocks.CharBlock):
    """For displaying red italic text"""

    class Meta:
        template = "blocks/emphatic_text.html"
        icon = "italic"
        label = "Emphatic Text"


class ButtonBlock(blocks.StructBlock):
    text = blocks.CharBlock(max_length=100)
    url = blocks.URLBlock()
    color = ColorChoiceBlock()
    alignment = TextAlignmentChoiceBlock()

    class Meta:
        template = "blocks/button_block.html"


class ButtonRow(blocks.StructBlock):
    list_items = blocks.ListBlock(ButtonBlock(), label="Button")

    class Meta:
        template = "blocks/button_row.html"


class NewsletterBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, required=False)
    embed = blocks.RawHTMLBlock(required=True)


class NewsletterListBlock(blocks.StructBlock):
    list_items = blocks.ListBlock(NewsletterBlock())

    class Meta:
        template = "blocks/newsletter_list_block.html"


class SingleThreeColumnDropdownInfoPanel(blocks.StructBlock):
    background_color = blocks.ChoiceBlock(
        [
            ("default-panel", "Default"),
            ("purple-panel", "Purple"),
            ("orange-panel", "Orange"),
            ("blue-panel", "Blue"),
            ("green-panel", "Green"),
        ],
        default="default-panel",
    )
    col_one_header = blocks.RichTextBlock(
        label="Column One Panel Header",
        help_text=_("Header for first column of dropdown panel"),
        required=True,
    )
    col_two_header = blocks.RichTextBlock(
        label="Column Two Panel Header",
        help_text=_("Header for second column of dropdown panel"),
        required=True,
    )
    col_three_header = blocks.RichTextBlock(
        label="Column Three Panel Header",
        help_text=_("Header for third column of dropdown panel"),
        required=True,
    )
    class_info_subheaders = blocks.BooleanBlock(
        label="Subheaders for Classes",
        help_text=_(
            "Select this option to include class-related subheadings for all columns (e.g. Grade, Ages, "
            "Session, Location, Cost"
        ),
    )
    col_one_top_info = blocks.RichTextBlock(
        help_text=_(
            'If class subheaders are selected, this text appears after the "GRADE:" subheading'
        )
    )
    col_two_top_info = blocks.RichTextBlock(
        help_text=_(
            'If class subheaders are selected, this text appears after the "AGES:" subheading'
        )
    )
    col_three_top_info = blocks.RichTextBlock(
        help_text=_(
            'If class subheaders are selected, this text appears after the "SESSION:" subheading'
        )
    )
    middle_info = AlignedParagraphBlock(
        help_text=_(
            "Text info appearing inside expanded panel between top and bottom subheader content"
        )
    )
    button = ButtonBlock(required=False)
    col_one_bottom_info = blocks.RichTextBlock(
        help_text=_(
            'If class subheaders are selected, this text appears beside the "LOCATION:" subheading'
        )
    )
    col_two_bottom_info = blocks.RichTextBlock(
        help_text=_(
            'If class subheaders are selected, this text appears beside the "COST:" subheading'
        )
    )
    col_three_bottom_info = blocks.RichTextBlock(
        help_text=_(
            'If class subheaders are selected, this text appears beside the "CONTACT INFORMATION:" subheading'
        )
    )


class ThreeColumnDropdownInfoPanel(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleThreeColumnDropdownInfoPanel(),
        label="Thee Column Dropdown Info Panel",
    )

    class Meta:
        template = "blocks/three_column_dropdown_info_panel.html"


class ColumnBlock(blocks.StreamBlock):
    heading = Heading(
        classname="full title", help_text=_("Text will be green and centered")
    )
    emphatic_text = EmphaticText(
        classname="full title", help_text=_("Text will be red, italic and centered")
    )
    aligned_paragraph = AlignedParagraphBlock()
    paragraph = blocks.RichTextBlock()
    image = ImageBlock()
    document = DocumentChooserBlock()
    button = ButtonBlock()
    html = blocks.RawHTMLBlock()

    class Meta:
        template = "blocks/column.html"


class TwoColumnBlock(blocks.StructBlock):
    left_column = ColumnBlock(icon="arrow-left", label="Left column content")
    right_column = ColumnBlock(icon="arrow-right", label="Right column content")

    class Meta:
        template = "blocks/two_column_block.html"
        icon = "placeholder"
        label = "Two Columns"


class GeneralPage(AbstractBase):
    body = StreamField(
        block_types=[
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
            ("image_carousel", ImageCarousel()),
            ("html", blocks.RawHTMLBlock()),
            ("dropdown_image_list", ImageListDropdownInfo()),
            ("dropdown_button_list", ButtonListDropdownInfo()),
            ("card_info_list", ImageListCardInfo()),
            ("image_info_list", ImageInfoList()),
            ("image_link_list", ImageLinkList()),
            ("three_column_dropdown_info_panel", ThreeColumnDropdownInfoPanel()),
            ("newsletters", NewsletterListBlock()),
        ],
        blank=False,
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(AbstractBase.dialog_box_panels, heading="Dialog"),
            ObjectList(AbstractBase.promote_panels, heading="Promote"),
            ObjectList(AbstractBase.settings_panels, heading="Settings"),
        ]
    )


class TwoColumnGeneralPage(AbstractBase):
    body = StreamField(
        block_types=(
            [
                (
                    "green_heading",
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
                ("paragraph", AlignedParagraphBlock()),
                ("image", ImageBlock()),
                ("document", DocumentChooserBlock()),
                ("two_columns", TwoColumnBlock()),
                ("embedded_video", EmbedBlock(icon="media")),
                ("html", blocks.RawHTMLBlock()),
                ("dropdown_image_list", ImageListDropdownInfo()),
                ("dropdown_button_list", ButtonListDropdownInfo()),
            ]
        ),
        null=True,
        blank=True,
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    search_fields = AbstractBase.search_fields + [index.SearchField("body")]


class PlantCollectionsPage(AbstractBase):
    intro = RichTextField()
    more_info_modal = RichTextField()

    content_panels = AbstractBase.content_panels + [
        FieldPanel("intro"),
        FieldPanel("more_info_modal"),
        InlinePanel("plant_collections", label=_("Plant Collection")),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("intro"),
        index.SearchField("more_info_modal"),
    ]


class PlantCollections(Orderable):
    page = ParentalKey(
        PlantCollectionsPage,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="plant_collections",
    )
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    collection_doc = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    title = models.CharField(max_length=255)
    text = RichTextField()
    slideshow_link = models.URLField()

    panels = [
        FieldPanel("image"),
        FieldPanel("title"),
        FieldPanel("text"),
        MultiFieldPanel(
            [FieldPanel("slideshow_link"), FieldPanel("collection_doc")],
            heading=_("Info for Collection buttons"),
        ),
    ]


class GeneralIndexPage(AbstractBase):
    body = StreamField(
        block_types=[
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
            ("image", ImageBlock()),
            ("html", blocks.RawHTMLBlock()),
            ("dropdown_image_list", ImageListDropdownInfo()),
            ("dropdown_button_list", ButtonListDropdownInfo()),
            ("image_link_list", ImageLinkList()),
            ("button", ButtonBlock()),
            ("button_row", ButtonRow()),
        ],
        blank=True,
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    subpage_types = [
        "events.EventPage",
        "events.EventIndexPage",
        "home.GeneralIndexPage",
        "home.GeneralPage",
        "home.TwoColumnGeneralPage",
        "concerts.ConcertPage",
        "journal.JournalIndexPage",
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
    ]

    def get_general_items(self):
        # This returns a Django paginator of blog items in this section
        return Paginator(self.get_children().live(), 10)

    def get_cached_paths(self):
        # Yield the main URL
        yield "/"

        # Yield one URL per page in the paginator to make sure all pages are purged
        for page_number in range(1, self.get_general_items().num_pages + 1):
            yield "/?page=" + str(page_number)

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request, *args, **kwargs)
        sub_pages = self.get_children().live().order_by("-latest_revision_created_at")
        context["sub_pages"] = sub_pages
        return context


class FAQPage(AbstractBase):
    body = StreamField(
        block_types=[
            (
                "heading",
                Heading(
                    classname="full title",
                    help_text=_("Text will be green and centered"),
                ),
            ),
            ("paragraph", AlignedParagraphBlock(required=True, classname="paragraph")),
            ("dropdown_button_list", ButtonListDropdownInfo()),
            ("image", ImageBlock()),
            ("html", blocks.RawHTMLBlock()),
            ("FAQ_list", FAQList()),
        ]
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
    ]

    class Meta:
        verbose_name = "FAQ Page"


class RBGHoursOrderable(Orderable):
    """This allows us to select one or more RBG Hours from Snippets."""

    page = ParentalKey("home.HomePage", related_name="rbg_hours")
    hours = models.ForeignKey(
        "home.RBGHours",
        on_delete=models.CASCADE,
    )


DAYS_OF_WEEK = (
    (0, "Sunday"),
    (1, "Monday"),
    (2, "Tuesday"),
    (3, "Wednesday"),
    (4, "Thursday"),
    (5, "Friday"),
    (6, "Saturday"),
)
MONTHS_OF_YEAR = (
    (0, "January"),
    (1, "February"),
    (2, "March"),
    (3, "April"),
    (4, "May"),
    (5, "June"),
    (6, "July"),
    (7, "August"),
    (8, "September"),
    (9, "October"),
    (10, "November"),
    (11, "December"),
)


def default_days_of_week():
    return [choice[0] for choice in DAYS_OF_WEEK]


def default_months_of_year():
    return [choice[0] for choice in MONTHS_OF_YEAR]


class RBGHours(models.Model):
    """
    Model for defining the hours that are processed and displayed by hours.js on the HomePage.
    """

    name = models.CharField(
        max_length=200, help_text=_("Create a name for this set of hours")
    )
    garden_open = models.TimeField(
        null=True, blank=True, help_text=_("The time the garden opens")
    )
    garden_close = models.TimeField(
        null=True, blank=True, help_text=_("The time the garden closes")
    )
    additional_message = RichTextField(
        null=True,
        blank=True,
        help_text=_("Message under the hours; e.g. 'Last entry at 3:30 PM'"),
    )
    additional_emphatic_mesg = RichTextField(
        null=True, blank=True, help_text=_("Message under hours in RED text")
    )
    garden_open_message = models.CharField(
        max_length=200, null=True, blank=True, default=_("The Garden is open")
    )
    garden_closed_message = models.CharField(
        max_length=200, null=True, blank=True, default=_("The Garden is closed now")
    )
    days_of_week = ChoiceArrayField(
        models.IntegerField(choices=DAYS_OF_WEEK),
        blank=True,
        null=True,
        default=default_days_of_week,
        help_text=_("Select the days of the week this set of hours applies to"),
    )
    months_of_year = ChoiceArrayField(
        models.IntegerField(choices=MONTHS_OF_YEAR),
        blank=True,
        null=True,
        default=default_months_of_year,
        help_text=_("Select the months of the year this set of hours applies to"),
    )

    last_modified = models.DateTimeField(auto_now=True)

    panels = [
        FieldPanel("name"),
        MultiFieldPanel(
            [
                FieldPanel("garden_open"),
                FieldPanel("garden_close"),
            ],
            heading="Hours",
            classname="collapsible",
        ),
        MultiFieldPanel(
            [
                FieldPanel("additional_message"),
                FieldPanel("additional_emphatic_mesg"),
                FieldPanel("garden_open_message"),
                FieldPanel("garden_closed_message"),
            ],
            heading="Messaging",
            classname="collapsible collapsed",
        ),
        MultiFieldPanel(
            [
                FieldPanel("days_of_week"),
                FieldPanel("months_of_year"),
            ],
            heading="Active Times",
            classname="collapsible",
        ),
    ]

    class Meta:
        verbose_name_plural = "RBG Hours"
        ordering = ["-last_modified"]

    def __str__(self):
        return self.name


class HomePage(AbstractBase):
    hours_section_text = RichTextField(
        null=True,
        blank=True,
        help_text=_(
            "This text is displayed within the hours section, just beneath the hours"
        ),
    )
    concert_page = models.ForeignKey(
        "concerts.ConcertPage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Set to this years concert Wagtail page to extract concert dates"),
    )
    visit_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="home_page_visit_images",
    )
    whats_blooming_now_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="home_page_blooming_now_images",
    )

    content_panels = Page.content_panels + [
        MultipleChooserPanel(
            "rbg_hours",
            label=_("RBG Hours"),
            chooser_field_name="hours",
            help_text=_("Choose the set of hours to display on the home page"),
        ),
        FieldPanel("hours_section_text"),
        InlinePanel("event_slides", label=_("Slideshow Images")),
        MultiFieldPanel(
            [
                FieldRowPanel(
                    [
                        FieldPanel("visit_image"),
                        FieldPanel("whats_blooming_now_image"),
                    ]
                ),
            ],
            heading=_("Homepage Featured Images"),
            help_text=_("Images used for Visit and What's Blooming sections."),
        ),
        FieldPanel(
            "concert_page", permission="superuser"
        ),  # Arbitrary permission name; only superusers can access this
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, **kwargs)

        if self.concert_page:
            concerts = self.concert_page.get_visible_concerts()
            concert_info = [
                {
                    "TicketURL": (
                        concert["ticket_url"] if not concert["sold_out"] else None
                    ),
                    "Date": concert_date,
                    "BandName": concert["band_name"],
                }
                for concert in concerts
                for concert_date in concert["concert_dates"]
            ]
            context["concert_info"] = json.dumps(concert_info, default=str)

        # Get upcoming events; avoid circular import
        EventPage = apps.get_model(app_label="events", model_name="EventPage")
        events = (
            EventPage.objects.live()
            .public()
            .filter(alias_of=None, order_date__gte=timezone.now())
            .order_by("order_date")[:3]
        )  # Get next 3 events
        context["upcoming_events"] = events

        # Get social media images
        try:
            instagram_collection = Collection.objects.get(name="Instagram Data")
        except Collection.DoesNotExist as e:
            instagram_collection = None

        if instagram_collection:
            social_media_images = Image.objects.filter(
                collection=instagram_collection
            ).order_by("-created_at")[:10]

            images_and_links = []
            url_validator = URLValidator()
            for image in social_media_images:
                # Try to get permalink from image's description
                try:
                    permalink = image.description.split(" ")[0]
                    url_validator(permalink)
                except (IndexError,):
                    logger.warning(
                        f"Image {image.id} does not have a valid permalink in its description."
                    )
                    continue
                except (ValidationError,) as e:
                    logger.warning(f"Failed to validate URL: {permalink}\n\n{e}")
                    continue

                # Try to get the the caption from the image's description
                try:
                    caption = " ".join(image.description.split(" ")[1:])
                except IndexError:
                    logger.warning(
                        f"Image {image.id} does not have a caption in its description."
                    )
                    caption = None

                images_and_links.append(
                    {"image": image, "url": permalink, "caption": caption}
                )

            context["social_media_images_links"] = images_and_links

        return context

    def get_cached_paths(self):
        """
        Override default so we can also invalidate the cache of the API endpoint for getting RBGHours
        """
        return ["/", reverse("home:hours", args=[self.id])]


class EventSlides(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name="event_slides")
    image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    embed = models.URLField(
        blank=True, null=True, help_text=_("Link to external video URL")
    )
    link = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_("Link to Wagtail page"),
    )
    alternate_link = models.URLField(
        blank=True,
        null=True,
        help_text=_("Link to external URL or non-page Wagtail view"),
    )
    text = RichTextField(
        max_length=100,
        features=["h1", "h2", "h3", "h4", "h5", "h6", "bold", "italic"],
        null=True,
        blank=True,
    )

    panels = [
        FieldPanel("image"),
        FieldPanel("embed"),
        PageChooserPanel("link"),
        FieldPanel("alternate_link"),
        FieldPanel("text"),
    ]

    def clean(self):
        if self.image and self.embed:
            raise ValidationError("Please choose only an image or embed link, not both")
        if self.link and self.alternate_link:
            raise ValidationError(
                "Please choose only a page link OR an alternate link, not both"
            )


class AddressBlock(blocks.StructBlock):
    street_address = blocks.CharBlock(max_length=40, required=False)
    city = blocks.CharBlock(max_length=30, required=False)
    # Looked up the minimum and maximum zipcode values in the USA
    zipcode = blocks.IntegerBlock(min_value=501, max_value=99950, required=False)
    phone = blocks.CharBlock(
        validators=[
            RegexValidator(
                r"\(?[0-9]{3}\)?[-|\s]?[0-9]{3}-?[0-9]{4}",
                "Please enter a valid phone number",
            )
        ]
    )

    class Meta:
        template = "blocks/address_block.html"


class RetailPartnerBlock(blocks.StructBlock):
    name = blocks.CharBlock(max_length=75)
    addresses = blocks.ListBlock(AddressBlock(), required=False)
    url = blocks.URLBlock(required=False)
    info = blocks.RichTextBlock()

    class Meta:
        template = "blocks/retail_partner_block.html"


class RetailPartnerPage(AbstractBase):
    body = StreamField(
        block_types=[
            ("button", ButtonBlock()),
            ("green_heading", Heading()),
            ("paragraph", AlignedParagraphBlock()),
        ]
    )
    retail_partners = StreamField(
        block_types=[("retail_partner", RetailPartnerBlock())]
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
        FieldPanel("retail_partners"),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
        index.SearchField("retail_partners"),
    ]

    def save_revision(self, *args, **kwargs):
        if self.banner is None:
            banner_query = Image.objects.filter().search("Retail Partner Banner")
            try:
                banner = banner_query[0]
                self.banner = banner
            except IndexError as e:
                logger.error("[!] Failed to find banner for Retail Partner Page: ", e)
        return super().save_revision(*args, **kwargs)


class FooterText(
    DraftStateMixin,
    RevisionMixin,
    PreviewableMixin,
    TranslatableMixin,
    models.Model,
):
    """
    This provides editable text for the site footer. It is made
    accessible on the template via a template tag defined in base/templatetags/
    navigation_tags.py
    """

    body = RichTextField()

    panels = [
        FieldPanel("body"),
        PublishingPanel(),
    ]

    def __str__(self):
        return "Footer text"

    def get_preview_template(self, request, mode_name):
        return "base.html"

    def get_preview_context(self, request, mode_name):
        return {"footer_text": self.body}

    class Meta(TranslatableMixin.Meta):
        verbose_name_plural = "Footer Text"


class CurrentWeather(models.Model):
    """
    Singleton model for storing the current weather data for the homepage.

    Single row is overwritten with each new weather update. This prevents
    the database and backups from growing too large.
    """

    condition = models.CharField(max_length=50)
    temperature = models.IntegerField()

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)


@register_setting
class SiteSettings(BaseSiteSetting):
    title_suffix = models.CharField(
        verbose_name="Title suffix",
        max_length=255,
        help_text="The suffix for the title meta tag e.g. ' | Red Butte Garden'",
        default="Red Butte Garden",
    )

    panels = [
        FieldPanel("title_suffix"),
    ]


register(HeadingBlockAdapter(), HeadingBlock)
