from django.core.paginator import Paginator
from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.admin.edit_handlers import InlinePanel
from wagtail.admin.panels import FieldPanel
from wagtail.contrib.settings.models import BaseSetting
from wagtail.contrib.settings.registry import register_setting
from wagtail.core.models import Page, Orderable


class Product(Page):
    sku = models.CharField(max_length=255)
    short_description = models.TextField(blank=True, null=True)
    price = models.DecimalField(decimal_places=2, max_digits=10)
    image = models.ForeignKey(
        'wagtailimages.Image',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    content_panels = Page.content_panels + [
        FieldPanel('sku'),
        FieldPanel('price'),
        FieldPanel('image'),
        FieldPanel('short_description'),
        InlinePanel('custom_fields', label='Custom fields'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        fields = []
        for f in self.custom_fields.get_object_list():  # custom_fields defined in ProductCustomField model
            if f.options:
                f.options_array = f.options.split('|')
                fields.append(f)
            else:
                fields.append(f)

        context['custom_fields'] = fields

        return context


class ProductCustomField(Orderable):
    product = ParentalKey(Product, on_delete=models.CASCADE, related_name='custom_fields')
    name = models.CharField(max_length=255)
    options = models.CharField(max_length=500, null=True, blank=True)

    panels = [
        FieldPanel('name'),
        FieldPanel('options')
    ]


@register_setting
class SnipcartSettings(BaseSetting):
    api_key = models.CharField(
        max_length=255,
        help_text='Your Snipcart public API key'
    )


class ShopIndexPage(Page):

    subpage_types = ['shop.Product']

    def get_product_items(self):
        # This returns a Django paginator of blog items in this section
        return Paginator(self.get_children().live(), 6)

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)

        context['products'] = Product.objects.child_of(self).live()

        return context
