"""List-page inline-edit popover: BookView opts `price` and `rating` into
`inline_editable_fields`, letting a single cell be edited without navigating
to the full edit form."""

from playwright.sync_api import Page, expect


def test_inline_edit_updates_price(page: Page):
    page.goto("/admin/book/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Foundation")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Foundation", timeout=3000)

    row.locator('td[data-sa-field="price"]').click()
    popover = page.locator(".popover.inline-edit-popover")
    popover.locator("#price").fill("15.99")
    popover.locator(".inline-edit-save").click()

    expect(
        page.get_by_text('The field "Price" of "Foundation" was updated successfully.')
    ).to_be_visible()
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="price"]')).to_have_text("15.99")


def test_inline_edit_updates_rating(page: Page):
    page.goto("/admin/book/list")
    search = page.get_by_placeholder("Search...")
    search.fill("I, Robot")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("I, Robot", timeout=3000)

    row.locator('td[data-sa-field="rating"]').click()
    popover = page.locator(".popover.inline-edit-popover")
    popover.locator("#rating").fill("2")
    popover.locator(".inline-edit-save").click()

    expect(
        page.get_by_text('The field "Rating" of "I, Robot" was updated successfully.')
    ).to_be_visible()
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="rating"]')).to_have_text("2")
