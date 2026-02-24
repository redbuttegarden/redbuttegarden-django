from decimal import Decimal

from django.db import models
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.search import index

from .combined_blocks import Columns2Block, ContentStreamBlock
from home.abstract_models import AbstractBase
from .widgets import MembershipWidgetBlock


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
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "cardholders_included",
                    "admissions_allowed",
                    "member_sale_ticket_allowance",
                ],
                name="uniq_membership_level_entitlements",
            ),
            models.CheckConstraint(
                condition=Q(price__gte=Decimal("0.00")),
                name="chk_membership_level_price_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(charitable_gift_amount__gte=Decimal("0.00")),
                name="chk_membership_level_gift_nonnegative",
            ),
            models.CheckConstraint(
                condition=Q(charitable_gift_amount__lte=F("price")),
                name="chk_membership_level_gift_lte_price",
            ),
        ]

    def __str__(self):
        return self.name


class MembershipPage(AbstractBase):
    body = StreamField(
        [
            ("content", ContentStreamBlock()),
            ("two_columns", Columns2Block()),
            ("membership_widget", MembershipWidgetBlock()),
        ],
        blank=True,
    )

    content_panels = AbstractBase.content_panels + [
        FieldPanel("body"),
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("body"),
    ]
