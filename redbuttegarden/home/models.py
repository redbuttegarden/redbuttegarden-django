from django.core.paginator import Paginator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey

from wagtail.core import blocks
from wagtail.core.models import Collection, Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import StreamFieldPanel, FieldPanel, MultiFieldPanel, InlinePanel, PageChooserPanel
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.models import Image
from wagtail.search import index
from wagtail.snippets.edit_handlers import SnippetChooserPanel
from wagtail.snippets.models import register_snippet

from home.abstract_models import AbstractBase


class ImageInfo(blocks.StructBlock):
    image = ImageChooserBlock()
    title = blocks.CharBlock(
        label='Image Title',
        help_text=_("Overlayed on image"),
        max_length=100,
        required=False,
    )
    subtitle = blocks.CharBlock(
        label='Image Sub-title',
        help_text=_("Overlayed on image below title"),
        max_length=100,
        required=False,
    )
    info_title = blocks.CharBlock(
        label='Information Title',
        help_text=_('Title heading for info displayed to the right of the image'),
        max_length=500,
        required=True,
    )
    info_subtitle = blocks.CharBlock(
        label='Information Sub-title',
        help_text=_('Subheading for info displayed beneath the Information Title'),
        max_length=500,
        required=False,
    )
    tan_bg_info = blocks.RichTextBlock(
        label='Tan background info text',
        help_text=_('Text is centered, bold and green inside a tan background element'),
    )
    tan_bg_button_text = blocks.CharBlock(
        label='Button text',
        help_text=_('Text for button within tan background element'),
        required=False
    )
    tan_bg_button_url = blocks.URLBlock(
        help_text=_('URL for button'),
        required=False
    )
    additional_info = blocks.RichTextBlock(
        help_text=_('Text displayed below tan background element'),
        required=False
    )


class ImageInfoList(blocks.StructBlock):
    list_items = blocks.ListBlock(
        ImageInfo(),
        label="Image Information"
    )

    class Meta:
        template = 'blocks/image_info_list.html'


class ImageCarousel(blocks.StructBlock):
    images = blocks.ListBlock(
        ImageChooserBlock(),
    )

    class Meta:
        template = 'blocks/image_carousel.html'


class ImageLink(blocks.StructBlock):
    title = blocks.CharBlock(
        label='Title',
        max_length=200,
        required=False,
    )
    url = blocks.URLBlock(
        label="URL"
    )
    image = ImageChooserBlock()


class ImageLinkList(blocks.StructBlock):
    list_items = blocks.ListBlock(
        ImageLink(),
        label="Image Links"
    )

    class Meta:
        template = 'blocks/image_link_list.html'


class AlignedParagraphBlock(blocks.StructBlock):
    alignment = blocks.ChoiceBlock([('left', 'Left'), ('text-center', 'Center'), ('right', 'Right')], default='left')
    background_color = blocks.ChoiceBlock([('default', 'Default'), ('tan-bg', 'Tan'), ('green-bg', 'Green'),
                                           ('dark-tan-bg', 'Dark Tan'), ('white-bg', 'White'), ('red-bg', 'Red'),
                                           ('orange-bg', 'Orange')], default='default')
    paragraph = blocks.RichTextBlock()

    class Meta:
        template = 'blocks/aligned_paragraph.html'


class MultiColumnAlignedParagraphBlock(AlignedParagraphBlock):
    title = blocks.CharBlock(max_length=100,
                             required=False,
                             help_text=_('Green centered heading above column content'))
    paragraph = blocks.ListBlock(
        blocks.RichTextBlock(),
    )

    class Meta:
        template = 'blocks/multi_col_aligned_paragraph.html'


class FAQItem(blocks.StructBlock):
    title_question = blocks.CharBlock(
        label='Title/Question',
        max_length=200,
    )
    text = AlignedParagraphBlock(
        label='Answer'
    )


class FAQList(blocks.StructBlock):
    list_items = blocks.ListBlock(
        FAQItem(),
        label="Question & Answer"
    )

    class Meta:
        template = 'blocks/FAQ_list.html'


class SingleListImageDropdownInfo(blocks.StructBlock):
    image = ImageChooserBlock(
        label='Image'
    )
    title = blocks.CharBlock(
        label='Title',
        max_length=200,
    )
    text = blocks.RichTextBlock(
        label='Text'
    )


class ImageListDropdownInfo(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleListImageDropdownInfo(),
        label="List Item"
    )

    class Meta:
        template = 'blocks/image_list_dropdown_info.html'


