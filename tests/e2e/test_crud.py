"""Create, edit, view detail, and delete happy paths for both models."""

import re

from playwright.sync_api import Page, expect


def _select_relation(
    page: Page, field_id: str, search_text: str, option_text: str
) -> None:
    """Drives the select2 widget rendered for a HasOne/HasMany relation field."""
    page.locator(f"span[aria-labelledby='select2-{field_id}-container']").click()
    page.locator("input.select2-search__field").fill(search_text)
    page.locator(".select2-results__option", has_text=option_text).first.click()


def _fill_flatpickr(page: Page, field_id: str, alt_text: str) -> None:
    """Types into the visible altInput flatpickr renders next to the real
    (hidden) input, using its ``altFormat`` so flatpickr's own blur-time
    parser fills the hidden, form-submitted input."""
    date_input = page.locator(f"#{field_id} + input")
    date_input.click()
    date_input.fill(alt_text)
    page.keyboard.press("Escape")


def test_create_author(page: Page):
    page.goto("/admin/author/create")
    page.fill("#name", "Neil Gaiman")
    page.fill("#email", "neil@example.com")
    page.fill("#bio", "British author of fiction, fantasy, and comics.")
    _fill_flatpickr(page, "birth_date", "November 10, 1960")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/author/list**")
    expect(
        page.get_by_text('The item "Neil Gaiman" was added successfully.')
    ).to_be_visible()

    page.get_by_placeholder("Search...").fill("Neil Gaiman")
    page.get_by_placeholder("Search...").press("Enter")
    expect(page.locator("tbody tr")).to_have_count(1)


def test_create_book_with_relation(page: Page):
    page.goto("/admin/book/create")
    page.fill("#title", "Good Omens")
    page.fill("#isbn", "978-0060853983")
    _select_relation(page, "author", "Ursula", "Ursula K. Le Guin")
    page.locator("#genre").select_option("FICTION")
    # price/rating/published_at live on the form's second tab (form_layout
    # splits BookView's fields into "Details" and "Pricing & Availability").
    page.locator(".nav-tabs .nav-link", has_text="Pricing").click()
    page.fill("#price", "12.49")
    page.fill("#rating", "5")
    _fill_flatpickr(page, "published_at", "May 1, 1990  10:00:00")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/book/list**")
    expect(
        page.get_by_text('The item "Good Omens" was added successfully.')
    ).to_be_visible()

    page.get_by_placeholder("Search...").fill("Good Omens")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="author"]')).to_contain_text("Ursula K. Le Guin")
    expect(row.locator('td[data-column="price"]')).to_have_text("12.49")


def test_save_and_add_another_resets_the_create_form(page: Page):
    """The form footer's "Save and add another" button redirects back to the
    (now blank) create form, distinct from the plain "Save" button's
    redirect to the list."""
    page.goto("/admin/author/create")
    page.fill("#name", "Terry Pratchett")
    page.fill("#email", "terry@example.com")

    page.get_by_role("button", name="Save and add another", exact=True).click()
    page.wait_for_url("**/admin/author/create")
    expect(
        page.get_by_text('The item "Terry Pratchett" was added successfully.')
    ).to_be_visible()
    expect(page.locator("#name")).to_have_value("")

    page.goto("/admin/author/list")
    page.get_by_placeholder("Search...").fill("Terry Pratchett")
    page.get_by_placeholder("Search...").press("Enter")
    expect(page.locator("tbody tr")).to_have_count(1)


def test_save_and_continue_editing_redirects_to_edit_form(page: Page):
    """The form footer's "Save and continue editing" button redirects to the
    edit page of the just-created item, pre-populated with its saved values."""
    page.goto("/admin/author/create")
    page.fill("#name", "Ann Leckie")
    page.fill("#email", "ann@example.com")

    page.get_by_role("button", name="Save and continue editing", exact=True).click()
    page.wait_for_url(re.compile(r"/admin/author/edit\?pk=\d+"))
    expect(
        page.get_by_text('The item "Ann Leckie" was added successfully.')
    ).to_be_visible()
    expect(page.locator("#name")).to_have_value("Ann Leckie")


def test_edit_book_updates_price(page: Page):
    page.goto("/admin/book/list")
    page.get_by_placeholder("Search...").fill("Foundation")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Foundation", timeout=3000)
    pk = row.get_attribute("data-sa-pk")

    page.goto(f"/admin/book/edit?pk={pk}")
    page.locator(".nav-tabs .nav-link", has_text="Pricing").click()
    price_input = page.locator("#price")
    price_input.fill("")
    price_input.fill("7.49")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/book/list**")
    expect(
        page.get_by_text('The item "Foundation" was changed successfully.')
    ).to_be_visible()

    page.get_by_placeholder("Search...").fill("Foundation")
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="price"]')).to_have_text("7.49", timeout=3000)


