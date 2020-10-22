from django.core.paginator import Paginator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.admin.edit_handlers import FieldPanel, StreamFieldPanel
from wagtail.core import blocks
from wagtail.core.blocks import PageChooserBlock
from wagtail.core.fields import RichTextField, StreamField
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.images.blocks import ImageChooserBlock

from home.models import AlignedParagraphBlock, GeneralPage


class SingleListImage(blocks.StructBlock):
    image = ImageChooserBlock(
        label='Image',
    )
    title = blocks.CharBlock(
        label='Title',
        max_length=200,
        help_text=_("Displayed right of image in h2 tag, centered and uppercase")
    )
    sub_title = blocks.CharBlock(
        label='Subtitle',
        max_length=200,
        help_text=_("Displayed under title, centered and green")
    )
    text = blocks.RichTextBlock(
        label='Text',
    )
    link_url = blocks.URLBlock(
        label='Link URL',
        max_length=200,
        required=False,
        help_text=_("If provided, the link will be applied to the image")
    )


class ListWithImagesBlock(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleListImage(),
        label="List Item",
        help_text=_("Images displayed with text to the right, all with a tan background")
    )

    class Meta:
        template = 'events/list_with_images.html'
        icon = 'fa-id-card-o'


BLOCK_TYPES = [
        ('green_heading', blocks.CharBlock(max_length=200, help_text="Green centered text")),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('tan_bg_text', blocks.RichTextBlock(required=False, classname='paragraph',
                                             help_text="Paragraph with a tan background")),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock(required=False)),
        ('image_list', ListWithImagesBlock(required=False)),
    ]


class EventIndexPage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    body = StreamField(BLOCK_TYPES + [('page_link', PageChooserBlock())], blank=True)

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner'),
        StreamFieldPanel('body', classname="full"),
    ]

    subpage_types = ['events.EventPage', 'events.EventGeneralPage']

    def get_event_items(self):
        # This returns a Django paginator of event items in this section
        return Paginator(self.get_children().live(), 10)

    def get_cached_paths(self):
        # Yield the main URL
        yield '/'

        # Yield one URL per page in the paginator to make sure all pages are purged
        for page_number in range(1, self.get_event_items().num_pages + 1):
            yield '/?page=' + str(page_number)

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request)
        events = self.get_children().live().order_by('-first_published_at')
        context['events'] = events
        return context


class EventPage(Page):
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    location = models.CharField(max_length=100)
    additional_info = RichTextField(blank=True)
    instructor = models.CharField(max_length=100, blank=True)
    member_cost = models.CharField(max_length=100, help_text="Accepts numbers or text. e.g. Free!")
    public_cost = models.CharField(max_length=200, help_text="Accepts numbers or text. e.g. $35")

    sub_heading = models.CharField(max_length=200, blank=True, help_text="e.g. 500,000 Blooming Bulbs")
    event_dates = models.CharField(max_length=200)
    notes = RichTextField(blank=True, help_text="Notes will appear on the thumbnail image of the event on the event index page")
    body = StreamField(BLOCK_TYPES)

    content_panels = Page.content_panels + [
        ImageChooserPanel('image'),
        FieldPanel('location'),
        FieldPanel('additional_info'),
        FieldPanel('instructor'),
        FieldPanel('member_cost'),
        FieldPanel('public_cost'),
        FieldPanel('sub_heading'),
        FieldPanel('event_dates'),
        FieldPanel('notes'),
        StreamFieldPanel('body'),
    ]

    parent_page_types = ['events.EventIndexPage']


class EventGeneralPage(GeneralPage):
    event_dates = models.CharField(max_length=200)
    notes = RichTextField(blank=True, help_text="Notes will appear on the thumbnail image of the event on the event index page")
    image = GeneralPage.thumbnail  # just to match EventPage so the EventIndexPage template doesn't need to be changed

    content_panels = GeneralPage.content_panels + [
        FieldPanel('event_dates'),
        FieldPanel('notes'),
    ]

    parent_page_types = ['events.EventIndexPage']
