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
        help_text=_('You only need to add a thumbnail if this page is the child of a another page')
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
