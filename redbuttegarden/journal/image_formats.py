from wagtail.images.formats import Format, register_image_format

register_image_format(Format('responive', 'Responsive', 'img-fluid', 'max-1000x800'))