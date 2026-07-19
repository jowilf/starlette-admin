"""CSV import via the list page's Import modal (CsvImporter, enabled by
default alongside JsonImporter)."""

from pathlib import Path

from playwright.sync_api import Page, expect


def test_import_csv_creates_new_author(page: Page, tmp_path: Path):
    csv_path = tmp_path / "authors.csv"
    csv_path.write_text(
        "name,email,bio,birth_date,is_active\n"
        "Frank Herbert,frank@example.com,American science fiction writer.,1920-10-08,true\n"
    )

    page.goto("/admin/author/list")
    page.locator('button[data-bs-target="#modal-import"]').click()
    page.locator("#import-format").select_option("csv")
    page.locator("#import-file").set_input_files(str(csv_path))
    page.locator("#import-submit").click()

    expect(page.locator("#import-summary")).to_contain_text(
        "1 row(s) scanned, 1 created."
    )
    page.locator("#import-submit").click()  # "Done" -> reloads the page

    page.wait_for_load_state()
    search = page.get_by_placeholder("Search...")
    search.fill("Frank Herbert")
    search.press("Enter")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    expect(page.locator("tbody tr").first).to_contain_text("Frank Herbert")
