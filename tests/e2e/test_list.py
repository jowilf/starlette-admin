"""List page: rendering, search, sort, pagination, columns, and filters."""

import re

from playwright.sync_api import Page, expect


def test_list_renders_seeded_rows(page: Page):
    page.goto("/admin/book/list")
    expect(page.locator(".page-header h1")).to_have_text("Books")
    expect(page.locator("tbody tr")).to_have_count(10)
    expect(page.get_by_text("Showing 1 to 10 of 14 entries")).to_be_visible()


def test_default_sort_orders(page: Page):
    """BookView sorts published_at descending; AuthorView sorts name ascending
    (both set via fields_default_sort), so the first row on a bare list load
    should reflect that ordering without any explicit sort click."""
    page.goto("/admin/book/list")
    expect(page.locator("tbody tr").first).to_contain_text(
        "Bloodchild and Other Stories"
    )

    page.goto("/admin/author/list")
    expect(page.locator("tbody tr").first).to_contain_text("Isaac Asimov")


def test_pagination_next_page_and_page_size(page: Page):
    page.goto("/admin/book/list")

    page.locator(".pagination a:has(i.fa-chevron-right)").click()
    expect(page).to_have_url(re.compile(r"page=2"))
    expect(page.get_by_text("Showing 11 to 14 of 14 entries")).to_be_visible()

    page.get_by_label("Page size").select_option("25")
    expect(page.locator("tbody tr")).to_have_count(14)
    expect(page.get_by_text("Showing 1 to 14 of 14 entries")).to_be_visible()


def test_sort_by_column_toggles_direction(page: Page):
    page.goto("/admin/book/list")

    page.get_by_role("link", name="Price").click()
    expect(page).to_have_url(re.compile(r"sort=price__asc"))
    first_price_asc = page.locator("tbody tr").first.locator('td[data-column="price"]')
    expect(first_price_asc).to_have_text("6.99")

    page.get_by_role("link", name="Price").click()
    expect(page).to_have_url(re.compile(r"sort=price__desc"))
    first_price_desc = page.locator("tbody tr").first.locator('td[data-column="price"]')
    expect(first_price_desc).to_have_text("19.99")


def test_global_search_auto_submit(page: Page):
    page.goto("/admin/book/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Foundation")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    expect(page.locator("tbody tr").first).to_contain_text("Foundation")


def test_search_on_author_list(page: Page):
    page.goto("/admin/author/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Octavia")
    search.press("Enter")
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(page.locator("tbody tr").first).to_contain_text("Octavia Butler")


def test_column_visibility_toggle(page: Page):
    page.goto("/admin/book/list")
    expect(page.locator('th[data-column="isbn"]')).to_be_visible()

    page.get_by_role("button", name="Columns").click()
    page.locator(".column-visibility-toggle[value='isbn']").uncheck()
    page.get_by_role("button", name="Apply").click()

    expect(page.locator('th[data-column="isbn"]')).to_have_count(0)


def test_filter_builder_boolean_is_true(page: Page):
    page.goto("/admin/book/list")

    page.get_by_role("button", name="Filters").click()
    row = page.locator(".filter-row").first
    row.locator(".filter-row-field").select_option(label="In stock")
    row.locator(".filter-row-op").select_option(label="Is true")
    page.get_by_role("button", name="Apply filters").click()

    expect(page).to_have_url(re.compile(r"filter="))
    expect(page.locator("tbody tr")).to_have_count(10)
    for icon in page.locator('td[data-column="in_stock"] i').all():
        expect(icon).to_have_class("fa-solid fa-check-circle fa-lg")


def test_filter_builder_numeric_greater_than(page: Page):
    page.goto("/admin/book/list")

    page.get_by_role("button", name="Filters").click()
    row = page.locator(".filter-row").first
    row.locator(".filter-row-field").select_option(label="Price")
    row.locator(".filter-row-op").select_option(label="Greater than")
    row.locator(".filter-row-value").fill("15")
    page.get_by_role("button", name="Apply filters").click()

    expect(page).to_have_url(re.compile(r"filter="))
    # Only "Asimov's Guide to Science" (19.99) is priced above 15 in the seed data.
    expect(page.locator("tbody tr")).to_have_count(1)
    expect(page.locator("tbody tr").first).to_contain_text("Asimov's Guide to Science")


def test_removing_one_active_filter_chip_keeps_the_other(page: Page):
    """Two filters applied at once (In stock + Price) render as two removable
    chips; removing one must drop only that filter, not the whole set."""
    page.goto("/admin/book/list")

    page.get_by_role("button", name="Filters").click()
    first_row = page.locator(".filter-row").first
    first_row.locator(".filter-row-field").select_option(label="In stock")
    first_row.locator(".filter-row-op").select_option(label="Is true")
    page.locator("#add-filter-row").click()
    second_row = page.locator(".filter-row").nth(1)
    second_row.locator(".filter-row-field").select_option(label="Price")
    second_row.locator(".filter-row-op").select_option(label="Greater than")
    second_row.locator(".filter-row-value").fill("10")
    page.get_by_role("button", name="Apply filters").click()

    expect(page).to_have_url(re.compile(r"filter="))
    chips = page.locator("#active-filters a.badge")
    expect(chips).to_have_count(2)
    # 10 in-stock books, 5 of which are priced above 10 (both filters applied).
    expect(page.locator("tbody tr[data-pk]")).to_have_count(5)

    chips.filter(has_text="In stock").click()

    expect(page).to_have_url(re.compile(r"filter="))
    expect(page.locator("#active-filters a.badge")).to_have_count(1)
    expect(page.locator("#active-filters")).to_contain_text("Price")
    expect(page.locator("#active-filters")).not_to_contain_text("In stock")
    # Price > 10 alone (in-stock or not) matches 8 books in the seed data.
    expect(page.locator("tbody tr[data-pk]")).to_have_count(8)
