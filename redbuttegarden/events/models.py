import logging

from django import forms
from django.core.paginator import Paginator
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q, CheckConstraint
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from modelcluster.fields import ParentalManyToManyField
from wagtail.admin.panels import (
    FieldPanel,
    FieldRowPanel,
    HelpPanel,
    MultiFieldPanel,
    ObjectList,
    PageChooserPanel,
    TabbedInterface,
)
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail import blocks
from wagtail.blocks import PageChooserBlock
from wagtail.fields import RichTextField, StreamField
from wagtail.images.blocks import ImageBlock
from wagtail.images.models import Image
from wagtail.search import index
from wagtail.snippets.models import register_snippet

from home.abstract_models import AbstractBase
from home.models import (
    AlignedParagraphBlock,
    ButtonBlock,
    EmphaticText,
    GeneralPage,
    ImageLinkList,
    Heading,
    MultiColumnAlignedParagraphBlock,
)
from . import utils as event_utils


logger = logging.getLogger(__name__)


@register_snippet
class EventCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=80)
    parent = models.ForeignKey(
        "self",
        blank=True,
        null=True,
        related_name="children",
        help_text=_(
            "Unlike tags, categories can have a hierarchy so they can be more specifically organized."
        ),
        on_delete=models.CASCADE,
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("slug"),
        FieldPanel("parent"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Event Category")
        verbose_name_plural = _("Event Categories")


@register_snippet
class PolicyLink(models.Model):
    """
    Model for maintaining links to policy pages that can be used on many pages
    """

    name = models.CharField(
        max_length=100, help_text=_("Create a name for this policy")
    )
    link_text = models.CharField(
        max_length=500, help_text=_("This text will link to the provided policy page")
    )
    policy_page = models.ForeignKey(
        "wagtailcore.Page",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("link_text"),
        PageChooserPanel("policy_page"),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Policy Link"


class SingleListImage(blocks.StructBlock):
    image = ImageBlock(
        label="Image",
    )
    title = blocks.CharBlock(
        label="Title",
        max_length=200,
        help_text=_("Displayed right of image in h2 tag, centered and uppercase"),
    )
    sub_title = blocks.CharBlock(
        label="Subtitle",
        max_length=200,
        help_text=_("Displayed under title, centered and green"),
    )
    text = blocks.RichTextBlock(
        label="Text",
        required=False,
        help_text=_("Optional text to be displayed alongside image"),
    )
    link_url = blocks.URLBlock(
        label="Link URL",
        max_length=200,
        required=False,
        help_text=_("If provided, the link will be applied to the image"),
    )


class ListWithImagesBlock(blocks.StructBlock):
    list_items = blocks.ListBlock(
        SingleListImage(),
        label="List Item",
        help_text=_(
            "Images displayed with text to the right, all with a tan background"
        ),
    )

    class Meta:
        template = "events/list_with_images.html"
        icon = "fa-id-card-o"


class ImageRow(blocks.StructBlock):
    images = blocks.ListBlock(ImageBlock())

    class Meta:
        template = "blocks/image_row.html"


BLOCK_TYPES = [
    ("button", ButtonBlock()),
    (
        "green_heading",
        Heading(classname="full title", help_text=_("Text will be green and centered")),
    ),
    ("emphatic_text", EmphaticText(required=False, help_text="Red italic text")),
    ("paragraph", AlignedParagraphBlock(required=True, classname="paragraph")),
    ("multi_column_paragraph", MultiColumnAlignedParagraphBlock()),
    ("image", ImageBlock()),
    ("image_link_list", ImageLinkList()),
    ("html", blocks.RawHTMLBlock(required=False)),
    ("image_list", ListWithImagesBlock(required=False)),
    ("image_row", ImageRow()),
]


class EventIndexPage(RoutablePageMixin, AbstractBase):
    intro = RichTextField(blank=True)
    body = StreamField(BLOCK_TYPES + [("page_link", PageChooserBlock())], blank=True)
    order_date = models.DateTimeField(
        default=timezone.now
    )  # Allow editors to control displayed order of pages

    content_panels = AbstractBase.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body", classname="full"),
    ]

    promote_panels = AbstractBase.promote_panels + [
        FieldPanel("order_date"),
    ]

    subpage_types = [
        "events.EventPage",
        "events.EventGeneralPage",
        "events.EventIndexPage",
    ]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    def get_event_items(self):
        # This returns a Django paginator of event items in this section
        return Paginator(self.get_children().live(), 10)

    def get_cached_paths(self):
        """
        As well as invalidating the URL of the EventIndexPage itself, also invalidate each of the results pages

        :param self: EventIndexPage
        """

        return ["/"] + [
            "/?page=" + str(page_number)
            for page_number in range(1, self.get_event_items().num_pages + 1)
        ]

    @route(r"^$")
    def event_list(self, request, *args, **kwargs):
        self.events = sorted(
            self.get_children().live(), key=lambda x: x.specific.order_date
        )
        return AbstractBase.serve(self, request, *args, **kwargs)

    @route(r"^e-cat/(?P<event_category>[-\w]+)/$")
    def event_by_category(self, request, event_category, *args, **kwargs):
        self.search_type = "event-category"
        self.search_term = event_category
        self.cat_title = event_category.replace("-", " ").title()
        # We need to figure out which banner image to display based on the category
        banner_search = Image.objects.search(self.cat_title + " banner")
        if banner_search:
            self.banner = banner_search[0]
        # We want to grab all events of the given category for each Page type that has event categories
        # We also want to exclude copies so we check the page has no alias
        events = []
        event_pages = EventPage.objects.live().filter(
            event_categories__slug=event_category, alias_of__isnull=True
        )
        for event in event_pages:
            events.append(event)
        event_general_pages = EventGeneralPage.objects.live().filter(
            event_categories__slug=event_category, alias_of__isnull=True
        )
        for event in event_general_pages:
            events.append(event)
        self.events = sorted(events, key=lambda x: x.specific.order_date)
        return AbstractBase.serve(self, request, *args, **kwargs)

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by order_date
        context = super().get_context(request, *args, **kwargs)
        context["events"] = self.events
        return context


class EventPage(AbstractBase):
    location = models.CharField(max_length=100)
    additional_info = RichTextField(blank=True)
    instructor = models.CharField(max_length=100, blank=True)
    member_cost = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Price text for more flexibility (e.g. 'Free', '$35', '$25-$35'). Prefer filling the numeric field when possible.",
    )
    public_cost = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        help_text="Price text for more flexibility (e.g. 'Free', '$35', '$25-$35'). Prefer filling the numeric field when possible.",
    )
    # numeric price fields for machine-readable offers
    member_cost_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric price for members (machine-readable). Enter a number like 0.00 for Free or 35.00. Leave blank to use 'Member cost' text.",
    )
    public_cost_amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Numeric price for general public (machine-readable). Example: 35.00.",
    )
    sub_heading = models.CharField(
        max_length=200, blank=True, help_text="e.g. 500,000 Blooming Bulbs"
    )
    # Ideally event dates would only be saved as DateTime values but editors often prefer the flexibility of free text
    event_dates = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Date text for more flexibility. (e.g. 'September-October', 'All Summer', etc.) Prefer filling the Start Datetime and End Datetime when possible.",
    )
    start_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Structured start date/time for search engines. Example: 2026-03-25 10:00 AM. Use this (preferred) when the event has a single start time.",
    )
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Structured end date/time. Optional — helpful for search engines and calendar integrations.",
    )
    display_times_on_index = models.BooleanField(
        default=False,
        verbose_name="Display times on event index page thumbnail",
        help_text="Show start/end times (e.g. 9 AM) on the event index page thumbnail (thumbnail space is limited; default off)."
    )
    display_times_on_detail = models.BooleanField(
        default=True,
        verbose_name="Display times on detail page",
        help_text="Show start/end times on the event detail page (default on). Turn off to display dates only."
    )
    event_categories = ParentalManyToManyField(EventCategory, blank=True)
    notes = RichTextField(
        blank=True,
        help_text="Notes will appear on the thumbnail image of the event on the event index page",
    )
    # optional URL where tickets are purchased / registration (helps the 'url' in offers)
    purchase_url = models.URLField(
        null=True,
        blank=True,
        help_text="Optional direct registration/ticketing URL. If provided, search engines will use this when linking to the event page.",
    )
    body = StreamField(BLOCK_TYPES)
    policies = models.ManyToManyField(
        "events.PolicyLink", blank=True, related_name="event_policies"
    )
    order_date = models.DateTimeField(
        default=timezone.now
    )  # Allow editors to control displayed order of pages

    content_panels = AbstractBase.content_panels + [
        MultiFieldPanel(
            [
                HelpPanel(
                    content=(
                        "Search engines (and rich results) prefer machine-readable dates/prices. "
                        "Please fill the fields in this section when possible. "
                        "You can still use the legacy text fields below when greater flexibility is required."
                    ),
                ),
                FieldPanel(
                    "start_datetime",
                    help_text="Structured start date/time.",
                ),
                FieldPanel("end_datetime", help_text="Structured end date/time."),
                FieldPanel("display_times_on_index"),
                FieldPanel("display_times_on_detail"),
                FieldRowPanel(
                    [
                        FieldPanel(
                            "member_cost_amount",
                            classname="col6",
                            help_text="Numeric price for members, e.g. 0.00 for Free or 35.00.",
                        ),
                        FieldPanel(
                            "public_cost_amount",
                            classname="col6",
                            help_text="Numeric price for general public, e.g. 35.00.",
                        ),
                    ],
                    heading="Structured prices",
                ),
                FieldPanel("purchase_url"),
            ],
            heading="Structured event data (for search engines)",
            classname="collapsible",
        ),
        # Put legacy free-text fields into a collapsed panel
        MultiFieldPanel(
            [
                FieldPanel(
                    "member_cost",
                    help_text="Legacy free text entry price for members. Example: 'Free', '$35', '$35-$45'. Prefer using structured 'Member Cost Amount' above when possible.",
                ),
                FieldPanel(
                    "public_cost",
                    help_text="Legacy free text entry price for public. Prefer using structured 'Public Cost Amount' above when possible.",
                ),
                FieldPanel(
                    "event_dates",
                    help_text="Free text event date/time text for display (e.g. 'Sundays in May, 10am–12pm'). Prefer using 'Start Datetime'/'End Datetime' above when possible.",
                ),
            ],
            heading="Legacy event fields (use only when necessary)",
            classname="collapsed",  # collapsed by default so editors don't default to these
        ),
        FieldPanel("location"),
        FieldPanel("additional_info"),
        FieldPanel("instructor"),
        FieldPanel("sub_heading"),
        FieldPanel("notes"),
        FieldPanel("body"),
        FieldPanel(
            "policies",
            help_text="Optionally choose one or more policy links to include on the page",
        ),
    ]

    promote_panels = AbstractBase.promote_panels + [
        FieldPanel("order_date"),
    ]

    parent_page_types = ["events.EventIndexPage", "home.GeneralIndexPage"]

    search_fields = AbstractBase.search_fields + [
        index.SearchField("instructor"),
        index.SearchField("sub_heading"),
        index.SearchField("event_dates"),
        index.SearchField("notes"),
        index.SearchField("body"),
    ]

    class Meta:
        constraints = [
            # At least one of start_datetime OR event_dates (non-empty)
            CheckConstraint(
                condition=Q(start_datetime__isnull=False) | ~Q(event_dates=""),
                name="events_eventpage_start_or_event_dates_not_empty",
            ),
            # If end_datetime is set, start_datetime must be set
            CheckConstraint(
                condition=Q(end_datetime__isnull=True) | Q(start_datetime__isnull=False),
                name="events_eventpage_end_requires_start",
            ),
        ]

    def clean(self):
        """
        Enforce:
        - At least one of event_dates (non-empty) OR start_datetime must be present.
        - If end_datetime is provided, start_datetime must also be provided.
        This provides helpful ValidationError messages for the admin forms.
        """
        # call parent clean (important)
        super().clean()

        errors = {}

        # treat empty/whitespace event_dates as not provided
        has_event_dates = bool(self.event_dates and self.event_dates.strip())
        has_start = getattr(self, "start_datetime", None) is not None
        has_end = getattr(self, "end_datetime", None) is not None

        # rule 1: require at least one of event_dates or start_datetime
        if not (has_event_dates or has_start):
            # attach errors to both fields for better UX (or use NON_FIELD_ERRORS)
            msg = _(
                "Please provide a structured start date/time (preferred) or fill the human-readable 'Event dates' field."
            )
            errors["event_dates"] = msg
            errors["start_datetime"] = msg

        # rule 2: if end_datetime provided, start_datetime must be provided
        if has_end and not has_start:
            errors["end_datetime"] = _(
                "An end date/time was provided but the start date/time is missing. Please set a start date/time."
            )
            # optionally also add error to start_datetime field
            errors.setdefault(
                "start_datetime",
                _("Provide a start date/time when an end date/time is set."),
            )

        if errors:
            raise ValidationError(errors)

    def get_context(self, request, *args, **kwargs):
        """
        Ensure structured JSON is available in the template context.
        Keep other context from the parent implementation.
        """
        context = super().get_context(request, *args, **kwargs)
        # attach JSON string (safe to include in template with |safe)
        context["structured_event_json"] = event_utils.build_structured_event_json(
            self, request=request
        )
        # optionally expose dict for tests/debugging
        context["structured_event_dict"] = event_utils.build_structured_event_dict(
            self, request=request
        )
        return context

    def save(self, *args, **kwargs):
        # If editor hasn't set numeric amount but has free-text, try to infer
        if (self.member_cost_amount is None) and (self.member_cost):
            try_amount = event_utils.parse_amount_from_text(self.member_cost)
            if try_amount is not None:
                self.member_cost_amount = try_amount

        if (self.public_cost_amount is None) and (self.public_cost):
            try_amount = event_utils.parse_amount_from_text(self.public_cost)
            if try_amount is not None:
                self.public_cost_amount = try_amount

        super().save(*args, **kwargs)

    def get_cached_paths(self):
        """
        In addition to overriding the URL of this page, we also need
        to invalidate the event category view of any category to which
        this page belongs.
        """
        return ["/"] + [
            "/events/e-cat/" + category.slug for category in self.event_categories.all()
        ]


