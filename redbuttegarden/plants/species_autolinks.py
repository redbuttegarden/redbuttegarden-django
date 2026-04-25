from collections import defaultdict
from functools import lru_cache
from html import escape
from html import unescape
from html.parser import HTMLParser
import re

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import Species


SKIP_LINK_TAGS = {"a", "code", "pre", "script", "style"}
AUTOLINK_IGNORED_INLINE_TAGS = {"b", "strong"}
TEXT_BOUNDARY_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "dd",
    "div",
    "dl",
    "dt",
    "figcaption",
    "figure",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


class SpeciesHTMLAutoLinkParser(HTMLParser):
    def __init__(self, autolinker):
        super().__init__()
        self.autolinker = autolinker
        self.chunks = []
        self.buffered_tokens = []
        self.open_tags = []

    def handle_starttag(self, tag, attrs):
        self.open_tags.append(tag)
        rendered_tag = f"<{tag}{self._render_attrs(attrs)}>"
        if tag in SKIP_LINK_TAGS or tag in TEXT_BOUNDARY_TAGS:
            self._flush_buffered_tokens()
            self.chunks.append(rendered_tag)
        else:
            self.buffered_tokens.append(
                {
                    "type": "starttag",
                    "tag": tag,
                    "html": rendered_tag,
                    "end_html": f"</{tag}>",
                }
            )

    def handle_endtag(self, tag):
        was_skipping = self._skip_current_text()
        if self.open_tags and self.open_tags[-1] == tag:
            self.open_tags.pop()
        elif tag in self.open_tags:
            self.open_tags.remove(tag)

        rendered_tag = f"</{tag}>"
        if was_skipping or tag in SKIP_LINK_TAGS or tag in TEXT_BOUNDARY_TAGS:
            self._flush_buffered_tokens()
            self.chunks.append(rendered_tag)
        else:
            self.buffered_tokens.append(
                {"type": "endtag", "tag": tag, "html": rendered_tag}
            )

    def handle_startendtag(self, tag, attrs):
        self._flush_buffered_tokens()
        self.chunks.append(f"<{tag}{self._render_attrs(attrs)} />")

    def handle_data(self, data):
        if self._skip_current_text():
            self._flush_buffered_tokens()
            self.chunks.append(escape(data))
            return

        self._append_text_token(data, escape(data))

    def handle_entityref(self, name):
        self._append_character_reference(f"&{name};")

    def handle_charref(self, name):
        self._append_character_reference(f"&#{name};")

    def handle_comment(self, data):
        self._flush_buffered_tokens()
        self.chunks.append(f"<!--{data}-->")

    def handle_decl(self, decl):
        self._flush_buffered_tokens()
        self.chunks.append(f"<!{decl}>")

    def get_html(self):
        self._flush_buffered_tokens()
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

    def _append_character_reference(self, html):
        if self._skip_current_text():
            self._flush_buffered_tokens()
            self.chunks.append(html)
            return

        self._append_text_token(unescape(html), html)

    def _append_text_token(self, plain_text, html):
        if (
            self.buffered_tokens
            and self.buffered_tokens[-1]["type"] == "text"
        ):
            self.buffered_tokens[-1]["plain_text"] += plain_text
            self.buffered_tokens[-1]["html"] += html
            return

        self.buffered_tokens.append(
            {"type": "text", "plain_text": plain_text, "html": html}
        )

    def _flush_buffered_tokens(self):
        if not self.buffered_tokens:
            return

        self.chunks.append(self.autolinker.link_tokens(self.buffered_tokens))
        self.buffered_tokens = []


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
            "subspecies",
            "variety",
            "subvariety",
            "forma",
            "subforma",
            "cultivar",
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
        if cls is SpeciesAutoLinker:
            return _get_cached_frontend_autolinker()
        return cls(cls.get_unique_match_targets_from_database())

    @classmethod
    def for_rich_text_storage(cls):
        if cls is SpeciesAutoLinker:
            return _get_cached_rich_text_autolinker()
        return cls(
            cls.get_unique_match_targets_from_database(),
            link_renderer=cls._render_rich_text_link,
        )

    @classmethod
    def clear_cached_autolinkers(cls):
        _get_cached_frontend_autolinker.cache_clear()
        _get_cached_rich_text_autolinker.cache_clear()

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

    def link_tokens(self, tokens):
        if not tokens or self.pattern is None:
            return "".join(token.get("html", "") for token in tokens)

        plain_text = ""
        text_token_ranges = {}
        token_positions = {}
        for index, token in enumerate(tokens):
            token_positions[index] = len(plain_text)
            if token["type"] != "text":
                continue

            start = len(plain_text)
            plain_text += token["plain_text"]
            text_token_ranges[index] = (start, len(plain_text))

        matches = list(self.pattern.finditer(plain_text))
        if not matches:
            return "".join(token["html"] for token in tokens)

        return self._render_linked_tokens(
            tokens,
            token_positions,
            text_token_ranges,
            matches,
        )

    def _render_linked_tokens(self, tokens, token_positions, text_token_ranges, matches):
        linked_tokens = []
        active_link = None
        active_link_tags = []
        skipped_tags = []
        match_index = 0

        def next_match():
            if match_index >= len(matches):
                return None
            return matches[match_index]

        def open_link(match):
            target = self.matches[match.group(0)]
            linked_tokens.append(self._render_link_start(target))
            return match

        def close_link(reopen_tags=False):
            if active_link is None:
                return

            if reopen_tags:
                for tag in reversed(active_link_tags):
                    linked_tokens.append(tag["end_html"])

            linked_tokens.append("</a>")

            if reopen_tags:
                for tag in active_link_tags:
                    linked_tokens.append(tag["html"])

        for index, token in enumerate(tokens):
            token_position = token_positions[index]

            if token["type"] in {"starttag", "endtag"}:
                match = next_match()
                if (
                    active_link is None
                    and match
                    and token["type"] == "starttag"
                    and match.start() <= token_position < match.end()
                ):
                    active_link = open_link(match)

                if token["type"] == "starttag":
                    if (
                        token["tag"] in AUTOLINK_IGNORED_INLINE_TAGS
                        and active_link is not None
                    ):
                        skipped_tags.append(token["tag"])
                        continue

                    linked_tokens.append(token["html"])
                    if active_link is not None:
                        active_link_tags.append(token)
                    continue

                if skipped_tags and skipped_tags[-1] == token["tag"]:
                    skipped_tags.pop()
                    continue

                linked_tokens.append(token["html"])
                if active_link is not None and active_link_tags:
                    for tag_index in range(len(active_link_tags) - 1, -1, -1):
                        if active_link_tags[tag_index]["tag"] == token["tag"]:
                            del active_link_tags[tag_index]
                            break

                    if (
                        active_link_tags == []
                        and active_link is not None
                        and token_position >= active_link.end()
                    ):
                        close_link()
                        active_link = None
                        match_index += 1
                continue

            token_start, token_end = text_token_ranges[index]
            text = token["plain_text"]
            local_index = 0

            while token_start + local_index < token_end:
                current_position = token_start + local_index
                match = active_link or next_match()

                if match is None or match.end() <= current_position:
                    linked_tokens.append(escape(text[local_index:]))
                    local_index = len(text)
                    continue

                if active_link is None and current_position < match.start():
                    segment_end = min(match.start(), token_end) - token_start
                    linked_tokens.append(escape(text[local_index:segment_end]))
                    local_index = segment_end
                    continue

                if active_link is None:
                    active_link = open_link(match)

                segment_end = min(match.end(), token_end) - token_start
                linked_tokens.append(escape(text[local_index:segment_end]))
                local_index = segment_end

                if token_start + local_index >= active_link.end():
                    has_remaining_text = token_start + local_index < token_end
                    if has_remaining_text or not active_link_tags:
                        close_link(reopen_tags=has_remaining_text and bool(active_link_tags))
                        active_link = None
                        match_index += 1

            if text == "" and active_link is None:
                linked_tokens.append("")

        if active_link is not None:
            close_link()

        return "".join(linked_tokens)

    def _render_link_start(self, matched_target):
        if self.link_renderer == self._render_rich_text_link:
            return (
                f'<a linktype="{escape(matched_target["linktype"], quote=True)}" '
                f'id="{matched_target["id"]}">'
            )

        matched_url = matched_target["url"]
        return f'<a href="{escape(matched_url, quote=True)}">'

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


@lru_cache(maxsize=1)
def _get_cached_frontend_autolinker():
    return SpeciesAutoLinker(SpeciesAutoLinker.get_unique_match_targets_from_database())


@lru_cache(maxsize=1)
def _get_cached_rich_text_autolinker():
    return SpeciesAutoLinker(
        SpeciesAutoLinker.get_unique_match_targets_from_database(),
        link_renderer=SpeciesAutoLinker._render_rich_text_link,
    )


@receiver([post_save, post_delete], sender=Species)
def clear_species_autolinker_cache(**kwargs):
    SpeciesAutoLinker.clear_cached_autolinkers()
