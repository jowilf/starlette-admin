"""Login, logout, and the unauthenticated redirect, using a guest (not
pre-authenticated) browser context so the login form is actually exercised."""

import re

from playwright.sync_api import Page, expect

from tests.e2e.app import ADMIN_PASSWORD, ADMIN_USERNAME


def test_unauthenticated_request_redirects_to_login(guest_page: Page):
    guest_page.goto("/admin/")
    expect(guest_page).to_have_url(re.compile(r"/admin/login"))


def test_login_with_wrong_password_shows_error(guest_page: Page):
    guest_page.goto("/admin/login")
    guest_page.fill('input[name="username"]', ADMIN_USERNAME)
    guest_page.fill('input[name="password"]', "not-the-password")
    guest_page.get_by_role("button", name="Sign in").click()

    expect(guest_page.get_by_text("Invalid username or password")).to_be_visible()
    expect(guest_page).to_have_url(re.compile(r"/admin/login"))


def test_login_and_logout_happy_path(guest_page: Page):
    guest_page.goto("/admin/login")
    guest_page.fill('input[name="username"]', ADMIN_USERNAME)
    guest_page.fill('input[name="password"]', ADMIN_PASSWORD)
    guest_page.get_by_role("button", name="Sign in").click()

    guest_page.wait_for_url(re.compile(r"/admin/$"))
    expect(
        guest_page.get_by_role("heading", name="Welcome to Library Admin")
    ).to_be_visible()

    guest_page.get_by_role("link", name="Open user menu").click()
    guest_page.get_by_role("button", name="Logout").click()

    guest_page.wait_for_url(re.compile(r"/admin/login"))
    # Logged out: the admin index should bounce back to the login form again.
    guest_page.goto("/admin/")
    expect(guest_page).to_have_url(re.compile(r"/admin/login"))
