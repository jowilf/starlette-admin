"""Export via the built-in "export" batch action: a modal (scope, fields,
format, filename) opened from its own dedicated toolbar button, submitted as
a native form POST so the response triggers a browser download."""

import json

from playwright.sync_api import Page, expect


def _open_export_modal(page: Page) -> None:
    page.get_by_role("link", name="Export", exact=True).click()
    page.locator("#modal-action").wait_for(state="visible")
    page.wait_for_timeout(400)


def _submit_export(page: Page):
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Export", exact=True).click()
    return download_info.value


def test_export_current_page_as_csv(page: Page):
    page.goto("/admin/book/list")
    _open_export_modal(page)
    page.locator("#export-action-format").select_option("csv")
    download = _submit_export(page)

    assert download.suggested_filename.endswith(".csv")
    content = download.path().read_text()
    header = content.splitlines()[0]
    assert "Title" in header
    assert "Isbn" in header
    # Default page size is 10, and scope defaults to "Current page" when
    # nothing is selected.
    assert len(content.splitlines()) == 1 + 10


def test_export_current_page_as_json(page: Page):
    """JsonExporter is enabled by default alongside CsvExporter (the
    view's default `exporters` list), so the export form offers both."""
    page.goto("/admin/book/list")
    _open_export_modal(page)
    page.locator("#export-action-format").select_option("json")
    download = _submit_export(page)

    assert download.suggested_filename.endswith(".json")
    rows = json.loads(download.path().read_text())
    assert len(rows) == 10
    assert "Title" in rows[0]
    assert "Isbn" in rows[0]


def test_export_selected_rows_defaults_scope_to_selected(page: Page):
    page.goto("/admin/book/list")
    title = "The Dispossessed"
    row = page.locator("tbody tr", has=page.get_by_text(title, exact=True))
    row.locator(".row-checkbox").check()

    _open_export_modal(page)
    expect(page.locator("[data-sa-export-scope-selected]")).to_be_checked()
    page.locator("#export-action-format").select_option("csv")
    download = _submit_export(page)

    lines = download.path().read_text().splitlines()
    assert len(lines) == 2  # header + the one selected row
    assert title in lines[1]


def test_export_select_all_matching_exports_every_row(page: Page):
    """The default page size (10) is below the seeded book count (14), so
    the select-all-matching banner is available without narrowing the list
    with a search first."""
    page.goto("/admin/book/list")
    page.locator("#select-all-rows").check()
    page.locator("#select-all-matching-link").click()

    _open_export_modal(page)
    expect(page.locator("[data-sa-export-scope-selected]")).to_be_checked()
    page.locator("#export-action-format").select_option("csv")
    download = _submit_export(page)

    lines = download.path().read_text().splitlines()
    assert len(lines) - 1 == 14  # header + every seeded book


def test_export_field_subset(page: Page):
    page.goto("/admin/book/list")
    _open_export_modal(page)
    page.locator("#export-action-format").select_option("csv")
    checkboxes = page.locator('#modal-form input[name="fields"]')
    for i in range(checkboxes.count()):
        checkbox = checkboxes.nth(i)
        if checkbox.get_attribute("value") != "title":
            checkbox.uncheck()
    download = _submit_export(page)

    header = download.path().read_text().splitlines()[0]
    assert header.strip() == "Title"


def test_export_custom_filename(page: Page):
    page.goto("/admin/book/list")
    _open_export_modal(page)
    page.locator("#export-action-format").select_option("csv")
    page.locator("#export-action-filename").fill("my-books")
    download = _submit_export(page)

    assert download.suggested_filename == "my-books.csv"
