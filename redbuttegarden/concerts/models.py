import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey
from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel, StreamFieldPanel
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.images.edit_handlers import ImageChooserPanel

from home.abstract_models import AbstractBase
from home.models import Heading, EmphaticText, AlignedParagraphBlock

donor_table_options = {
    'minSpareRows': 0,
    'startRows': 3,
    'startCols': 6,
    'colHeaders': True,
    'rowHeaders': True,
    'contextMenu': True,
    'editor': 'text',
    'stretchH': 'all',
    'height': 216,
    'language': 'en-US',
    'renderer': 'text',
    'autoColumnSize': False,
}

info_card_table_options = {
    'minSpareRows': 0,
    'startRows': 2,
    'startCols': 4,
    'colHeaders': True,
    'rowHeaders': True,
    'contextMenu': True,
    'editor': 'text',
    'stretchH': 'all',
    'height': 216,
    'language': 'en-US',
    'renderer': 'text',
    'autoColumnSize': False,
}


class Sponsors(blocks.StructBlock):
    sponsor_title = blocks.CharBlock(
        label='Sponsor Title',
        max_length=200,
    )
    sponsor_url = blocks.URLBlock(
        label="URL to sponsor website"
    )
    sponsor_logo = ImageChooserBlock()


class SponsorList(blocks.StructBlock):
    list_items = blocks.ListBlock(
        Sponsors(),
        label="Sponsors"
    )

    class Meta:
        template = 'blocks/sponsor_list.html'


class ButtonTable(blocks.StructBlock):
    button_text = blocks.CharBlock(
        label="Button text"
    )
    table_list = blocks.StreamBlock([
        ('title', Heading()),
        ('table', TableBlock(table_options=donor_table_options,
                             help_text=_("Right-click to add/remove rows/columns"))),
    ])

    class Meta:
        template = 'blocks/button_table.html'


class TableInfoCard(blocks.StructBlock):
    body = blocks.StreamBlock([
        ('heading', Heading()),
        ('paragraph', AlignedParagraphBlock()),
        ('table', TableBlock(table_options=info_card_table_options))
    ])


class TableInfoCardList(blocks.StructBlock):
    list_items = blocks.ListBlock(
        TableInfoCard(),
        label="List of info cards with tables"
    )

    class Meta:
        template = 'blocks/table_info_card_list.html'


class ConcertPage(AbstractBase):
    banner_link = models.URLField(default='/',
                                  help_text=_("Where to direct the banner image link"))
    intro = RichTextField(blank=True)
    donor_banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    button_one = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    button_two = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    button_three = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )
    button_four = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel('banner_link'),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('donor_banner'),
        PageChooserPanel('button_one'),
        PageChooserPanel('button_two'),
        PageChooserPanel('button_three'),
        PageChooserPanel('button_four'),
        InlinePanel('concerts', label='Concerts')
    ]


class Concert(Orderable):
    page = ParentalKey(ConcertPage, on_delete=models.CASCADE, related_name='concerts')
    band_img = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=False,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    band_name = models.CharField(max_length=255, blank=False)
    band_url = models.URLField()
    opener_name = models.CharField(max_length=255, blank=True)
    opener_url = models.URLField(blank=True)

    concert_date = models.DateField(blank=True)
    gates_time = models.TimeField(default=datetime.time(hour=18))
    show_time = models.TimeField(default=datetime.time(hour=19))
    member_price = models.IntegerField()
    public_price = models.IntegerField()

    panels = [
        ImageChooserPanel('band_img'),
        FieldPanel('band_name'),
        FieldPanel('band_url'),
        FieldPanel('opener_name'),
        FieldPanel('opener_url'),

        FieldPanel('concert_date'),
        FieldPanel('gates_time'),
        FieldPanel('show_time'),
        FieldPanel('member_price'),
        FieldPanel('public_price'),
    ]


class DonorPackagePage(AbstractBase):
    body = StreamField(block_types=[
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('sponsor_list', SponsorList()),
        ('button_table', ButtonTable()),
        ('table_cards', TableInfoCardList()),
    ], blank=False)

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]
