"""Plain-text summaries for public search result listings."""

from collections.abc import Mapping
from html.parser import HTMLParser

from django.utils.text import Truncator
from wagtail.models import Page
from wagtail.rich_text import RichText


class _ParagraphText(HTMLParser):
    """Collect prose without rendering rich text or exposing embedded markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style"}:
            self.ignored_depth += 1
        elif tag == "p" and not self.ignored_depth:
            self.parts = []
        elif tag in {"br", "div", "li"}:
            self.parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"}:
            self.ignored_depth = max(0, self.ignored_depth - 1)
        elif tag == "p" and not self.ignored_depth:
            text = " ".join("".join(self.parts).split())
            if text:
                self.paragraphs.append(text)
            self.parts = []
        elif tag in {"div", "li"}:
            self.parts.append(" ")

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)


def _plain_text(value: object) -> str:
    """Select the first nonempty HTML paragraph, or normalize plain prose."""

    parser = _ParagraphText()
    parser.feed(str(value))
    parser.close()
    return (parser.paragraphs or [" ".join("".join(parser.parts).split())])[0]


def search_excerpt(page: Page) -> str:
    """Return at most 200 plain-text characters from metadata or supported prose.

    Only paragraph blocks and rich-text bodies are used; arbitrary HTML and
    unrelated structured block values are never rendered for a search summary.
    The returned ordinary string remains subject to template autoescaping.
    """

    description = _plain_text(page.search_description or "")
    if description:
        return Truncator(description).chars(200)

    body = getattr(page, "body", None)
    if isinstance(body, (RichText, str)):
        return Truncator(_plain_text(body)).chars(200)
    for block in body or []:
        if block.block_type not in {"paragraph", "aligned_paragraph", "multi_column_paragraph"}:
            continue
        value = block.value
        if isinstance(value, Mapping):
            value = value.get("paragraph", "")
        candidates = value if block.block_type == "multi_column_paragraph" else [value]
        for candidate in candidates:
            text = _plain_text(candidate)
            if text:
                return Truncator(text).chars(200)
    return ""
