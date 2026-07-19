"""Integration tests for signed-cookie flash messages."""

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import BaseAdmin, StringField

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class Item(TinydbBaseModel):
    name: str


class ItemView(TinydbModelView):
    fields = [StringField("name")]


@pytest.fixture()
def app():
    admin = BaseAdmin(secret_key="test-secret")
    starlette_app = Starlette()
    admin.add_view(ItemView(Item))
    admin.mount_to(starlette_app)
    return starlette_app


@pytest.fixture()
def client(app):
    ItemView._db.truncate()
    return CsrfTestClient(app)


class TestFlashMessages:
    def test_flash_message_appears_after_redirect(self, client):
        response = client.post(
            "/admin/item/create",
            data={"name": "hello"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert "starlette_admin_flash" in client.cookies

        response = client.get(response.headers["location"], follow_redirects=True)
        assert response.status_code == 200
        assert "was added successfully" in response.text

    def test_flash_cookie_cleared_after_consumption(self, client):
        response = client.post(
            "/admin/item/create",
            data={"name": "hello"},
            follow_redirects=False,
        )
        redirect_url = response.headers["location"]

        # First GET consumes the flash cookie
        client.get(redirect_url, follow_redirects=True)
        assert "starlette_admin_flash" not in client.cookies

        # Second GET should not show the message again
        response = client.get(redirect_url, follow_redirects=True)
        assert "was added successfully" not in response.text

    def test_flash_cookie_is_signed(self, client):
        client.post(
            "/admin/item/create",
            data={"name": "hello"},
            follow_redirects=False,
        )
        flash_cookie = client.cookies["starlette_admin_flash"]
        # itsdangerous URLSafeSerializer produces base64-ish tokens with a signature
        assert "." in flash_cookie

    def test_tampered_flash_cookie_is_ignored(self, app):
        ItemView._db.truncate()
        bare_client = TestClient(app)
        # Plant a tampered flash cookie
        bare_client.cookies.set("starlette_admin_flash", "tampered.value")
        response = bare_client.get("/admin/item/list")
        assert response.status_code == 200
        # Tampered cookie is consumed and cleared, not rendered
        set_cookies = [
            value
            for name, value in response.headers.multi_items()
            if name.lower() == "set-cookie"
            and value.startswith("starlette_admin_flash")
        ]
        assert set_cookies
        assert any(
            "max-age=0" in c.lower() or c.startswith("starlette_admin_flash=;")
            for c in set_cookies
        )
