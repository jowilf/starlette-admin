"""Integration tests for FileField / ImageField with LocalStorage.

Covers the full lifecycle routed through BaseAdmin: upload on create, URL
rendering on list/detail, replace and delete-checkbox on edit, and record
deletion (both bulk action and row action).
"""

import io
from pathlib import Path

import pytest
from PIL import Image
from starlette.applications import Starlette
from starlette_admin import BaseAdmin, FileField, ImageField, IntegerField, StringField
from starlette_admin.storage import LocalStorage

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


def make_png(width: int = 10, height: int = 4) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (width, height)).save(buf, "PNG")
    return buf.getvalue()


class Article(TinydbBaseModel):
    title: str = ""
    cover: dict | None = None
    attachments: list[dict] = []


class ArticleView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        ImageField(
            "cover",
            storage=None,  # patched per-fixture via class attr
            upload_folder="covers/",
            max_size=10 * 1024 * 1024,
        ),
        FileField(
            "attachments",
            storage=None,  # patched per-fixture
            upload_folder="att/",
            multiple=True,
            accept=".txt,.pdf",
        ),
    ]


@pytest.fixture()
def storage_and_client(tmp_path: Path):
    """Create a fresh LocalStorage, patch it onto the view fields, and return
    both so tests can inspect the filesystem."""
    storage = LocalStorage(base_dir=tmp_path, name=f"test-{id(tmp_path)}")
    for f in ArticleView.fields:
        if hasattr(f, "storage"):
            f.storage = storage  # type: ignore[attr-defined]

    ArticleView._db.truncate()
    app = Starlette()
    admin = BaseAdmin()
    admin.add_view(ArticleView(Article))
    admin.mount_to(app)
    client = CsrfTestClient(
        app, base_url="http://testserver", raise_server_exceptions=True
    )
    yield storage, client
    # clean up class-level storage references
    for f in ArticleView.fields:
        if hasattr(f, "storage"):
            f.storage = None  # type: ignore[attr-defined]


def _upload(content: bytes, filename: str, content_type: str = "text/plain"):
    return (filename, io.BytesIO(content), content_type)


# ── create ────────────────────────────────────────────────────────────────────


def test_create_saves_file_and_image(storage_and_client, tmp_path):
    storage, client = storage_and_client
    png = make_png(12, 7)
    r = client.post(
        "/admin/article/create",
        data={"title": "Hello"},
        files=[
            ("cover", ("cover.png", io.BytesIO(png), "image/png")),
            ("attachments", ("note.txt", io.BytesIO(b"note"), "text/plain")),
            ("attachments", ("readme.txt", io.BytesIO(b"readme"), "text/plain")),
        ],
        follow_redirects=False,
    )
    assert r.status_code == 303

    obj = ArticleView._get(1)
    assert obj is not None
    assert obj.cover is not None
    assert obj.cover["storage"] == storage.name
    assert obj.cover["key"].startswith("covers/")
    assert obj.cover["content_type"] == "image/png"
    assert obj.cover["width"] == 12
    assert obj.cover["height"] == 7

    assert len(obj.attachments) == 2
    filenames = {a["filename"] for a in obj.attachments}
    assert filenames == {"note.txt", "readme.txt"}
    for att in obj.attachments:
        assert att["key"].startswith("att/")
        assert (tmp_path / att["key"]).exists()

    assert (tmp_path / obj.cover["key"]).exists()


