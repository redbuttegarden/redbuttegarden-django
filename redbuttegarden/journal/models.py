from django import forms
from django.conf import settings
from django.core.paginator import Paginator
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalManyToManyField, ParentalKey
from taggit.models import TaggedItemBase, Tag as TaggitTag
from wagtail.admin.edit_handlers import FieldPanel, InlinePanel, StreamFieldPanel
from wagtail.contrib.routable_page.models import RoutablePageMixin, route
from wagtail.core.fields import StreamField
from wagtail.core.models import Page, Orderable
from wagtail.images.edit_handlers import ImageChooserPanel
from wagtail.snippets.models import register_snippet

from events.models import BLOCK_TYPES
from home.abstract_models import AbstractBase


@register_snippet
class JournalCategory(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=80)

    panels = [
        FieldPanel('name'),
        FieldPanel('slug'),
    ]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Category")
        verbose_name_plural = _("Categories")


@register_snippet
class Tag(TaggitTag):
    class Meta:
        proxy = True


class JournalPageTag(TaggedItemBase):
    content_object = ParentalKey('JournalPage', related_name='journal_tags')


class JournalIndexPage(RoutablePageMixin, AbstractBase):
    body = StreamField(block_types=BLOCK_TYPES, blank=True, null=True)

    content_panels = AbstractBase.content_panels + [
        StreamFieldPanel('body'),
    ]

    subpage_types = ['journal.JournalPage']

    def get_context(self, request, *args, **kwargs):
        # Update context to include only published posts, ordered by reverse-chron
        context = super().get_context(request, *args, **kwargs)
        posts = JournalPage.objects.child_of(self).order_by('-date')
        context['posts'] = posts
        return context

    def get_posts(self):
        """
        Method of returning JournalPage objects that can be further filtered
        """
        return JournalPage.objects.descendant_of(self).live()

    def get_journal_items(self):
        # This returns a Django paginator of blog items in this section
        return Paginator(self.get_children().live(), 6)

    def get_cached_paths(self):
        # Yield the main URL
        yield '/'

        # Yield one URL per page in the paginator to make sure all pages are purged
        for page_number in range(1, self.get_journal_items().num_pages + 1):
            yield '/?page=' + str(page_number)

    @route(r'^tag/(?P<tag>[-\w]+)/$')
    def post_by_tag(self, request, tag, *args, **kwargs):
        self.search_type = 'tag'
        self.search_term = tag
        self.posts = self.get_posts().filter(tags__slug=tag)
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^category/(?P<category>[-\w]+)/$')
    def post_by_category(self, request, category, *args, **kwargs):
        self.search_type = 'category'
        self.search_term = category
        self.posts = self.get_posts().filter(categories__slug=category)
        return Page.serve(self, request, *args, **kwargs)

    @route(r'^$')
    def post_list(self, request, *args, **kwargs):
        self.posts = self.get_journal_items()
        return Page.serve(self, request, *args, **kwargs)


class JournalPage(AbstractBase):
    authors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        verbose_name=_('Authors'),
        related_name='author_posts'
    )
    date = models.DateTimeField(verbose_name="Post date", default=timezone.now)
    categories = ParentalManyToManyField('journal.JournalCategory', blank=True)
    tags = ClusterTaggableManager(through='journal.JournalPageTag', blank=True)
    body = StreamField(BLOCK_TYPES)

    content_panels = AbstractBase.content_panels + [
        FieldPanel('categories', widget=forms.CheckboxSelectMultiple),
        FieldPanel('tags'),
        InlinePanel('gallery_images', label=_('gallery images'),
                    help_text=_("Gallery images are displayed along the left side of the page")),
        StreamFieldPanel('body'),
    ]

    promote_panels = AbstractBase.promote_panels + [
        FieldPanel('authors', help_text=_("If left blank, this will be set to the currently logged in user")),
        FieldPanel('date')
    ]

    parent_page_types = ['journal.JournalIndexPage']

    @property
    def journal_index_page(self):
        return self.get_parent().specific

    def get_context(self, request, *args, **kwargs):
        context = super(JournalPage, self).get_context(request, *args, **kwargs)
        context['journal_index_page'] = self.journal_index_page
        context['post'] = self
        return context

    def save_revision(self, *args, **kwargs):
        if not self.authors:
            self.authors.add(self.owner)
        return super().save_revision(*args, **kwargs)


class JournalPageGalleryImage(Orderable):
    page = ParentalKey(JournalPage, blank=True, null=True, on_delete=models.SET_NULL, related_name='gallery_images')
    image = models.ForeignKey(
        'wagtailimages.Image', blank=True, null=True, on_delete=models.SET_NULL, related_name='+'
    )
    caption = models.CharField(blank=True, max_length=255, help_text=_("Displayed below the image in italics"))

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('caption'),
    ]
