from wagtail import hooks
from django.contrib import messages


@hooks.register("before_publish_page")
def before_publish_page(request, page):
    if hasattr(page, "start_datetime") and not page.start_datetime:
        messages.warning(
            request,
            "This page has no structured start date. Adding one improves search results.",
        )
