import datetime
import logging

import code128
from django.conf import settings
from django.contrib import messages
from django.core.files.base import ContentFile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

from wagtail.contrib.table_block.blocks import TableBlock
from wagtail import blocks
from wagtail.images.blocks import ImageChooserBlock

from wagtail.admin.panels import FieldPanel, PageChooserPanel
from wagtail.fields import RichTextField, StreamField
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

logger = logging.getLogger(__name__)


class CometChatBlock(blocks.StaticBlock):
    """
    Very simple block that simply enables the ability to choose where
    on the page the CometChat javascript will be rendered.
    """

    class Meta:
        template = 'blocks/comet_chat_block.html'
        label = 'Comet Chat'
        icon = 'comment'
        admin_text = 'Determines where the chat window will appear on the page.'


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
    wave = blocks.ChoiceBlock(choices=[
        (1, 'Wave 1'),
        (2, 'Wave 2')
    ], required=False)
    hidden = blocks.BooleanBlock(default=True, help_text=_('If hidden box is checked, concert will not be displayed on'
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
    ticket_url = blocks.URLBlock(
        default='https://www.etix.com/ticket/e/1035223/2023-season-salt-lake-city-red-butte-garden')

    class Meta:
        icon = 'music'


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
    wave_one_info = RichTextField(blank=True, help_text=_('Displayed at the top of the list of concerts'))
    wave_two_info = RichTextField(blank=True, help_text=_('Displayed above any wave 2 concerts (if there are any)'))
    wave_two_sale_date = models.DateField(default=None, null=True, blank=True)
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
    body = StreamField(ConcertStreamBlock(), null=True, blank=True, use_json_field=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('banner_link'),
        FieldPanel('intro', classname="full"),
        FieldPanel('donor_banner'),
        PageChooserPanel('button_one'),
        PageChooserPanel('button_two'),
        PageChooserPanel('button_three'),
        PageChooserPanel('button_four'),
        FieldPanel('wave_one_info', classname="full"),
        FieldPanel('wave_two_info', classname="full"),
        FieldPanel('wave_two_sale_date'),
        FieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('intro'),
    ]

    def get_context(self, request, **kwargs):
        context = super().get_context(request, **kwargs)

        concerts = self.get_visible_concerts()
        if self.wave_two_sale_date and datetime.date.today() < self.wave_two_sale_date:
            context['wave_one_concerts'] = self.sort_concerts(
                [concert for concert in concerts if concert['wave'] and concert['wave'] == '1'])
            context['wave_two_concerts'] = self.sort_concerts(
                [concert for concert in concerts if concert['wave'] and concert['wave'] == '2'])
        else:
            context['concerts'] = self.sort_concerts(concerts)
        return context

    def get_visible_concerts(self):
        return [concert.value for concert in self.body if
                concert.block_type == 'concerts' and not concert.value['hidden'] and len(
                    concert.value['concert_dates']) > 0]

    def sort_concerts(self, concerts):
        # Determine the following:
        # Are they in the past and if they are virtual, is the on-demand offering also in the past?
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
    lineups = StreamField(PastLineupStreamBlock(), use_json_field=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('lineups'),
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
        ('table', TableBlock(table_options=donor_schedule_table_options,
                             help_text=_("Right-click to add/remove rows/columns"))),
    ], blank=False, use_json_field=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('body'),
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
    ], blank=False, use_json_field=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]


class ConcertDonorClubPortalPage(AbstractBase):
    body = StreamField(block_types=[
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph')),
        ('html', blocks.RawHTMLBlock()),
    ], blank=False, use_json_field=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, **kwargs)

        if request.user.is_authenticated:
            cdc_member = ConcertDonorClubMember.objects.get(user=request.user)

            if cdc_member:
                context['cdc_member'] = cdc_member
            else:
                messages.add_message(request, messages.WARNING, "No matching Concert Donor Club membership found.")

        return context


class ConcertDonorClubTicketSalePage(AbstractBase):
    body = StreamField(block_types=[
        ('chat', CometChatBlock()),
        ('paragraph', AlignedParagraphBlock(required=True, classname='paragraph'))
    ], blank=False, use_json_field=True)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('body'),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField('body'),
    ]

    parent_page_types = ['home.GeneralPage', 'concerts.ConcertDonorClubPortalPage']

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, **kwargs)

        context['app_ID'] = settings.COMET_CHAT_APP_ID
        context['app_region'] = settings.COMET_CHAT_REGION
        context['auth_key'] = settings.COMET_CHAT_AUTH_KEY
        context['widget_ID'] = settings.COMET_CHAT_WIDGET_ID
        context['user_name'] = request.user.get_full_name()

        return context


class Concert(models.Model):
    etix_id = models.PositiveBigIntegerField(primary_key=True)
    name = models.CharField(max_length=300)
    begin = models.DateTimeField()
    end = models.DateTimeField()
    doors_before_event_time_minutes = models.PositiveSmallIntegerField(default=0)
    image_url = models.CharField(max_length=500, blank=True, null=True)

    class Meta:
        ordering = ['begin', 'name']

    def __str__(self):
        return f'{self.name} ({self.begin.year})'


class ConcertDonorClubPackage(models.Model):
    name = models.CharField(max_length=150)
    year = models.IntegerField(_('year'), validators=[MinValueValidator(1984), MaxValueValidator(2099)])
    concerts = models.ManyToManyField(Concert, blank=True)

    class Meta:
        ordering = ['-year', 'name']

    def __str__(self):
        return f'{self.name} ({self.year})'


class ConcertDonorClubMember(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True
    )
    phone_number = models.CharField(max_length=150)
    packages = models.ManyToManyField(ConcertDonorClubPackage, blank=True)

    class Meta:
        ordering = ['user']

    def __str__(self):
        return str(self.user)


class Ticket(models.Model):
    owner = models.ForeignKey(ConcertDonorClubMember, on_delete=models.CASCADE)
    concert = models.ForeignKey(Concert, on_delete=models.CASCADE)
    package = models.ForeignKey(ConcertDonorClubPackage, on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.PositiveBigIntegerField()
    # We wouldn't need to store the ticket if it were VOID or RESERVED so those aren't used as valid status options
    status = models.CharField(max_length=20,
                              choices=[('ISSUED', 'Issued'), ('REDEEMED', 'Redeemed'), ('RESERVED', 'Reserved')],
                              blank=True, null=True)
    barcode = models.PositiveBigIntegerField(unique=True)
    barcode_image = models.ImageField(upload_to='tickets', blank=True, null=True)

    class Meta:
        ordering = ['barcode', 'concert__name']

    def __str__(self):
        return f'{self.barcode} ({self.concert})'

    def save(self, **kwargs):
        logger.debug(f'Saving ticket {self}')
        if self.barcode and not self.barcode_image:
            self.barcode_image.save(f'{self.barcode}.svg',
                                    ContentFile(bytes(code128.svg(self.barcode), encoding='utf-8')), save=False)

        super().save(**kwargs)
