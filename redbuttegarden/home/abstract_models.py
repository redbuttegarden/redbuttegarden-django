import logging

from django import forms
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import Page
from wagtail.documents import get_document_model_string

logger = logging.getLogger(__name__)


class AbstractBase(Page):
    banner = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    thumbnail = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_(
            "You only need to add a thumbnail if this page is the child of a another page"
        ),
    )
    custom_css = models.ForeignKey(
        get_document_model_string(),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text=_(
            "Upload a CSS file to apply custom styling to this page. Note that editing an existing document will apply "
            "the changes to ALL pages where the document is used"
        ),
        verbose_name="Custom CSS",
    )
    dialog_display = models.BooleanField(
        help_text=_("Should this dialog be displayed?"),
        null=True,
        blank=True,
        default=False,
    )
    dialog_title = models.CharField(
        help_text=_("Title for pop-up dialog box"),
        max_length=100,
        null=True,
        blank=True,
    )
    dialog_content = RichTextField(
        help_text=_("Main content of the dialog box"), null=True, blank=True
    )
    dialog_style = models.CharField(
        choices=[("corner", "Corner"), ("full", "Full Page")],
        null=True,
        blank=True,
        max_length=6,
    )

    class Meta:
        abstract = True

    content_panels = Page.content_panels + [
        MultiFieldPanel(
            [FieldPanel("banner"), FieldPanel("thumbnail"), FieldPanel("custom_css")],
            classname="collapsible",
        ),
    ]

    dialog_box_panels = [
        FieldPanel("dialog_display", widget=forms.CheckboxInput),
        FieldPanel("dialog_title"),
        FieldPanel("dialog_content"),
        FieldPanel("dialog_style"),
    ]

    @cached_property
    def canonical_page(self):
        # For real alias pages, point back to the source; otherwise self
        source = (
            getattr(self, "alias_of", None)
            or getattr(self, "get_alias_of", lambda: None)()
        )
        return source or self

    @property
    def canonical_url(self):
        """
        Absolute canonical URL as a string, suitable for <link rel="canonical">.
        """
        # full_url is Wagtail's absolute URL incl. scheme + domain
        return self.canonical_page.full_url

    def save(self, clean=True, user=None, log_action=False, **kwargs):
        """
        If this page is new and it's parent is aliased, created an
        alias of this page under the alias of the parent as well.
        """
        is_new = self.id is None
        super().save(self, **kwargs)

        parent_aliases = self.get_parent().aliases.all()

        if is_new and parent_aliases:
            for alias in parent_aliases:
                self.create_alias(parent=alias, user=self.owner)
