"""Regression coverage for search excerpts and bounded page navigation."""

from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from bs4 import BeautifulSoup
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.test import SimpleTestCase
from wagtail.models import Page
from wagtail.rich_text import RichText

from home.models import AlignedParagraphBlock, MultiColumnAlignedParagraphBlock
from search.excerpts import search_excerpt


class SearchPresentationTests(SimpleTestCase):
    """Exercise presentation edge cases without creating indexed pages."""

    def test_metadata_is_preferred_normalized_and_truncated(self) -> None:
        """Prefer normalized metadata and enforce the summary character cap."""

        page = SimpleNamespace(search_description="  Garden &amp;  plants\n " + "x" * 250,
                               body=RichText("<p>Fallback prose</p>"))
        text = search_excerpt(page)
        self.assertTrue(text.startswith("Garden & plants "))
        self.assertEqual(len(text), 200)
        self.assertTrue(text.endswith("…"))

    def test_supported_paragraph_shapes_select_first_nonempty_prose(self) -> None:
        """Read supported Wagtail paragraph values while skipping empty blocks."""

        values = [
            ("paragraph", AlignedParagraphBlock().to_python({"paragraph": "<p></p><p>Garden &amp; plants</p><p>Later prose</p>"})),
            ("paragraph", RichText("<p>Garden &amp; plants</p>")),
            ("aligned_paragraph", AlignedParagraphBlock().to_python({"paragraph": "<p>Garden &amp; plants</p>"})),
            ("multi_column_paragraph", MultiColumnAlignedParagraphBlock().to_python({"paragraph": ["<p> </p>", "<p>Garden &amp; plants</p>"]})),
        ]
        for block_type, value in values:
            with self.subTest(block_type=block_type, value=value):
                page = SimpleNamespace(search_description=" ", body=[
                    SimpleNamespace(block_type="html", value="<p>Ignore raw HTML</p>"),
                    SimpleNamespace(block_type="paragraph", value=RichText("<p> </p>")),
                    SimpleNamespace(block_type=block_type, value=value),
                ])
                self.assertEqual(search_excerpt(page), "Garden & plants")

    def test_rich_text_body_and_missing_prose(self) -> None:
        """Use the first rich-text paragraph and omit unsupported content."""

        page = SimpleNamespace(search_description="", body=RichText("<p></p><p>First prose</p><p>Second prose</p>"))
        self.assertEqual(search_excerpt(page), "First prose")
        for body in (None, [], [SimpleNamespace(block_type="image", value="No prose")]):
            self.assertEqual(search_excerpt(SimpleNamespace(search_description="", body=body)), "")

    def test_embedded_scripts_and_styles_do_not_become_summary_text(self) -> None:
        """Discard script and style contents when extracting readable prose."""

        page = SimpleNamespace(search_description="", body=RichText(
            "<script>alert('hidden')</script><style>p {color:red}</style><p>Visible prose</p>"
        ))
        self.assertEqual(search_excerpt(page), "Visible prose")

    def test_leading_headings_and_lists_are_excluded_from_first_paragraph(self) -> None:
        """Keep prose separate from headings and lists before its paragraph."""

        page = SimpleNamespace(search_description="", body=RichText(
            "<h2>Heading</h2><ul><li>List item</li></ul><p></p>"
            "<p>First prose</p><p>Later prose</p>"
        ))
        self.assertEqual(search_excerpt(page), "First prose")
        page.body = "Plain prose without paragraph markup"
        self.assertEqual(search_excerpt(page), "Plain prose without paragraph markup")

    def test_excerpt_is_autoescaped_in_result_template(self) -> None:
        """Leave excerpt and title text subject to template autoescaping."""

        page = Page(content_type_id=1, search_description="&lt;img src=x onerror=alert(1)&gt; &amp; Garden", title="<script>Title</script>")
        page.get_url = lambda *args, **kwargs: "/garden/"
        html = render_to_string("includes/search_results.html", {
            "search_results": [SimpleNamespace(specific=page)],
        })
        soup = BeautifulSoup(html, "html.parser")
        self.assertIsNone(soup.find("script"))
        self.assertIsNone(soup.find("img"))
        self.assertEqual(soup.p.get_text(), "<img src=x onerror=alert(1)> & Garden")

    def test_pagination_is_elided_and_retains_encoded_query_parameters(self) -> None:
        """Bound pagination links and retain escaped query parameters."""

        paginator = Paginator(range(2000), 10)
        results = paginator.page(100)
        html = render_to_string("search/pagination.html", {
            "search_results": results,
            "page_range": paginator.get_elided_page_range(100, on_each_side=1, on_ends=1),
            "query_prefix": "q=Garden+%26+plants&category=visit&",
        })
        soup = BeautifulSoup(html, "html.parser")
        self.assertEqual(soup.select_one('[aria-current="page"]').get_text(), "Page 100")
        self.assertEqual(len(soup.find_all("a")), 6)
        self.assertEqual(len(soup.select(".search-pagination__gap")), 2)
        for link in soup.find_all("a"):
            params = parse_qs(urlsplit(link["href"]).query)
            self.assertEqual(params["q"], ["Garden & plants"])
            self.assertEqual(params["category"], ["visit"])
            self.assertEqual(len(params["page"]), 1)
            self.assertTrue(link["aria-label"])
