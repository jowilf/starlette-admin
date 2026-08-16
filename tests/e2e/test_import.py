"""CSV import via the list page's Import modal: a 3-step wizard (upload,
preview, confirm), using CsvImporter (enabled by default alongside
JsonImporter)."""

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
    page.locator("#import-submit").click()  # upload -> preview

    expect(page.locator("#import-preview-summary")).to_contain_text("1 row(s): 1 new")
    page.locator("#import-submit").click()  # preview -> confirm

    expect(page.locator("#import-result-summary")).to_contain_text(
        "1 row(s) scanned, 1 created"
    )
    page.locator("#import-submit").click()  # "Done" -> reloads the page

    page.wait_for_load_state()
    search = page.get_by_placeholder("Search...")
    search.fill("Frank Herbert")
    search.press("Enter")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    expect(page.locator("tbody tr").first).to_contain_text("Frank Herbert")


def test_import_deselect_field_excludes_column(page: Page, tmp_path: Path):
    """Unchecking a mapped field in the preview step drops that column from
    the confirmed import, mirroring what the old "skip primary key" checkbox
    did for the pk field."""
    csv_path = tmp_path / "authors.csv"
    csv_path.write_text(
        "name,email,bio,birth_date,is_active\n"
        "Skip Bio,skipbio@example.com,Should be dropped.,1975-05-05,true\n"
    )

    page.goto("/admin/author/list")
    page.locator('button[data-bs-target="#modal-import"]').click()
    page.locator("#import-format").select_option("csv")
    page.locator("#import-file").set_input_files(str(csv_path))
    page.locator("#import-submit").click()  # upload -> preview

    bio_checkbox = page.locator('#import-preview-mapping input[data-sa-field="bio"]')
    expect(bio_checkbox).to_be_checked()
    bio_checkbox.uncheck()
    page.wait_for_timeout(300)  # field-toggle re-preview round trip

    page.locator("#import-submit").click()  # preview -> confirm
    expect(page.locator("#import-result-summary")).to_contain_text(
        "1 row(s) scanned, 1 created"
    )
    page.locator("#import-submit").click()  # "Done" -> reloads the page

    page.wait_for_load_state()
    search = page.get_by_placeholder("Search...")
    search.fill("Skip Bio")
    search.press("Enter")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Skip Bio", timeout=3000)
    pk = row.get_attribute("data-sa-pk")

    page.goto(f"/admin/author/detail?pk={pk}")
    expect(page.get_by_text("Should be dropped.")).to_have_count(0)


def test_import_upsert_updates_existing_author(page: Page, tmp_path: Path):
    """Importing a row with `update_existing` checked and a pk matching an
    existing record edits it in place instead of creating a duplicate."""
    create_csv = tmp_path / "authors_create.csv"
    create_csv.write_text(
        "name,email,bio,birth_date,is_active\n"
        "UpsertMe,upsert@example.com,Bio text.,1950-01-01,true\n"
    )
    page.goto("/admin/author/list")
    page.locator('button[data-bs-target="#modal-import"]').click()
    page.locator("#import-format").select_option("csv")
    page.locator("#import-file").set_input_files(str(create_csv))
    page.locator("#import-submit").click()  # upload -> preview
    page.locator("#import-submit").click()  # preview -> confirm
    expect(page.locator("#import-result-summary")).to_contain_text("1 created")
    page.locator("#import-submit").click()  # "Done" -> reloads the page

    page.wait_for_load_state()
    search = page.get_by_placeholder("Search...")
    search.fill("UpsertMe")
    search.press("Enter")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("UpsertMe", timeout=3000)
    pk = row.get_attribute("data-sa-pk")

    update_csv = tmp_path / "authors_update.csv"
    update_csv.write_text(
        "id,name,email,bio,birth_date,is_active\n"
        f"{pk},UpsertedName,upsert@example.com,Bio text.,1950-01-01,true\n"
    )
    page.locator('button[data-bs-target="#modal-import"]').click()
    page.locator("#import-format").select_option("csv")
    page.locator("#import-file").set_input_files(str(update_csv))
    page.locator("#import-update-existing").check()
    page.locator("#import-submit").click()  # upload -> preview

    expect(page.locator("#import-preview-summary")).to_contain_text("1 updated")
    page.locator("#import-submit").click()  # preview -> confirm

    expect(page.locator("#import-result-summary")).to_contain_text("1 updated")
    page.locator("#import-submit").click()  # "Done" -> reloads the page

    page.wait_for_load_state()
    search.fill("UpsertedName")
    search.press("Enter")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
