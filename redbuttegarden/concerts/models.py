import datetime

from django.db import models

from modelcluster.fields import ParentalKey

from wagtail.admin.edit_handlers import FieldPanel, InlinePanel
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
    intro = RichTextField(blank=True)
    donor_banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        ImageChooserPanel('banner'),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('donor_banner'),
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
