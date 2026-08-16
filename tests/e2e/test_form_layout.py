"""Form layout composition: BookView splits its create/edit form across two
tabs (TabsWidget), so fields in the inactive tab start hidden."""

from playwright.sync_api import Page, expect


def _fill_flatpickr(page: Page, field_id: str, alt_text: str) -> None:
    date_input = page.locator(f"#{field_id} + input")
    date_input.click()
    date_input.fill(alt_text)
    page.keyboard.press("Escape")


def test_book_create_form_splits_fields_across_tabs(page: Page):
    page.goto("/admin/book/create")

    tabs = page.locator(".nav-tabs .nav-link")
    expect(tabs).to_have_count(2)
    expect(tabs.first).to_have_text("Details")
    expect(tabs.nth(1)).to_have_text("Pricing & Availability")

    # "Details" is the active tab on load: its fields are visible, the other
    # tab's fields aren't rendered as visible until selected.
    expect(page.locator("#title")).to_be_visible()
    expect(page.locator("#price")).not_to_be_visible()

    tabs.nth(1).click()
    expect(page.locator("#price")).to_be_visible()
    expect(page.locator("#title")).not_to_be_visible()


def test_create_book_using_both_tabs(page: Page):
    """Fields from both tabs must be submitted together, even though only
    one tab's fields are visible at a time."""
    page.goto("/admin/book/create")
    page.fill("#title", "The Fellowship of the Ring")
    page.fill("#isbn", "978-0618346257")
    page.locator("span[aria-labelledby='select2-author-container']").click()
    page.locator("input.select2-search__field").fill("Ursula")
    page.locator(".select2-results__option", has_text="Ursula K. Le Guin").first.click()
    page.locator("#genre").select_option("FICTION")

    page.locator(".nav-tabs .nav-link", has_text="Pricing").click()
    page.fill("#price", "22.75")
    page.fill("#rating", "5")
    _fill_flatpickr(page, "published_at", "July 29, 1954  00:00:00")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/book/list**")
    expect(
        page.get_by_text(
            'The item "The Fellowship of the Ring" was added successfully.'
        )
    ).to_be_visible()

    page.get_by_placeholder("Search...").fill("The Fellowship of the Ring")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="price"]')).to_have_text("22.75")
