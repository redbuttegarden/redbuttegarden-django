from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import (
    FieldPanel,
)

from wagtail.fields import RichTextField, StreamField
from wagtail.search import index

from .blocks import Columns2Block, ContentStreamBlock
from home.abstract_models import AbstractBase


class MembershipWidgetConfig(models.Model):
    page_header_text = models.CharField(
        help_text="Header text at top of page",
        default="Find the best membership for you",
    )
    widget_header_text = models.CharField(
        help_text="Header text above membership widget form inputs",
        default="Your needs",
    )

    cardholder_label = models.CharField(
        help_text="Label used for cardholders", default="Cardholders"
    )
    admissions_label = models.CharField(
        help_text="Label used for admissions",
        default="Additional Admission Guest Entry",
    )
    member_tickets_label = models.CharField(
        help_text="Label for member tickets",
        default="Concert Series Pre-Sale Member Tickets",
    )

    cardholder_help_hover = models.CharField(
        help_text="Help text to appear when hovering over question mark beside cardholder entry field"
    )
    admissions_help_hover = models.CharField(
        help_text="Help text to appear when hovering over question mark beside admissions entry field"
    )
    member_tickets_help_hover = models.CharField(
        help_text="Help text to appear when hovering over question mark beside member tickets entry field"
    )

    presale_qualification_error_message_template = models.TextField(
        default=(
            "To qualify for Red Butte Garden Outdoor Concert Member Presale access at the {tickets} "
            "ticket level, please add a combination of cardholders and guests that is equal to or "
            "greater than {tickets}."
        ),
        help_text="Use {tickets} as a placeholder. Example output will replace {tickets} with 2, 4, or 6.",
    )

    auto_renewal_discount = models.DecimalField(
        max_digits=4,  # supports up to 99.99
        decimal_places=2,
        help_text="Auto renewal discount amount in USD. Set to zero to disable.",
        default=Decimal(0),
    )

    panels = [
        FieldPanel("page_header_text"),
        FieldPanel("widget_header_text"),
        FieldPanel("cardholder_label"),
        FieldPanel("admissions_label"),
        FieldPanel("member_tickets_label"),
        FieldPanel("cardholder_help_hover"),
        FieldPanel("admissions_help_hover"),
        FieldPanel("member_tickets_help_hover"),
        FieldPanel("presale_qualification_error_message_template"),
        FieldPanel("auto_renewal_discount"),
    ]

    class Meta:
        verbose_name = "Membership widget configuration"
        verbose_name_plural = "Membership widget configuration"

    def clean(self):
        super().clean()
        # Enforce singleton: only one instance allowed
        if not self.pk and MembershipWidgetConfig.objects.exists():
            raise ValidationError(
                "Only one MembershipWidgetConfig instance is allowed."
            )

    def __str__(self):
        return "Membership widget configuration"

    @classmethod
    def get_solo(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class MembershipLabel(models.Model):
    """
    Allow labels used by Membership Levels to be user editable
    """

    name = models.CharField(help_text="Name for this label group")

    cardholder_label = models.CharField(
        help_text="Label used for cardholders, e.g. 'Cardholders'"
    )
    admissions_label = models.CharField(
        help_text="Label used for admissions, e.g. 'Guests per visit'"
    )
    member_tickets_label = models.CharField(
        help_text="Label for member tickets, e.g. 'Member concert tickets'"
    )

    def __repr__(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name


class MembershipLevel(models.Model):
    """
    A membership *type* (examples: Individual Garden 1, Individual Experience 4, Dual Garden 2).
    Encodes the entitlements for memberships of this level.
    """

    labels = models.ForeignKey(MembershipLabel, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=100, unique=True)
    description = RichTextField(
        blank=True, features=["link", "bold", "italic"]  # keep this minimal
    )
    tooltip = RichTextField(
        blank=True, features=["link", "bold", "italic"], help_text="Displayed on hover"
    )

    # Included cardholders (how many people are on the membership card)
    cardholders_included = models.PositiveSmallIntegerField(default=1)

    # Admissions: number of admissions allowed (per visit / per day / or global depending on rules)
    admissions_allowed = models.PositiveSmallIntegerField(default=1)

    # Number of concert tickets the membership may purchase during a member sale period
    member_sale_ticket_allowance = models.PositiveSmallIntegerField(default=0)

    price = models.DecimalField(
        max_digits=7,  # supports up to 99,999.99
        decimal_places=2,
        help_text="Price of the membership level in USD.",
    )

    charitable_gift_amount = models.DecimalField(
        max_digits=7,  # supports up to 99,999.99
        decimal_places=2,
        help_text="Charitable gift amount in USD.",
        default=Decimal(0),
    )

    purchase_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL where this membership level can be purchased.",
    )

    active = models.BooleanField(default=True)  # if you ever retire a level

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class MembershipPage(AbstractBase):
    body = StreamField(
        [
            ("content", ContentStreamBlock()),
            ("two_columns", Columns2Block()),
        ],
        blank=True
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
    ]
