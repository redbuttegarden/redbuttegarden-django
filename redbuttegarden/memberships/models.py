from django.db import models


class MembershipLevel(models.Model):
    """
    A membership *type* (examples: Individual Garden 1, Individual Experience 4, Dual Garden 2).
    Encodes the entitlements for memberships of this level.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Included cardholders (how many people are on the membership card)
    cardholders_included = models.PositiveSmallIntegerField(default=1)

    # Admissions: number of admissions allowed (per visit / per day / or global depending on rules)
    admissions_allowed = models.PositiveSmallIntegerField(default=1)

    # Number of concert tickets the membership may purchase during a member sale period
    member_sale_ticket_allowance = models.PositiveSmallIntegerField(default=0)

    price = models.DecimalField(
        max_digits=7,   # supports up to 99,999.99
        decimal_places=2,
        help_text="Price of the membership level in USD."
    )

    purchase_url = models.URLField(
        max_length=500,
        blank=True,
        help_text="URL where this membership level can be purchased."
    )

    active = models.BooleanField(default=True)  # if you ever retire a level

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
