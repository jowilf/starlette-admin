"""CSV and JSON export, both "this page" and "all matching rows" scopes."""

import json

from playwright.sync_api import Page, expect


def test_export_current_page_as_csv(page: Page):
    page.goto("/admin/book/list")
    page.get_by_role("button", name="Export").click()
    page.get_by_role("link", name="CSV").click()

    with page.expect_download() as download_info:
        page.get_by_role("link", name="This Page").click()
    download = download_info.value

    assert download.suggested_filename.endswith(".csv")
    path = download.path()
    content = path.read_text()
    header = content.splitlines()[0]
    assert "Title" in header
    assert "Isbn" in header
    # Default page size is 10, so only the first page's rows are exported.
    assert len(content.splitlines()) == 1 + 10


def test_export_all_matching_rows_respects_search(page: Page):
    page.goto("/admin/book/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Foundation")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)

    page.get_by_role("button", name="Export").click()
    page.get_by_role("link", name="CSV").click()

    with page.expect_download() as download_info:
        page.get_by_role("link", name="All Matching Rows").click()
    download = download_info.value

    content = download.path().read_text()
    lines = content.splitlines()
    assert len(lines) == 2
    assert "Foundation" in lines[1]


def test_export_current_page_as_json(page: Page):
    """JsonExporter is enabled by default alongside CsvExporter (views.py's
    default `exporters` list), so the export dropdown offers both."""
    page.goto("/admin/book/list")
    page.get_by_role("button", name="Export").click()
    page.get_by_role("link", name="JSON").click()

    with page.expect_download() as download_info:
        page.get_by_role("link", name="This Page").click()
    download = download_info.value

    assert download.suggested_filename.endswith(".json")
    rows = json.loads(download.path().read_text())
    assert len(rows) == 10  # default page size
    assert "Title" in rows[0]
    assert "Isbn" in rows[0]
