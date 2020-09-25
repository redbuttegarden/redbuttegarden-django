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


class Heading(blocks.CharBlock):
    class Meta:
        template = 'blocks/heading.html'
        icon = 'grip'
        label = 'Heading'


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


class ColumnBlock(blocks.StreamBlock):
    heading = Heading(classname='full title',
                      help_text=_('Text will be green and centered'))
    emphatic_text = EmphaticText(classname='full title',
                                 help_text=_('Text will be red, italic and centered'))
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
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', blocks.RichTextBlock(required=True, classname='paragraph')),
        ('tan_bg_text', blocks.RichTextBlock(required=False, classname='paragraph',
                                             help_text="Paragraph with a tan background")),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
        ('dropdown_button_list', ButtonListDropdownInfo()),
        ('card_info_list', ImageListCardInfo()),
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
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', blocks.RichTextBlock()),
        ('image', ImageChooserBlock()),
        ('document', DocumentChooserBlock()),
        ('two_columns', TwoColumnBlock()),
        ('embedded_video', EmbedBlock(icon='media')),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
        ('dropdown_button_list', ButtonListDropdownInfo()),
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
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_('You only need to add a thumbnail if this page is the child of a general index page')
    )
    body = StreamField(block_types=[
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', blocks.RichTextBlock(required=True, classname='paragraph')),
        ('tan_bg_text', blocks.RichTextBlock(required=False, classname='paragraph',
                                             help_text="Paragraph with a tan background")),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('dropdown_image_list', ImageListDropdownInfo()),
        ('dropdown_button_list', ButtonListDropdownInfo()),
    ], blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            ImageChooserPanel('banner'),
            ImageChooserPanel('thumbnail'),
        ], classname="collapsible"),
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