def test_author_detail_shows_related_books(page: Page):
    page.goto("/admin/author/list")
    search = page.get_by_placeholder("Search...")
    search.fill("Isaac Asimov")
    search.press("Enter")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Isaac Asimov", timeout=3000)
    row.click()  # whole row is clickable (row_click_navigate) and opens the detail page

    expect(page.locator(".page-header h1")).to_be_visible()
    attr_row = page.locator("tr", has=page.get_by_text("Books", exact=True))
    expect(attr_row.get_by_role("link", name="Foundation")).to_be_visible()
    expect(attr_row.get_by_role("link", name="I, Robot")).to_be_visible()


def test_book_detail_shows_author_link_and_field_values(page: Page):
    """Covers the HasOne side of the relation (author as a link) plus enum
    and float/datetime rendering, none of which the Author detail test above
    (HasMany side) touches."""
    page.goto("/admin/book/list")
    search = page.get_by_placeholder("Search...")
    # Not "Foundation": test_edit_book_updates_price (above) changes its
    # price, so asserting the seeded price here would depend on run order.
    search.fill("Asimov's Guide to Science")
    expect(page.locator("tbody tr")).to_have_count(1, timeout=3000)
    row = page.locator("tbody tr").first
    # Click the title cell, not the row itself: a plain row.click() lands on
    # the element at its geometric center, which for Book's 9 columns is the
    # "author" cell, a link that navigates to the author's own detail page.
    row.locator('td[data-column="title"]').click()

    expect(page.locator(".page-header h1")).to_be_visible()

    def attr_row(label: str):
        return page.locator("tr", has=page.get_by_text(label, exact=True))

    expect(attr_row("Author").get_by_role("link", name="Isaac Asimov")).to_be_visible()
    # EnumField renders the member name (underscores replaced with spaces)
    # as its detail label, e.g. Genre.NON_FICTION -> "NON FICTION".
    expect(attr_row("Genre")).to_contain_text("NON FICTION")
    expect(attr_row("Price")).to_contain_text("19.99")
    # Rendered in the browser's local timezone, so the UTC 1960-01-01
    # midnight seed value can display as late Dec 1959.
    expect(attr_row("Published at")).to_contain_text(re.compile(r"19(59|60)"))


def test_edit_book_updates_relation(page: Page):
    """Changing a pre-populated select2 relation is a distinct code path from
    the empty one exercised on create.

    Must run after the detail-page tests above: they assert "I, Robot" is
    still one of Isaac Asimov's books, and this test reassigns it away."""
    page.goto("/admin/book/list")
    page.get_by_placeholder("Search...").fill("I, Robot")
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("I, Robot", timeout=3000)
    pk = row.get_attribute("data-sa-pk")

    page.goto(f"/admin/book/edit?pk={pk}")
    expect(
        page.locator("span[aria-labelledby='select2-author-container']")
    ).to_contain_text("Isaac Asimov")
    _select_relation(page, "author", "Octavia", "Octavia Butler")

    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/book/list**")
    expect(
        page.get_by_text('The item "I, Robot" was changed successfully.')
    ).to_be_visible()

    page.get_by_placeholder("Search...").fill("I, Robot")
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="author"]')).to_have_text(
        "Octavia Butler", timeout=3000
    )


def test_delete_book(page: Page):
    page.goto("/admin/book/create")
    page.fill("#title", "Disposable Book")
    page.fill("#isbn", "000-0000000000")
    _select_relation(page, "author", "Octavia", "Octavia Butler")
    page.locator("#genre").select_option("FICTION")
    page.locator(".nav-tabs .nav-link", has_text="Pricing").click()
    page.fill("#price", "1.00")
    _fill_flatpickr(page, "published_at", "January 1, 2000  00:00:00")
    page.get_by_role("button", name="Save", exact=True).click()
    page.wait_for_url("**/admin/book/list**")

    page.get_by_placeholder("Search...").fill("Disposable Book")
    # `search_auto_submit` debounces ~400ms after typing before it navigates;
    # wait for that navigation to land *before* opening the delete modal, or
    # it can fire mid-interaction and blow the modal away underneath us.
    page.wait_for_url(re.compile(r"q=Disposable"))
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("Disposable Book", timeout=3000)

    row.locator("a[title='Delete']").click()
    page.locator("#modal-action").wait_for(state="visible")
    # Bootstrap's fade-in transition is still running after `visible`; a
    # click mid-transition can miss the button silently.
    page.wait_for_timeout(400)
    page.get_by_role("button", name="Yes, delete", exact=True).click()
    expect(
        page.get_by_text('The item "Disposable Book" was successfully deleted.')
    ).to_be_visible()
    # Delete reloads the same search-filtered URL, hence the empty result set.
    expect(page.locator("tbody tr[data-sa-pk]")).to_have_count(0)
