import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, PageChooserPanel
from wagtail.core.models import Page, Orderable
from wagtail.core.fields import RichTextField
from wagtail.images.edit_handlers import ImageChooserPanel


class ConcertPage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
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

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner'),
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


class DonorPackagePage(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
