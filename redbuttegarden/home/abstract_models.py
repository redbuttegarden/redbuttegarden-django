from django.db import models
from django.utils.translation import ugettext_lazy as _, gettext_lazy
from wagtail.admin.edit_handlers import MultiFieldPanel, TabbedInterface, ObjectList
from wagtail.core.models import Page
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.utils.decorators import cached_classmethod


class AbstractBase(Page):
    banner = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    thumbnail = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+',
        help_text=_('You only need to add a thumbnail if this page is the child of a general index page')
    )

    class Meta:
        abstract = True

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            ImageChooserPanel('banner'),
            ImageChooserPanel('thumbnail'),
        ], classname="collapsible"),
    ]

    @cached_classmethod
    def get_edit_handler(cls):
        edit_handler = TabbedInterface([
            ObjectList(cls.content_panels,
                       heading=gettext_lazy('Content')),
            ObjectList(cls.promote_panels,
                       heading=gettext_lazy('Promote')),
            ObjectList(cls.settings_panels,
                       heading=gettext_lazy('Settings'),
                       classname='settings'),
        ])
        return edit_handler.bind_to(model=cls)