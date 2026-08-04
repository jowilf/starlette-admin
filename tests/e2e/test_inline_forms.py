"""Inline model views: AuthorView embeds a Book formset (BookInline) in its
own create/edit form, so books can be added/removed without leaving the page."""

from playwright.sync_api import Page, expect


def _select_relation(
    page: Page, field_id: str, search_text: str, option_text: str
) -> None:
    page.locator(f"span[aria-labelledby='select2-{field_id}-container']").click()
    page.locator("input.select2-search__field").fill(search_text)
    page.locator(".select2-results__option", has_text=option_text).first.click()


def _fill_flatpickr(page: Page, field_id: str, alt_text: str) -> None:
    date_input = page.locator(f"#{field_id} + input")
    date_input.click()
    date_input.fill(alt_text)
    page.keyboard.press("Escape")


def _fill_inline_book_row(row, title: str, isbn: str, genre: str, price: str) -> None:
    row.locator('input[id$=".title"]').fill(title)
    row.locator('input[id$=".isbn"]').fill(isbn)
    row.locator('select[id$=".genre"]').select_option(genre)
    row.locator('input[id$=".price"]').fill(price)
    row.locator('input[id$=".rating"]').fill("5")
    date_input = row.locator('input[id$=".published_at"] + input')
    date_input.click()
    date_input.fill("June 1, 1965  00:00:00")
    row.page.keyboard.press("Escape")


def test_create_author_with_inline_book_row(page: Page):
    page.goto("/admin/author/create")
    page.fill("#name", "Frank Herbert")
    page.fill("#email", "frank@example.com")

    formset = page.locator(".inline-formset").filter(has_text="Books")
    formset.locator(".inline-add-row").click()
    row = formset.locator(".inline-row").last
    _fill_inline_book_row(row, "Dune", "978-0441172719", "SCIENCE_FICTION", "11.99")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/author/list**")
    expect(
        page.get_by_text('The item "Frank Herbert" was added successfully.')
    ).to_be_visible()

    page.goto("/admin/book/list")
    page.get_by_placeholder("Search...").fill("Dune")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="author"]')).to_contain_text("Frank Herbert")


def test_edit_author_adds_second_inline_book_via_add_row(page: Page):
    page.goto("/admin/author/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Octavia")
    search.press("Enter")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Octavia Butler", timeout=3000)
    pk = row.get_attribute("data-sa-pk")

    page.goto(f"/admin/author/edit?pk={pk}")
    formset = page.locator(".inline-formset").filter(has_text="Books")
    formset.locator(".inline-add-row").click()
    new_row = formset.locator(".inline-row").last
    _fill_inline_book_row(
        new_row, "Wild Seed", "978-0446676094", "SCIENCE_FICTION", "13.50"
    )

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/author/list**")
    expect(
        page.get_by_text('The item "Octavia Butler" was changed successfully.')
    ).to_be_visible()

    page.goto("/admin/book/list")
    page.get_by_placeholder("Search...").fill("Wild Seed")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    expect(page.locator("tbody tr").first).to_contain_text("Octavia Butler")


def test_edit_author_removes_inline_book_row(page: Page):
    """Deleting an already-saved inline row (has a pk) soft-marks it for
    deletion client-side; the row (and the Book it points to) is gone once
    the parent form is saved."""
    page.goto("/admin/author/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Isaac Asimov")
    search.press("Enter")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Isaac Asimov", timeout=3000)
    pk = row.get_attribute("data-sa-pk")

    page.goto(f"/admin/author/edit?pk={pk}")
    formset = page.locator(".inline-formset").filter(has_text="Books")
    target_row = formset.locator(".inline-row").filter(
        has=page.locator('input[id$=".title"][value="Foundation"]')
    )
    expect(target_row).to_have_count(1)
    target_row.locator(".inline-delete-btn").click()

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/author/list**")
    expect(
        page.get_by_text('The item "Isaac Asimov" was changed successfully.')
    ).to_be_visible()

    page.goto("/admin/book/list")
    page.get_by_placeholder("Search...").fill("Foundation")
    expect(page.locator("tbody tr[data-sa-pk]")).to_have_count(0, timeout=3000)
