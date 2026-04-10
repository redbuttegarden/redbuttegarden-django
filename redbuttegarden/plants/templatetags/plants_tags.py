from django import template

from plants.species_autolinks import SpeciesAutoLinker


register = template.Library()


def _is_journal_page(page):
    specific_page = getattr(page, "specific", page)
    page_meta = getattr(specific_page, "_meta", None)

    return bool(
        page_meta
        and page_meta.app_label == "journal"
        and page_meta.model_name == "journalpage"
    )


def _get_species_autolinker(context):
    request = context.get("request")
    autolinker = getattr(request, "_species_autolinker", None) if request else None

    if autolinker is None:
        autolinker = SpeciesAutoLinker.from_database()
        if request is not None:
            request._species_autolinker = autolinker

    return autolinker


@register.simple_tag(takes_context=True)
def species_autolinks(context, html):
    if not html:
        return ""

    if not _is_journal_page(context.get("page")):
        return html

    return _get_species_autolinker(context).link_html(html)


@register.simple_tag(takes_context=True)
def species_autolinks_any_page(context, html):
    if not html:
        return ""

    return _get_species_autolinker(context).link_html(html)