class SingleListImageCardInfo(blocks.StructBlock):
    image = ImageChooserBlock(
        label='Image',
        required=False,
    )
    text = blocks.RichTextBlock(
        label='Text',
        features=['h4', 'h5', 'bold', 'italic', 'link', 'ul'],
        help_text=_('Note that h4 elements will be colored green and h5 elements will be colored purple')
    )
    button_text = blocks.CharBlock(
        label='Button Text',
        required=False,
    )
    button_url = blocks.CharBlock(
        label='Button URL',
        required=False,
    )


class ImageListCardInfo(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleListImageCardInfo(),
        label="Image Card List Item"
    )

    class Meta:
        template = 'blocks/image_list_card_info.html'


class SingleListButtonDropdownInfo(blocks.StructBlock):
    button_text = blocks.CharBlock(
        label='Button Text',
        max_length=200,
    )
    info_text = blocks.RichTextBlock(
        label='Info Text',
        features=['h4', 'h5', 'bold', 'italic', 'link', 'ul']
    )


class ButtonListDropdownInfo(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleListButtonDropdownInfo(),
        label="Button"
    )

    class Meta:
        template = 'blocks/button_list_dropdown_info.html'


class SingleListCardDropdownInfo(blocks.StructBlock):
    card_info = AlignedParagraphBlock(
        label='Card Text',
    )
    info_text = blocks.RichTextBlock(
        label='Info Text',
    )
    info_button_text = blocks.CharBlock(
        max_length=100,
        help_text=_('Button appears below Info Text'),
        required=False,
    )
    info_button_url = blocks.URLBlock(
        max_length=200,
        label='Button URL',
        required=False
    )


class CardListDropdownInfo(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleListCardDropdownInfo(),
        label="Card"
    )

    class Meta:
        template = 'blocks/card_list_dropdown_info.html'


class Heading(blocks.CharBlock):
    """Green centered h2 element"""

    class Meta:
        template = 'blocks/heading.html'
        icon = 'grip'
        label = 'Green Centered Heading'


class EmphaticText(blocks.CharBlock):
    """For displaying red italic text"""

    class Meta:
        template = 'blocks/emphatic_text.html'
        icon = 'italic'
        label = 'Emphatic Text'


class ButtonBlock(blocks.StructBlock):
    GREEN = 'green'
    TAN = 'tan'
    DARK_TAN = 'dk-tn'
    RED = 'red'
    ORANGE = 'org'
    COLOR_CHOICES = [
        (DARK_TAN, 'Dark Tan'),
        (GREEN, 'Green'),
        (ORANGE, 'Orange'),
        (RED, 'Red'),
        (TAN, 'Tan'),
    ]
    text = blocks.CharBlock(max_length=100)
    url = blocks.URLBlock()
    color = blocks.ChoiceBlock(choices=COLOR_CHOICES)
    alignment = blocks.ChoiceBlock(choices=[
        ('center', 'Center'),
        ('justify', 'Justified'),
        ('left', 'Left'),
        ('right', 'Right')
    ])

    class Meta:
        template = 'blocks/button_block.html'


class ButtonRow(blocks.StructBlock):
    list_items = blocks.ListBlock(
        ButtonBlock(),
        label="Button"
    )

    class Meta:
        template = 'blocks/button_row.html'


class NewsletterBlock(blocks.StructBlock):
    title = blocks.CharBlock(max_length=100, required=False)
    embed = blocks.RawHTMLBlock(required=True)


class NewsletterListBlock(blocks.StructBlock):
    list_items = blocks.ListBlock(NewsletterBlock())

    class Meta:
        template = 'blocks/newsletter_list_block.html'


