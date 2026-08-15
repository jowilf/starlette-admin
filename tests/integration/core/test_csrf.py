"""Integration tests for CSRF protection (§8.1)."""

import pytest
from itsdangerous import URLSafeSerializer
from starlette.applications import Starlette
from starlette.middleware import Middleware
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


@pytest.fixture()
def bare_client(app):
    """TestClient with no CSRF cookie pre-seeded."""
    ItemView._db.truncate()
    return TestClient(app, raise_server_exceptions=False)


class TestCsrfMiddleware:
    def test_get_sets_csrftoken_cookie(self, bare_client):
        response = bare_client.get("/admin/item/list")
        assert response.status_code == 200
        assert "starlette_admin_csrftoken" in bare_client.cookies

    def test_post_without_cookie_returns_403(self, bare_client):
        response = bare_client.post(
            "/admin/item/create",
            data={"name": "x"},
        )
        assert response.status_code == 403

    def test_post_with_mismatched_header_returns_403(self, bare_client):
        # seed the cookie via a GET first, then send a wrong token
        bare_client.get("/admin/item/list")
        response = bare_client.post(
            "/admin/item/create",
            headers={"X-CSRFToken": "wrong-token"},
            data={"name": "x"},
        )
        assert response.status_code == 403

    def test_post_with_mismatched_form_field_returns_403(self, bare_client):
        bare_client.get("/admin/item/list")
        response = bare_client.post(
            "/admin/item/create",
            data={"name": "x", "csrftoken": "wrong-token"},
        )
        assert response.status_code == 403

    def test_post_with_valid_header_passes(self, bare_client):
        bare_client.get("/admin/item/list")
        # The starlette_admin_csrftoken cookie already holds the *signed* value
        # that JS reads and forwards verbatim as the X-CSRFToken header
        # (double-submit cookie pattern). Sending the raw cookie value IS the
        # intended AJAX flow.
        token = bare_client.cookies["starlette_admin_csrftoken"]
        response = bare_client.post(
            "/admin/item/create",
            headers={"X-CSRFToken": token},
            data={"name": "hello"},
            follow_redirects=False,
        )
        # 303 redirect on success
        assert response.status_code == 303

    def test_post_with_valid_form_field_passes(self, bare_client):
        bare_client.get("/admin/item/list")
        token = bare_client.cookies["starlette_admin_csrftoken"]
        response = bare_client.post(
            "/admin/item/create",
            data={"name": "hello", "csrftoken": token},
            follow_redirects=False,
        )
        assert response.status_code == 303

    def test_csrf_client_helper_passes_automatically(self, client):
        response = client.post(
            "/admin/item/create", data={"name": "hello"}, follow_redirects=False
        )
        assert response.status_code == 303

    def test_csrf_token_visible_in_create_form(self, client):
        response = client.get("/admin/item/create")
        assert response.status_code == 200
        assert 'name="csrftoken"' in response.text

    def test_csrf_token_visible_in_edit_form(self, client):
        client.post("/admin/item/create", data={"name": "item1"})
        pk = ItemView._db.all()[0].doc_id
        response = client.get(f"/admin/item/edit?pk={pk}")
        assert response.status_code == 200
        assert 'name="csrftoken"' in response.text

    def test_cookie_httponly_false_for_js_access(self, bare_client):
        response = bare_client.get("/admin/item/list")
        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        # Cookie must NOT be HttpOnly so JS can read it for X-CSRFToken
        assert "httponly" not in set_cookie.lower()

    def test_cookie_samesite_lax(self, bare_client):
        response = bare_client.get("/admin/item/list")
        set_cookie = response.headers.get("set-cookie", "")
        assert "samesite=lax" in set_cookie.lower()

    def test_existing_cookie_not_overwritten(self, bare_client):
        # First request plants the cookie
        bare_client.get("/admin/item/list")
        first_token = bare_client.cookies["starlette_admin_csrftoken"]
        # Second request must not change it
        bare_client.get("/admin/item/create")
        assert bare_client.cookies["starlette_admin_csrftoken"] == first_token

    def test_tampered_cookie_is_regenerated(self, app):
        # Plant a tampered cookie on a fresh client and make a safe request
        bare_client = TestClient(app)
        bare_client.cookies.set("starlette_admin_csrftoken", "tampered.value")
        response = bare_client.get("/admin/item/list")
        assert response.status_code == 200
        # Server rejected the signature and issued a new signed token
        signed_token = response.cookies.get("starlette_admin_csrftoken")
        assert signed_token != "tampered.value"
        assert "." in signed_token

    def test_post_with_tampered_cookie_returns_403(self, bare_client):
        bare_client.cookies.set("starlette_admin_csrftoken", "tampered.value")
        response = bare_client.post(
            "/admin/item/create",
            data={"name": "x"},
        )
        assert response.status_code == 403

    def test_post_with_validly_signed_but_wrong_token_returns_403(self, bare_client):
        signer = URLSafeSerializer("test-secret", salt="starlette-admin-csrf")
        wrong_token = signer.dumps("different-token")

        bare_client.get("/admin/item/list")
        response = bare_client.post(
            "/admin/item/create",
            headers={"X-CSRFToken": wrong_token},
            data={"name": "x"},
        )
        assert response.status_code == 403
        assert b"CSRF token invalid" in response.content

    def test_post_with_json_content_type_returns_403(self, bare_client):
        bare_client.get("/admin/item/list")
        response = bare_client.post(
            "/admin/item/create",
            json={"name": "x"},
        )
        assert response.status_code == 403
        assert b"CSRF token missing" in response.content


