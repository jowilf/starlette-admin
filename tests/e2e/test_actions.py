"""Batch (bulk) actions and per-row actions, both built-in and custom."""

import re

from playwright.sync_api import Page, expect


def _confirm_modal(page: Page, submit_button_name: str) -> None:
    """Waits out the modal's fade-in (clicking mid-transition can silently
    miss the button) then confirms it."""
    page.locator("#modal-action").wait_for(state="visible")
    page.wait_for_timeout(400)
    page.get_by_role("button", name=submit_button_name, exact=True).click()


def test_batch_action_mark_out_of_stock(page: Page):
    page.goto("/admin/book/list")
    page.get_by_label("Page size").select_option("25")  # show all 14 on one page

    titles = ["A Wizard of Earthsea", "The Left Hand of Darkness", "The Dispossessed"]
    for title in titles:
        row = page.locator("tbody tr", has=page.get_by_text(title, exact=True))
        row.locator(".row-checkbox").check()

    page.get_by_role("button", name=re.compile(r"With selected")).click()
    page.get_by_role("link", name="Mark selected books as out of stock").click()
    _confirm_modal(page, "Yes, proceed")

    expect(page.get_by_text("3 book(s) marked as out of stock")).to_be_visible()
    for title in titles:
        row = page.locator("tbody tr", has=page.get_by_text(title, exact=True))
        expect(row.locator('td[data-column="in_stock"] i')).to_have_class(
            re.compile(r"fa-times-circle")
        )


def test_batch_action_delete_selected(page: Page):
    """The built-in bulk "Delete" is a distinct code path from the row
    delete covered in test_crud.py: it runs delete_action on a pk list
    instead of a single-item row_action."""
    page.goto("/admin/book/list")
    page.get_by_label("Page size").select_option("25")  # show all 14 on one page

    # These three fall within the default (published_at desc) first page, so
    # the "gone" assertion holds even if the reload after the action drops
    # back to the default page size instead of keeping the "25" selection.
    titles = ["Kindred", "The Gods Themselves", "Asimov's Guide to Science"]
    for title in titles:
        row = page.locator("tbody tr", has=page.get_by_text(title, exact=True))
        row.locator(".row-checkbox").check()

    page.get_by_role("button", name=re.compile(r"With selected")).click()
    # Scoped to the batch-actions dropdown: row-level delete icons also carry
    # the accessible name "Delete" via their title attribute.
    page.locator("#actions-dropdown").get_by_role(
        "link", name="Delete", exact=True
    ).click()
    _confirm_modal(page, "Yes, delete all")

    expect(page.get_by_text("3 items were successfully deleted.")).to_be_visible()
    for title in titles:
        expect(
            page.locator("tbody tr", has=page.get_by_text(title, exact=True))
        ).to_have_count(0)


def test_row_action_restock(page: Page):
    page.goto("/admin/book/list")
    search = page.get_by_placeholder("Search...")
    search.fill("The Dispossessed")
    page.wait_for_url(re.compile(r"q=The"))
    row = page.locator("tbody tr").first
    expect(row).to_contain_text("The Dispossessed", timeout=3000)
    expect(row.locator('td[data-column="in_stock"] i')).to_have_class(
        re.compile(r"fa-times-circle")
    )

    row.locator("a[title='Restock']").click()
    _confirm_modal(page, "Yes, restock")

    expect(page.get_by_text("Book restocked")).to_be_visible()
    row = page.locator("tbody tr").first
    expect(row.locator('td[data-column="in_stock"] i')).to_have_class(
        re.compile(r"fa-check-circle")
    )
    # Restocked books no longer need the action: is_row_action_allowed_for_obj
    # hides it once in_stock is True.
    expect(row.locator("a[title='Restock']")).to_have_count(0)
