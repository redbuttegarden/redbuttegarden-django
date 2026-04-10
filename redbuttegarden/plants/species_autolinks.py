from collections import defaultdict
from html import escape
from html.parser import HTMLParser
import re

from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Species


SKIP_LINK_TAGS = {"a", "code", "pre", "script", "style"}


class SpeciesHTMLAutoLinkParser(HTMLParser):
    def __init__(self, autolinker):
        super().__init__()
        self.autolinker = autolinker
        self.chunks = []
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        self.open_tags.append(tag)
        self.chunks.append(f"<{tag}{self._render_attrs(attrs)}>")

    def handle_endtag(self, tag):
        if self.open_tags and self.open_tags[-1] == tag:
            self.open_tags.pop()
        elif tag in self.open_tags:
            self.open_tags.remove(tag)
        self.chunks.append(f"</{tag}>")

    def handle_startendtag(self, tag, attrs):
        self.chunks.append(f"<{tag}{self._render_attrs(attrs)} />")

    def handle_data(self, data):
        if self._skip_current_text():
            self.chunks.append(escape(data))
            return

        self.chunks.append(self.autolinker.link_text(data))

    def handle_entityref(self, name):
        self.chunks.append(f"&{name};")

    def handle_charref(self, name):
        self.chunks.append(f"&#{name};")

    def handle_comment(self, data):
        self.chunks.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self.chunks.append(f"<!{decl}>")

    def get_html(self):
        return "".join(self.chunks)

    def _render_attrs(self, attrs):
        rendered_attrs = []
        for name, value in attrs:
            if value is None:
                rendered_attrs.append(f" {name}")
            else:
                rendered_attrs.append(f' {name}="{escape(value, quote=True)}"')
        return "".join(rendered_attrs)

    def _skip_current_text(self):
        return any(tag in SKIP_LINK_TAGS for tag in self.open_tags)


class SpeciesAutoLinker:
    def __init__(self, matches, link_renderer=None):
        self.matches = matches
        self.link_renderer = link_renderer or self._render_frontend_link
        self.pattern = self._compile_pattern(matches)

    @classmethod
    def get_unique_matches_from_database(cls):
        return {
            term: target["url"]
            for term, target in cls.get_unique_match_targets_from_database().items()
        }

    @classmethod
    def get_unique_match_targets_from_database(cls):
        species_matches = defaultdict(set)

        species_queryset = Species.objects.filter(autolink_enabled=True).only(
            "id",
            "full_name",
            "autolink_aliases",
        )

        for species in species_queryset:
            for term in species.get_autolink_terms():
                species_matches[term].add(
                    (
                        species.pk,
                        reverse("plants:species-detail", args=[species.pk]),
                    )
                )

        unique_matches = {
            term: {
                "id": species_id,
                "url": species_url,
                "linktype": "species",
            }
            for term, targets in species_matches.items()
            if len(targets) == 1
            for species_id, species_url in [next(iter(targets))]
        }
        return unique_matches

    @classmethod
    def from_database(cls):
        return cls(cls.get_unique_match_targets_from_database())

    @classmethod
    def for_rich_text_storage(cls):
        return cls(
            cls.get_unique_match_targets_from_database(),
            link_renderer=cls._render_rich_text_link,
        )

    def link_html(self, html):
        if not html or self.pattern is None:
            return html

        parser = SpeciesHTMLAutoLinkParser(self)
        parser.feed(str(html))
        parser.close()
        return mark_safe(parser.get_html())

    def link_text(self, text):
        if not text or self.pattern is None:
            return escape(text)

        linked_text = []
        last_index = 0

        for match in self.pattern.finditer(text):
            start, end = match.span()
            matched_text = match.group(0)
            matched_target = self.matches[matched_text]

            linked_text.append(escape(text[last_index:start]))
            linked_text.append(self.link_renderer(matched_text, matched_target))
            last_index = end

        linked_text.append(escape(text[last_index:]))
        return "".join(linked_text)

    def _compile_pattern(self, matches):
        if not matches:
            return None

        escaped_terms = sorted((re.escape(term) for term in matches), key=len, reverse=True)
        return re.compile(rf"(?<!\w)({'|'.join(escaped_terms)})(?!\w)")

    @staticmethod
    def _render_frontend_link(matched_text, matched_target):
        matched_url = matched_target["url"]
        return f'<a href="{escape(matched_url, quote=True)}">{escape(matched_text)}</a>'

    @staticmethod
    def _render_rich_text_link(matched_text, matched_target):
        return (
            f'<a linktype="{escape(matched_target["linktype"], quote=True)}" '
            f'id="{matched_target["id"]}">{escape(matched_text)}</a>'
        )


def autolink_rich_text_value(block, rich_text_value, autolinker=None):
    if not rich_text_value:
        return rich_text_value

    autolinker = autolinker or SpeciesAutoLinker.for_rich_text_storage()
    linked_html = autolinker.link_html(rich_text_value.source)

    if str(linked_html) == rich_text_value.source:
        return rich_text_value

    return block.normalize(str(linked_html))
