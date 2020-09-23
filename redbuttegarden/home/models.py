from django.core.paginator import Paginator
from django.db import models
from django.utils.translation import ugettext_lazy as _
from modelcluster.fields import ParentalKey

from wagtail.core import blocks
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.admin.edit_handlers import StreamFieldPanel, FieldPanel, MultiFieldPanel, InlinePanel
from wagtail.documents.blocks import DocumentChooserBlock
from wagtail.documents.edit_handlers import DocumentChooserPanel
from wagtail.embeds.blocks import EmbedBlock
from wagtail.images.blocks import ImageChooserBlock
from wagtail.images.edit_handlers import ImageChooserPanel


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


class Heading(blocks.CharBlock):
    class Meta:
        template = 'blocks/heading.html'
        icon = 'grip'
        label = 'Heading'


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


class ColumnBlock(blocks.StreamBlock):
    heading = Heading(classname='full title')
    paragraph = blocks.RichTextBlock()
    image = ImageChooserBlock()
    document = DocumentChooserBlock()
    button = ButtonBlock()

    class Meta:
        template = 'blocks/column.html'


class TwoColumnBlock(blocks.StructBlock):
    left_column = ColumnBlock(icon='arrow-left', label='Left column content')
    right_column = ColumnBlock(icon='arrow-right', label='Right column content')

    class Meta:
        template = 'blocks/two_column_block.html'
        icon = 'placeholder'
        label = 'Two Columns'


class GeneralPage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_('You only need to add a thumbnail if this page is the child of a general index page')
    )
    body = StreamField(block_types=[
        ('button', ButtonBlock()),
        ('heading', Heading(classname='full title')),
        ('paragraph', blocks.RichTextBlock(required=True, classname='paragraph')),
        ('tan_bg_text', blocks.RichTextBlock(required=False, classname='paragraph',
                                             help_text="Paragraph with a tan background")),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
    ], blank=False)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            ImageChooserPanel('banner'),
            ImageChooserPanel('thumbnail'),
        ], classname="collapsible"),
        StreamFieldPanel('body'),
    ]


class TwoColumnGeneralPage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_('You only need to add a thumbnail if this page is the child of a general index page')
    )
    body = StreamField(block_types=([
        ('heading', Heading(classname='full title')),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('document', DocumentChooserBlock()),
        ('two_columns', TwoColumnBlock()),
        ('embedded_video', EmbedBlock(icon='media')),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
    ]), null=True, blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            ImageChooserPanel('banner'),
            ImageChooserPanel('thumbnail'),
        ], classname="collapsible"),
        StreamFieldPanel('body'),
    ]


class PlantCollectionsPage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    intro = RichTextField()
    more_info_modal = RichTextField()

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner'),
        FieldPanel('intro'),
        FieldPanel('more_info_modal'),
        InlinePanel('plant_collections', label=_('Plant Collection')),
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


class GeneralIndexPage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    body = StreamField(block_types=[
        ('heading', Heading(classname='full title')),
        ('paragraph', blocks.RichTextBlock(required=True, classname='paragraph')),
        ('tan_bg_text', blocks.RichTextBlock(required=False, classname='paragraph',
                                             help_text="Paragraph with a tan background")),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
    ], blank=True)

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner'),
        StreamFieldPanel('body'),
    ]

    subpage_types = ['home.GeneralIndexPage', 'home.GeneralPage', 'home.TwoColumnGeneralPage']

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
        context = super().get_context(request)
        sub_pages = self.get_children().live().order_by('-latest_revision_created_at')
        context['sub_pages'] = sub_pages
        return context


class HomePage(Page):
    pass