class TestCsrfLogout:
    """Verify that the logout POST route is also covered by CSRFMiddleware.

    A forged cross-site POST to /logout must be rejected before the session is
    cleared; otherwise, an attacker can force a victim out of their session.
    The CSRFMiddleware wraps all routes in the admin mount, including the auth
    routes added by the provider.
    """

    @pytest.fixture()
    def auth_app(self):
        from starlette.middleware.sessions import SessionMiddleware
        from starlette_admin.auth import AdminUser, AuthProvider
        from starlette_admin.exceptions import LoginFailed

        class _SimpleAuth(AuthProvider):
            async def login(self, username, password, remember_me, request):
                if username == "admin" and password == "admin":
                    request.session["user"] = username
                    return
                raise LoginFailed("bad credentials")

            async def logout(self, request):
                request.session.clear()

            async def authenticate(self, request):
                if request.session.get("user"):
                    return AdminUser(username=request.session["user"])
                return None

        admin = BaseAdmin(
            secret_key="csrf-logout-test-secret",
            auth_provider=_SimpleAuth(),
            middlewares=[Middleware(SessionMiddleware, secret_key="session-secret")],
        )
        app = Starlette()
        admin.add_view(ItemView(Item))
        admin.mount_to(app)
        return app

    def test_logout_post_without_csrf_token_returns_403(self, auth_app):
        client = TestClient(auth_app, raise_server_exceptions=False)
        # Do NOT seed the CSRF cookie (simulates a cross-site attacker).
        response = client.post("/admin/logout")
        assert response.status_code == 403

    def test_logout_post_with_valid_csrf_token_succeeds(self, auth_app):

        client = TestClient(auth_app, raise_server_exceptions=False)
        # Obtain a CSRF cookie first, then log in.
        client.get("/admin/login")
        csrf_token = client.cookies.get("starlette_admin_csrftoken", "")
        client.post(
            "/admin/login",
            data={"username": "admin", "password": "admin"},
            headers={"X-CSRFToken": csrf_token},
            follow_redirects=False,
        )
        # Now logout with the token (should succeed, redirect to index).
        response = client.post(
            "/admin/logout",
            headers={"X-CSRFToken": csrf_token},
            follow_redirects=False,
        )
        assert response.status_code == 303