class SingleThreeColumnDropdownInfoPanel(blocks.StructBlock):
    background_color = blocks.ChoiceBlock([('default-panel', 'Default'), ('purple-panel', 'Purple'),
                                           ('orange-panel', 'Orange'), ('blue-panel', 'Blue'), ('green-panel', 'Green'),
                                           ], default='default-panel')
    col_one_header = blocks.RichTextBlock(
        label='Column One Panel Header',
        help_text=_('Header for first column of dropdown panel'),
        required=True,
    )
    col_two_header = blocks.RichTextBlock(
        label='Column Two Panel Header',
        help_text=_('Header for second column of dropdown panel'),
        required=True,
    )
    col_three_header = blocks.RichTextBlock(
        label='Column Three Panel Header',
        help_text=_('Header for third column of dropdown panel'),
        required=True,
    )
    class_info_subheaders = blocks.BooleanBlock(
        label='Subheaders for Classes',
        help_text=_('Select this option to include class-related subheadings for all columns (e.g. Grade, Ages, '
                    'Session, Location, Cost'),
    )
    col_one_top_info = blocks.RichTextBlock(
        help_text=_('If class subheaders are selected, this text appears after the "GRADE:" subheading')
    )
    col_two_top_info = blocks.RichTextBlock(
        help_text=_('If class subheaders are selected, this text appears after the "AGES:" subheading')
    )
    col_three_top_info = blocks.RichTextBlock(
        help_text=_('If class subheaders are selected, this text appears after the "SESSION:" subheading')
    )
    middle_info = AlignedParagraphBlock(
        help_text=_('Text info appearing inside expanded panel between top and bottom subheader content')
    )
    button = ButtonBlock(required=False)
    col_one_bottom_info = blocks.RichTextBlock(
        help_text=_('If class subheaders are selected, this text appears beside the "LOCATION:" subheading')
    )
    col_two_bottom_info = blocks.RichTextBlock(
        help_text=_('If class subheaders are selected, this text appears beside the "COST:" subheading')
    )
    col_three_bottom_info = blocks.RichTextBlock(
        help_text=_('If class subheaders are selected, this text appears beside the "CONTACT INFORMATION:" subheading')
    )


class ThreeColumnDropdownInfoPanel(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleThreeColumnDropdownInfoPanel(),
        label="Thee Column Dropdown Info Panel",
    )

    class Meta:
        template = 'blocks/three_column_dropdown_info_panel.html'


class ColumnBlock(blocks.StreamBlock):
    heading = Heading(classname='full title',
                      help_text=_('Text will be green and centered'))
    emphatic_text = EmphaticText(classname='full title',
                                 help_text=_('Text will be red, italic and centered'))
    aligned_paragraph = AlignedParagraphBlock()
    paragraph = blocks.RichTextBlock()
    image = ImageChooserBlock()
    document = DocumentChooserBlock()
    button = ButtonBlock()
    html = blocks.RawHTMLBlock()

    class Meta:
        template = 'blocks/column.html'


class TwoColumnBlock(blocks.StructBlock):
    left_column = ColumnBlock(icon='arrow-left', label='Left column content')
    right_column = ColumnBlock(icon='arrow-right', label='Right column content')

    class Meta:
        template = 'blocks/two_column_block.html'
        icon = 'placeholder'
        label = 'Two Columns'


class GeneralPage(AbstractBase):
    body = StreamField(block_types=[
        ('button', ButtonBlock()),
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('multi_column_paragraph', MultiColumnAlignedParagraphBlock()),
        ('image', ImageChooserBlock(help_text=_('Centered image'))),
        ('image_carousel', ImageCarousel()),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
        ('dropdown_button_list', ButtonListDropdownInfo()),
        ('dropdown_card_list', CardListDropdownInfo()),
        ('card_info_list', ImageListCardInfo()),
        ('image_info_list', ImageInfoList()),
        ('three_column_dropdown_info_panel', ThreeColumnDropdownInfoPanel()),
        ('newsletters', NewsletterListBlock()),
    ], blank=False)

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]


