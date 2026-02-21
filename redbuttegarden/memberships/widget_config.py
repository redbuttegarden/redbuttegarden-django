from decimal import Decimal
from django.core.exceptions import ValidationError
from django.db import models
from wagtail.admin.panels import FieldPanel


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