def test_create_no_file_stores_none(storage_and_client):
    _storage, client = storage_and_client
    r = client.post(
        "/admin/article/create",
        data={"title": "No file"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    obj = ArticleView._get(1)
    assert obj.cover is None
    assert obj.attachments == []


def test_create_invalid_accept_returns_422(storage_and_client):
    _storage, client = storage_and_client
    r = client.post(
        "/admin/article/create",
        data={"title": "Bad type"},
        files={"attachments": _upload(b"x", "evil.exe", "application/exe")},
        follow_redirects=False,
    )
    assert r.status_code == 422


def test_create_oversize_returns_422(storage_and_client):
    _storage, client = storage_and_client
    for f in ArticleView.fields:
        if isinstance(f, ImageField):
            f.max_size = 5  # tiny limit
    try:
        r = client.post(
            "/admin/article/create",
            data={"title": "Big"},
            files={"cover": _upload(make_png(), "x.png", "image/png")},
            follow_redirects=False,
        )
        assert r.status_code == 422
    finally:
        for f in ArticleView.fields:
            if isinstance(f, ImageField):
                f.max_size = 10 * 1024 * 1024


# ── list / detail render ──────────────────────────────────────────────────────


def test_list_and_detail_render_file_urls(storage_and_client, tmp_path):
    storage, client = storage_and_client
    # seed a record with cover
    r = client.post(
        "/admin/article/create",
        data={"title": "With cover"},
        files={"cover": _upload(make_png(), "x.png", "image/png")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    obj = ArticleView._get(1)
    key = obj.cover["key"]

    list_r = client.get("/admin/article/list")
    assert list_r.status_code == 200
    # The file-serving URL should appear in the rendered HTML
    assert f"/_files/{storage.name}/{key}" in list_r.text

    detail_r = client.get("/admin/article/detail?pk=1")
    assert detail_r.status_code == 200
    assert f"/_files/{storage.name}/{key}" in detail_r.text


def test_list_falls_back_to_full_image_without_thumbnail(storage_and_client):
    """Rows without a thumbnail (thumbnail_size unset, the default) render the
    full image in the list avatar."""
    storage, client = storage_and_client
    client.post(
        "/admin/article/create",
        data={"title": "No thumbnail"},
        files={"cover": _upload(make_png(), "x.png", "image/png")},
        follow_redirects=False,
    )
    key = ArticleView._get(1).cover["key"]

    list_r = client.get("/admin/article/list")
    assert list_r.status_code == 200
    assert (
        f"background-image: url('http://testserver/admin/_files/{storage.name}/{key}')"
        in list_r.text
    )


def test_list_prefers_thumbnail_url_when_present(storage_and_client, tmp_path):
    storage, client = storage_and_client
    cover_field = next(f for f in ArticleView.fields if f.name == "cover")
    cover_field.thumbnail_size = (5, 5)
    try:
        r = client.post(
            "/admin/article/create",
            data={"title": "With thumbnail"},
            files={"cover": _upload(make_png(20, 10), "x.png", "image/png")},
            follow_redirects=False,
        )
        assert r.status_code == 303
        obj = ArticleView._get(1)
        thumbnail_key = obj.cover["thumbnail"]["key"]
        assert (tmp_path / thumbnail_key).exists()

        list_r = client.get("/admin/article/list")
        assert list_r.status_code == 200
        assert (
            f"background-image: url('http://testserver/admin/_files/{storage.name}/{thumbnail_key}')"
            in list_r.text
        )
    finally:
        cover_field.thumbnail_size = None


# ── edit: replace ─────────────────────────────────────────────────────────────


def test_edit_replaces_old_file(storage_and_client, tmp_path):
    _storage, client = storage_and_client
    png = make_png()
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files={"cover": _upload(png, "old.png", "image/png")},
        follow_redirects=False,
    )
    old_key = ArticleView._get(1).cover["key"]

    r = client.post(
        "/admin/article/edit?pk=1",
        data={"title": "A"},
        files={"cover": _upload(make_png(8, 6), "new.png", "image/png")},
        follow_redirects=False,
    )
    assert r.status_code == 303
    obj = ArticleView._get(1)
    assert obj.cover["key"] != old_key
    assert (tmp_path / obj.cover["key"]).exists()


def test_edit_carry_through_when_no_new_upload(storage_and_client, tmp_path):
    _storage, client = storage_and_client
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files={"cover": _upload(make_png(), "a.png", "image/png")},
        follow_redirects=False,
    )
    original_key = ArticleView._get(1).cover["key"]

    r = client.post(
        "/admin/article/edit?pk=1",
        data={"title": "B"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert ArticleView._get(1).cover["key"] == original_key
    assert (tmp_path / original_key).exists()


def test_edit_delete_checkbox_clears_field(storage_and_client):
    _storage, client = storage_and_client
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files={"cover": _upload(make_png(), "a.png", "image/png")},
        follow_redirects=False,
    )

    r = client.post(
        "/admin/article/edit?pk=1",
        data={"title": "A", "_cover-delete": "on"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert ArticleView._get(1).cover is None


def test_edit_delete_checkbox_multiple_clears_list(storage_and_client):
    _storage, client = storage_and_client
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files=[
            ("attachments", ("a.txt", io.BytesIO(b"alpha"), "text/plain")),
            ("attachments", ("b.txt", io.BytesIO(b"beta"), "text/plain")),
        ],
        follow_redirects=False,
    )
    assert len(ArticleView._get(1).attachments) == 2

    r = client.post(
        "/admin/article/edit?pk=1",
        data={"title": "A", "_attachments-delete": "on"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert ArticleView._get(1).attachments == []


# ── delete record ─────────────────────────────────────────────────────────────


def test_bulk_delete_removes_record(storage_and_client, tmp_path):
    _storage, client = storage_and_client
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files={"cover": _upload(make_png(), "a.png", "image/png")},
        follow_redirects=False,
    )
    key = ArticleView._get(1).cover["key"]

    r = client.post(
        "/admin/_api/article/action",
        params={"name": "delete", "pks": ["1"]},
    )
    assert r.status_code == 200
    assert ArticleView._len() == 0
    # The storage file is NOT deleted; callers manage that themselves.
    assert (tmp_path / key).exists()


def test_row_delete_removes_record(storage_and_client, tmp_path):
    _storage, client = storage_and_client
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files={"cover": _upload(make_png(), "a.png", "image/png")},
        follow_redirects=False,
    )
    key = ArticleView._get(1).cover["key"]

    r = client.post(
        "/admin/_api/article/row-action",
        params={"name": "delete", "pk": "1"},
    )
    assert r.status_code == 200
    assert ArticleView._len() == 0
    # The storage file is NOT deleted; callers manage that themselves.
    assert (tmp_path / key).exists()


# ── file serving ──────────────────────────────────────────────────────────────


def test_file_serving_route(storage_and_client, tmp_path):
    storage, client = storage_and_client
    png = make_png()
    client.post(
        "/admin/article/create",
        data={"title": "A"},
        files={"cover": _upload(png, "a.png", "image/png")},
        follow_redirects=False,
    )
    key = ArticleView._get(1).cover["key"]

    r = client.get(f"/admin/_files/{storage.name}/{key}")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


def test_file_serving_unknown_key_returns_404(storage_and_client):
    storage, client = storage_and_client
    r = client.get(f"/admin/_files/{storage.name}/does-not-exist.txt")
    assert r.status_code == 404


def test_file_serving_unknown_storage_returns_404(storage_and_client):
    _, client = storage_and_client
    r = client.get("/admin/_files/no-such-storage/x.txt")
    assert r.status_code == 404


def test_file_serving_path_traversal_rejected(storage_and_client):
    storage, client = storage_and_client
    r = client.get(f"/admin/_files/{storage.name}/../../etc/passwd")
    assert r.status_code == 404


# ── no-storage fallback (legacy behavior) ────────────────────────────────────


def test_no_storage_fields_return_raw_upload_tuple(tmp_path):
    """Without a storage the field hands (upload, delete_flag) straight to the
    backend, as before. A TinyDB view that doesn't handle it will raise; here
    we verify the fallback doesn't interfere with storage-based fields.
    """

    class NoStorageArticle(TinydbBaseModel):
        title: str = ""

    class NoStorageView(TinydbModelView):
        model = NoStorageArticle
        fields = [
            IntegerField("id"),
            StringField("title"),
        ]

    app = Starlette()
    admin = BaseAdmin()
    admin.add_view(NoStorageView(NoStorageArticle))
    admin.mount_to(app)
    client = CsrfTestClient(app, raise_server_exceptions=True)

    r = client.post(
        "/admin/no-storage-article/create",
        data={"title": "plain"},
        follow_redirects=False,
    )
    assert r.status_code == 303
    assert NoStorageView._get(1).title == "plain"