class TwoColumnGeneralPage(AbstractBase):
    body = StreamField(block_types=([
        ('green_heading', Heading(classname='full title',
                                  help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', AlignedParagraphBlock()),
        ('image', ImageChooserBlock()),
        ('document', DocumentChooserBlock()),
        ('two_columns', TwoColumnBlock()),
        ('embedded_video', EmbedBlock(icon='media')),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
        ('dropdown_button_list', ButtonListDropdownInfo()),
    ]), null=True, blank=True)

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body')
    ]


class PlantCollectionsPage(AbstractBase):
    intro = RichTextField()
    more_info_modal = RichTextField()

    content_panels = AbstractBase.content_panels + [
        FieldPanel('intro'),
        FieldPanel('more_info_modal'),
        InlinePanel('plant_collections', label=_('Plant Collection')),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('intro'),
        index.SearchField('more_info_modal')
    ]


class PlantCollections(Orderable):
    page = ParentalKey(
        PlantCollectionsPage,
        blank=True, null=True,
        on_delete=models.SET_NULL,
        related_name="plant_collections"
    )
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    collection_doc = models.ForeignKey(
        'wagtaildocs.Document',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    title = models.CharField(max_length=255)
    text = RichTextField()
    slideshow_link = models.URLField()

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('title'),
        FieldPanel('text'),
        MultiFieldPanel(
            [
                FieldPanel('slideshow_link'),
                DocumentChooserPanel('collection_doc')
            ],
            heading=_('Info for Collection buttons')
        ),
    ]


class GeneralIndexPage(AbstractBase):
    body = StreamField(block_types=[
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
        ('dropdown_button_list', ButtonListDropdownInfo()),
        ('image_link_list', ImageLinkList()),
        ('button', ButtonBlock()),
        ('button_row', ButtonRow()),
    ], blank=True)

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]

    subpage_types = ['events.EventPage', 'events.EventIndexPage', 'home.GeneralIndexPage', 'home.GeneralPage',
                     'home.TwoColumnGeneralPage', 'concerts.ConcertPage', 'journal.JournalIndexPage']

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]

    def get_general_items(self):
        # This returns a Django paginator of blog items in this section
        return Paginator(self.get_children().live(), 10)

    def get_cached_paths(self):
        # Yield the main URL
        yield '/'

        # Yield one URL per page in the paginator to make sure all pages are purged
        for page_number in range(1, self.get_general_items().num_pages + 1):
            yield '/?page=' + str(page_number)

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request, *args, **kwargs)
        sub_pages = self.get_children().live().order_by('-latest_revision_created_at')
        context['sub_pages'] = sub_pages
        return context


class FAQPage(AbstractBase):
    body = StreamField(block_types=[
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('FAQ_list', FAQList()),
    ])

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]

    class Meta:
        verbose_name = "FAQ Page"


@register_snippet
class RBGHours(models.Model):
    """
    Model for setting variables used by hours.js on the HomePage.
    # TODO - Write tests to make sure hours display correctly for various times of day/year
    """
    # Set a name for this hours object
    name = models.CharField(max_length=200, help_text=_("Create a name for this set of hours"))

    # Allow users to manually set hour options independent of hours.js
    allow_override = models.BooleanField(help_text=_("Override hours.js script and manually set all hours options"),
                                         default=False)
    garden_open = models.TimeField(null=True, blank=True,
                                   help_text=_(
                                       "When override set to True, this time will be shown as the time the garden opens"))
    garden_close = models.TimeField(null=True, blank=True,
                                    help_text=_(
                                        "When override set to True, this time will be shown as the time the garden closes"))
    additional_message = models.CharField(max_length=200, null=True, blank=True,
                                          help_text=_("Message under the hours; e.g. 'Last entry at 3:30 PM'"))
    additional_emphatic_mesg = models.CharField(max_length=200, null=True, blank=True,
                                                help_text=_("Message under hours in RED text"))

    # Day and time we close for Holiday Party in December
    holiday_party_close_time = models.DateTimeField(null=True, blank=True,
                                                    help_text=_("Day and time we close for Holiday Party in December"))
    """
    Originally created start and end dates for Garden After Dark but this won't work well
    when GAD occurs on non-consecutive dates.
    
    Changed to a StreamField Model so as many or as few dates could be selected.
    
    When GAD occurs over so many days, it would be inconvenient to create them all individually,
    the user can user the manual override option instead.
    """
    gad_dates = StreamField(block_types=[
        ('date', blocks.DateBlock(verbose_name="Garden After Dark date", help_text=_("Date that GAD takes place")))
    ], help_text=_("Choose the dates of GAD. If there are many, using the manual override might be easier"),
        blank=True, null=True)

    panels = [
        FieldPanel('name'),
        MultiFieldPanel([
            FieldPanel('allow_override'),
            FieldPanel('garden_open'),
            FieldPanel('garden_close'),
            FieldPanel('additional_message'),
            FieldPanel('additional_emphatic_mesg'),
        ], heading="Manual override settings", classname="collapsible collapsed"),
        FieldPanel('holiday_party_close_time'),
        StreamFieldPanel('gad_dates'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "RBG Hours"


class HomePage(AbstractBase):
    hours = models.ForeignKey(
        'home.RBGHours',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        SnippetChooserPanel('hours', help_text=_("Choose the set of hours to display on the home page")),
        InlinePanel('event_slides', label=_('Slideshow Images'))
    ]


class EventSlides(Orderable):
    page = ParentalKey(HomePage, on_delete=models.CASCADE, related_name='event_slides')
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    link = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    text = RichTextField(max_length=100,
                         features=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'bold', 'italic'],
                         null=True, blank=True)

    panels = [
        ImageChooserPanel('image'),
        PageChooserPanel('link'),
        FieldPanel('text'),
    ]
