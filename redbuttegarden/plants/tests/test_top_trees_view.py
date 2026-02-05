import logging
import pytest
from django.http import HttpResponse
from django.urls import reverse

import plants.views as views
from plants.models import Species
from plants.tests.utils import get_species


@pytest.mark.django_db
def test_top_trees_renders_list(client, genus):
    """
    Basic smoke test: view returns 200 and contains the downloadable XLSX link text.
    """
    for i in range(3):
        get_species(genus, name=f"sp{i}", full_name=f"Genus sp{i}", arborist_rec=True)

    url = reverse("plants:top-trees")
    resp = client.get(url)
    assert resp.status_code == 200
    text = resp.content.decode("utf-8")
    # the view supplies additional_html that references the Top Tree Selections file
    assert "Top Tree Selections for Utah 2025" in text


@pytest.mark.django_db
def test_top_trees_invalid_page_param_does_not_500_and_logs(client, genus, caplog):
    """
    Ensure a malicious/invalid `page` param does not raise 500 and we log a warning.
    This test expects the hardened view to log either 'Invalid page param' or 'Paginator fallback for page'.
    """
    # create enough rows to exercise pagination
    for i in range(60):
        get_species(genus, name=f"sp{i}", full_name=f"Genus sp{i}", arborist_rec=True)

    caplog.set_level(logging.WARNING)
    url = reverse("plants:top-trees")
    malicious_page = "'nvOpzp"
    resp = client.get(url, {"page": malicious_page})
    assert resp.status_code == 200

    # sanity check content rendered
    assert "Top Tree Selections for Utah 2025" in resp.content.decode("utf-8")

    # Expect that a warning was logged about invalid page param or paginator fallback
    logged = "Invalid page param" in " ".join(r.getMessage() for r in caplog.records) or any(
        "Paginator fallback for page" in r.getMessage() for r in caplog.records
    )
    assert logged, f"Expected a warning about invalid page param; logs: {[r.getMessage() for r in caplog.records]}"


@pytest.mark.django_db
def test_top_trees_htmx_uses_partial_template(client, genus):
    """
    When HX-Request header is present the HTMX partial template should be used.
    Verify by checking the templates used in the response (Django test client populates response.templates).
    """
    for i in range(2):
        get_species(genus, name=f"sp{i}", full_name=f"Genus sp{i}", arborist_rec=True)

    url = reverse("plants:top-trees")
    # Django test client requires HTTP_ prefix for custom headers
    resp = client.get(url, **{"HTTP_HX_REQUEST": "true"})
    assert resp.status_code == 200

    # response.templates is a list of Template objects used to render this response.
    template_names = [t.name for t in getattr(resp, "templates", []) if t.name]
    assert (
        "plants/collection_list_table.html" in template_names
        or any("collection_list_table" in (name or "") for name in template_names)
    ), f"Expected table partial to be used; templates: {template_names}"


@pytest.mark.django_db
def test_top_trees_export_branch_returns_file_response(monkeypatch, client, genus):
    """
    Monkeypatch the TableExport used in plants.views so export branch returns a controlled HttpResponse.
    The view does: if TableExport.is_valid_format(export_format): export_table = TopTreesSpeciesTable(...);
    exporter = TableExport(export_format, export_table); return exporter.response(...)
    We'll ensure that branch executes and returns an attachment-like response.
    """
    # create at least one row
    get_species(genus, name="sp-export", full_name="Genus export", arborist_rec=True)

    # Create fake exporter class used by the view
    class FakeExporter:
        def __init__(self, fmt, table):
            self.fmt = fmt
            self.table = table

        def response(self, filename):
            resp = HttpResponse(b"fake-bytes", content_type="application/octet-stream")
            resp["Content-Disposition"] = f'attachment; filename="{filename}"'
            return resp

    # Monkeypatch TableExport.is_valid_format to return True and TableExport to our fake class.
    # plants.views imports TableExport at top-level; patch that symbol.
    monkeypatch.setattr(views, "TableExport", FakeExporter)
    # Provide an is_valid_format attribute on the FakeExporter class for the check used in the view
    setattr(views.TableExport, "is_valid_format", staticmethod(lambda fmt: True))

    url = reverse("plants:top-trees")
    resp = client.get(url, {"_export": "xlsx"})
    assert resp.status_code == 200
    assert resp.get("Content-Disposition") is not None
    assert resp.content == b"fake-bytes"