class EventGeneralPage(GeneralPage):
    event_dates = models.CharField(max_length=200)
    notes = RichTextField(
        blank=True,
        help_text="Notes will appear on the thumbnail image of the event on the event index page",
    )
    image = (
        GeneralPage.thumbnail
    )  # just to match EventPage so the EventIndexPage template doesn't need to be changed
    event_categories = ParentalManyToManyField(EventCategory, blank=True)
    order_date = models.DateTimeField(
        default=timezone.now
    )  # Allow editors to control displayed order of pages

    content_panels = GeneralPage.content_panels + [
        FieldPanel("event_dates"),
        FieldPanel("event_categories", widget=forms.CheckboxSelectMultiple),
        FieldPanel("notes"),
    ]

    promote_panels = AbstractBase.promote_panels + [
        FieldPanel("order_date"),
    ]

    parent_page_types = ["events.EventIndexPage", "home.GeneralIndexPage"]

    search_fields = GeneralPage.search_fields + [
        index.SearchField("event_dates"),
        index.SearchField("notes"),
    ]

    edit_handler = TabbedInterface(
        [
            ObjectList(content_panels, heading="Content"),
            ObjectList(AbstractBase.dialog_box_panels, heading="Dialog"),
            ObjectList(promote_panels, heading="Promote"),
            ObjectList(AbstractBase.settings_panels, heading="Settings"),
        ]
    )

    def get_cached_paths(self):
        """
        In addition to overriding the URL of this page, we also need
        to invalidate the event category view of any category to which
        this page belongs.
        """

        return ["/"] + [
            "/events/e-cat/" + category.slug for category in self.event_categories.all()
        ]
