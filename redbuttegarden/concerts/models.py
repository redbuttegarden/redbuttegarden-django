import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from wagtail.contrib.table_block.blocks import TableBlock
from wagtail.core import blocks
from wagtail.images.blocks import ImageChooserBlock

from wagtail.admin.edit_handlers import FieldPanel, PageChooserPanel, StreamFieldPanel
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField, StreamField
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.search import index

from concerts.utils import live_in_the_past, on_demand_expired
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

donor_schedule_table_options = {
    'contextMenu': [
        'row_above',
        'row_below',
        '---------',
        'col_left',
        'col_right',
        '---------',
        'remove_row',
        'remove_col',
        '---------',
        'undo',
        'redo',
        '---------',
        'copy',
        'cut'
        '---------',
        'alignment',
    ],
    'minSpareRows': 0,
    'startRows': 3,
    'startCols': 4,
    'colHeaders': False,
    'rowHeaders': True,
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
        required=False,
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


class ConcertBlock(blocks.StructBlock):
    band_img = ImageChooserBlock(required=True)
    hidden = blocks. BooleanBlock(default=True, help_text=_('If hidden box is checked, concert will not be displayed on'
                                                            ' the page'), required=False)
    on_sale = blocks.BooleanBlock(default=True, help_text=_('If unchecked, Buy Tickets button will be grayed out'),
                                  required=False)
    virtual = blocks.BooleanBlock(default=False, help_text=_('Is this a virtual concert?'), required=False)
    canceled = blocks.BooleanBlock(default=False, required=False)
    postponed = blocks.BooleanBlock(default=False, required=False)
    sold_out = blocks.BooleanBlock(default=False, required=False)
    # Virtual concert will remain available on demand until this date
    available_until = blocks.DateTimeBlock(required=False, blank=True, null=True,
                                           help_text=_(
                                               'Date that on-demand virtual concert will remain available until'))
    # Band/opener names and url properties replaced with single RichTextField to account for wide variety in how the
    # bands info may be displayed
    band_info = blocks.RichTextBlock(
        help_text=_('Provide the names of the bands/openers and any other info here. Text will be'
                    ' centered.'))
    concert_dates = blocks.ListBlock(blocks.DateTimeBlock())
    gates_time = blocks.TimeBlock(default=datetime.time(hour=18), required=False, blank=True, null=True)
    show_time = blocks.TimeBlock(default=datetime.time(hour=19), required=False, blank=True, null=True)
    member_price = blocks.CharBlock(default='$', max_length=100, blank=True, null=True)
    public_price = blocks.CharBlock(default='$', max_length=100)

    # Added a ticket URL for concerts that are sold from a non-standard URL
    ticket_url = blocks.URLBlock(default='https://redbuttegarden.ticketfly.com')


class SimpleConcertBlock(blocks.StructBlock):
    """
    Simplified concert info designed for Concert Donor Schedule page.
    """
    band_img = ImageChooserBlock(required=True)
    concert_dates = blocks.ListBlock(blocks.DateTimeBlock())
    band_info = blocks.RichTextBlock(
        help_text=_('Provide the names of the bands/openers and any other info here. Text will be'
                    ' centered.'))

    class Meta:
        template = 'blocks/simple_concert_block.html'


class ConcertStreamBlock(blocks.StreamBlock):
    concerts = ConcertBlock()

    class Meta:
        required = False


class SimpleConcertStreamBlock(blocks.StreamBlock):
    concerts = SimpleConcertBlock()

    class Meta:
        required = False


class ConcertPage(AbstractBase):
    banner_link = models.URLField(help_text=_("Where to direct the banner image link"),
                                  blank=True)
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
    body = StreamField(ConcertStreamBlock(), null=True, blank=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('banner_link'),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('donor_banner'),
        PageChooserPanel('button_one'),
        PageChooserPanel('button_two'),
        PageChooserPanel('button_three'),
        PageChooserPanel('button_four'),
        StreamFieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('intro'),
    ]

    def get_context(self, request, **kwargs):
        context = super().get_context(request, **kwargs)

        context['concerts'] = self.sort_visible_concerts()
        return context

    def sort_visible_concerts(self):
        # Get a list of concert objects and determine the following:
        # Are they in the past and if they are virtual, is the on-demand offering also in the past?
        concerts = [concert.value for concert in self.body if not concert.value['hidden'] and len(concert.value['concert_dates']) > 0]
        for concert in concerts:
            concert['concert_dates'] = sorted(concert['concert_dates'])
            concert.soonest_date = sorted(concert['concert_dates'])[-1]
            concert.live_in_the_past = live_in_the_past(concert)
            concert.on_demand_expired = on_demand_expired(concert)

        # Sort concerts by soonest date
        return sorted(concerts, key=lambda x: x.soonest_date)

class LineupBlock(blocks.StructBlock):
    year = blocks.IntegerBlock(min_value=1980, required=True)
    poster = ImageChooserBlock(required=True)
    artists = blocks.RichTextBlock(required=True)

    class Meta:
        template = 'blocks/lineup_block.html'


class PastLineupStreamBlock(blocks.StreamBlock):
    lineup = LineupBlock()

    class Meta:
        required = True


class PastConcertPage(AbstractBase):
    lineups = StreamField(PastLineupStreamBlock())

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('lineups'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('lineups'),
    ]

    parent_page_types = ['concerts.ConcertPage']


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


class DonorSchedulePage(AbstractBase):
    body = StreamField(block_types=[
        ('heading', Heading(classname='full title',
                            help_text=_('Text will be green and centered'))),
        ('emphatic_text', EmphaticText(classname='full title',
                                       help_text=_('Text will be red, italic and centered'))),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('image', ImageChooserBlock()),
        ('html', blocks.RawHTMLBlock()),
        ('table', TableBlock(table_options=donor_schedule_table_options,
                             help_text=_("Right-click to add/remove rows/columns"))),
        ('concerts', SimpleConcertStreamBlock()),
    ], blank=False)


    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]
