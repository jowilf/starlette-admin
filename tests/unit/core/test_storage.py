"""Unit tests for starlette_admin.storage and the storage-related FileField logic."""

import io
import sys
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image
from starlette.exceptions import HTTPException
from starlette_admin import BaseAdmin, FileField, ImageField
from starlette_admin.storage import (
    FileInfo,
    LocalStorage,
    UnknownStorageError,
    delete_stored_files,
    get_storage,
    secure_filename,
)

from tests.conftest import make_png, make_upload


def make_jpeg(width: int = 10, height: int = 4) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height)).save(buffer, "JPEG")
    return buffer.getvalue()


def _make_request() -> MagicMock:
    mock = MagicMock()
    mock.app.state.ROUTE_NAME = "admin"
    mock.url_for.side_effect = lambda name, **params: (
        f"http://testserver/{name}/{params['storage']}/{params['path']}"
    )
    return mock


# ── secure_filename ───────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("photo.png", "photo.png"),
        ("my photo (1).png", "my_photo_1_.png"),
        ("../../etc/passwd", "passwd"),
        ("..\\..\\windows\\cmd.exe", "cmd.exe"),
        ("...", "file"),
        ("", "file"),
    ],
)
def test_secure_filename(raw, expected):
    assert secure_filename(raw) == expected


# ── FileInfo ──────────────────────────────────────────────────────────────────


def test_file_info_to_dict_drops_none_and_serializes_datetime():
    uploaded_at = datetime(2026, 6, 11, 10, 30, tzinfo=UTC)
    info = FileInfo(
        filename="a.txt",
        content_type="text/plain",
        size=4,
        storage="local",
        key="a.txt",
        uploaded_at=uploaded_at,
    )
    data = info.to_dict()
    assert data["uploaded_at"] == "2026-06-11T10:30:00+00:00"
    assert "width" not in data
    assert "height" not in data


def test_file_info_from_dict_roundtrip():
    uploaded_at = datetime(2026, 6, 11, 10, 30, tzinfo=UTC)
    info = FileInfo(
        filename="a.png",
        content_type="image/png",
        size=4,
        storage="local",
        key="x/a.png",
        uploaded_at=uploaded_at,
        width=10,
        height=4,
    )
    assert FileInfo.from_dict(info.to_dict()) == info


def test_file_info_thumbnail_roundtrip():
    info = FileInfo(
        filename="a.png",
        content_type="image/png",
        size=100,
        storage="local",
        key="photos/a.png",
        width=20,
        height=10,
        thumbnail={"key": "photos/a.thumb.png", "width": 5, "height": 2, "size": 30},
    )
    assert FileInfo.from_dict(info.to_dict()) == info


def test_file_info_from_dict_ignores_unknown_keys():
    info = FileInfo.from_dict(
        {
            "filename": "a.txt",
            "content_type": "text/plain",
            "size": 1,
            "storage": "local",
            "key": "a.txt",
            "not_a_field": True,
        }
    )
    assert info.filename == "a.txt"
    assert info.uploaded_at is None


# ── registry ──────────────────────────────────────────────────────────────────


def test_get_storage_returns_registered_instance(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="registry-test")
    assert get_storage("registry-test") is storage


def test_get_storage_unknown_name_raises():
    with pytest.raises(UnknownStorageError):
        get_storage("never-registered")


def test_storage_requires_a_name(tmp_path):
    with pytest.raises(AssertionError):
        LocalStorage(base_dir=tmp_path, name="")


# ── delete_stored_files ───────────────────────────────────────────────────────


async def test_delete_stored_files_handles_all_value_shapes(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="delete-test")
    info1 = await storage.save(make_upload(filename="one.txt"), "one.txt")
    info2 = await storage.save(make_upload(filename="two.txt"), "two.txt")
    await delete_stored_files(
        [
            info1,
            info2.to_dict(),
            {"storage": "never-registered", "key": "x"},
            {"unrelated": "dict"},
            None,
        ]
    )
    assert not (tmp_path / "one.txt").exists()
    assert not (tmp_path / "two.txt").exists()


async def test_delete_stored_files_removes_thumbnail_too(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="delete-thumb-test")
    info = await storage.save(make_upload(filename="photo.png"), "photo.png")
    thumb_info = await storage.save(
        make_upload(filename="photo.thumb.png"), "photo.thumb.png"
    )
    await delete_stored_files(
        {
            **info.to_dict(),
            "thumbnail": {"key": thumb_info.key, "width": 5, "height": 5},
        }
    )
    assert not (tmp_path / info.key).exists()
    assert not (tmp_path / thumb_info.key).exists()


# ── Generic backend tests (local + s3) ────────────────────────────────────────


async def test_storage_save_returns_file_info(storage):
    info = await storage.save(make_upload(b"hello", "a.txt"), "docs/a.txt")
    assert info.storage == storage.name
    assert info.key.endswith("a.txt")
    assert info.size == 5
    assert info.content_type == "text/plain"
    assert info.uploaded_at is not None


async def test_storage_save_never_overwrites(storage):
    first = await storage.save(make_upload(b"first"), "a.txt")
    second = await storage.save(make_upload(b"second"), "a.txt")
    assert first.key != second.key


async def test_storage_delete_is_idempotent(storage):
    info = await storage.save(make_upload(), "del.txt")
    await storage.delete(info.key)
    await storage.delete(info.key)  # already gone (no error)


async def test_storage_url_contains_key(storage):
    info = await storage.save(make_upload(), "url.txt")
    url = await storage.url(_make_request(), info.key)
    assert info.key in url


async def test_storage_serve_returns_response(storage):
    from starlette.responses import Response

    info = await storage.save(make_upload(b"data", "serve.txt"), "serve.txt")
    resp = await storage.serve(_make_request(), info.key)
    assert isinstance(resp, Response)


# ── LocalStorage-specific tests ───────────────────────────────────────────────


async def test_local_storage_save_writes_to_disk(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="save-test")
    info = await storage.save(make_upload(b"hello"), "docs/a.txt")
    assert (tmp_path / "docs" / "a.txt").read_bytes() == b"hello"
    assert info.storage == "save-test"
    assert info.key == "docs/a.txt"


async def test_local_storage_delete_removes_file(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="idempotent-test")
    info = await storage.save(make_upload(), "a.txt")
    await storage.delete(info.key)
    assert not (tmp_path / "a.txt").exists()


async def test_local_storage_rejects_path_traversal(tmp_path):
    s = LocalStorage(base_dir=tmp_path / "uploads", name="traversal-test")
    with pytest.raises(HTTPException):
        await s.delete("../outside.txt")


async def test_local_storage_rejects_symlink_escape(tmp_path):
    """A key without '..' can still escape base_dir via a symlink; this must be caught."""
    if sys.platform == "win32":
        pytest.skip("symlinks not supported on Windows")
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (uploads / "escape").symlink_to(outside)
    s = LocalStorage(base_dir=uploads, name=f"symlink-{id(tmp_path)}")
    with pytest.raises(HTTPException):
        await s.delete("escape/secret.txt")


# ── S3-specific tests ─────────────────────────────────────────────────────────


async def test_s3_presigned_url(s3_private_storage):
    info = await s3_private_storage.save(make_upload(b"secret", "s.txt"), "s.txt")
    url = await s3_private_storage.url(MagicMock(), info.key)
    assert "X-Amz-Signature" in url or "AWSAccessKeyId" in url or "Signature" in url


def test_s3_public_url_aws_format():
    """_public_url uses the AWS URL pattern when no endpoint_url is configured."""
    from starlette_admin.storage.s3 import S3Storage

    storage = S3Storage(bucket="my-bucket", region="eu-west-1", name="s3-aws-url-test")
    url = storage._public_url("uploads/photo.png")
    assert url == "https://my-bucket.s3.eu-west-1.amazonaws.com/uploads/photo.png"


def _make_s3_with_mock_client(error: Exception) -> tuple:
    """Return (storage, patch context) that raises *error* from get_object."""
    from starlette_admin.storage.s3 import S3Storage

    storage = S3Storage(
        bucket="b",
        endpoint_url="http://fake",
        name=f"s3-read-mock-{id(error)}",
    )
    mock_client = AsyncMock()
    mock_client.get_object.side_effect = error
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_client)
    mock_cm.__aexit__ = AsyncMock(return_value=False)
    mock_session = MagicMock()
    mock_session.create_client.return_value = mock_cm
    return storage, patch("aiobotocore.session.get_session", return_value=mock_session)


@pytest.mark.asyncio
async def test_s3_read_no_such_key_raises_file_not_found():
    """ClientError with NoSuchKey is mapped to FileNotFoundError."""
    from botocore.exceptions import ClientError

    exc = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "Not found"}}, "GetObject"
    )
    storage, ctx = _make_s3_with_mock_client(exc)
    with ctx, pytest.raises(FileNotFoundError):
        await storage.read("missing.txt")


@pytest.mark.asyncio
async def test_s3_read_404_raises_file_not_found():
    """ClientError with code 404 is also mapped to FileNotFoundError."""
    from botocore.exceptions import ClientError

    exc = ClientError({"Error": {"Code": "404", "Message": "Not found"}}, "GetObject")
    storage, ctx = _make_s3_with_mock_client(exc)
    with ctx, pytest.raises(FileNotFoundError):
        await storage.read("missing.txt")


@pytest.mark.asyncio
async def test_s3_read_reraises_other_client_errors():
    """ClientError codes other than NoSuchKey/404 propagate unchanged."""
    from botocore.exceptions import ClientError

    exc = ClientError(
        {"Error": {"Code": "AccessDenied", "Message": "Denied"}}, "GetObject"
    )
    storage, ctx = _make_s3_with_mock_client(exc)
    with ctx, pytest.raises(ClientError):
        await storage.read("file.txt")


# ── FileField.validate / accept matching ──────────────────────────────────────


@pytest.mark.asyncio
async def test_validate_upload_max_size():
    field = FileField("doc", max_size=3)
    with pytest.raises(ValueError, match="too large"):
        await field.validate(None, (make_upload(b"too big"), False), {})
    assert await field.validate(None, (make_upload(b"ok"), False), {}) is None


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("accept", "filename", "content_type", "ok"),
    [
        (".pdf", "doc.PDF", "application/octet-stream", True),
        (".pdf", "doc.txt", "text/plain", False),
        ("image/*", "x.bin", "image/png", True),
        ("image/*", "x.txt", "text/plain", False),
        ("text/plain", "x.txt", "text/plain", True),
        ("text/plain", "x.html", "text/html", False),
        (".pdf, image/*,", "photo.png", "image/png", True),
        (
            ",image/png",
            "x.png",
            "image/png",
            True,
        ),  # A leading comma results in an empty token, causing the loop to continue.
    ],
)
async def test_validate_upload_accept(accept, filename, content_type, ok):
    field = FileField("doc", accept=accept)
    upload = make_upload(b"x", filename, content_type)
    if ok:
        assert await field.validate(None, (upload, False), {}) is None
    else:
        with pytest.raises(ValueError, match="not allowed"):
            await field.validate(None, (upload, False), {})


@pytest.mark.asyncio
async def test_validate_upload_no_constraints():
    field = FileField("doc")
    assert await field.validate(None, (make_upload(b"anything"), False), {}) is None


# ── FileField.serialize_value ─────────────────────────────────────────────────


async def test_serialize_value_refreshes_url(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="serialize-test")
    info = await storage.save(make_upload(), "a.txt")
    field = FileField("doc", storage=storage)
    value = await field.serialize_value(_make_request(), info.to_dict())
    assert value["url"] == "http://testserver/admin:file/serialize-test/a.txt"


async def test_serialize_value_multiple(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="serialize-multi-test")
    info = await storage.save(make_upload(), "a.txt")
    field = FileField("doc", storage=storage, multiple=True)
    values = await field.serialize_value(_make_request(), [info, info.to_dict()])
    assert [v["url"] for v in values] == [
        "http://testserver/admin:file/serialize-multi-test/a.txt"
    ] * 2


async def test_serialize_value_exposes_thumbnail_url(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="serialize-thumb-test")
    info = await storage.save(make_upload(), "a.png")
    thumb_info = await storage.save(make_upload(), "a.thumb.png")
    field = ImageField("cover", storage=storage)
    stored = {
        **info.to_dict(),
        "thumbnail": {"key": thumb_info.key, "width": 5, "height": 5},
    }
    value = await field.serialize_value(_make_request(), stored)
    assert (
        value["thumbnail_url"]
        == f"http://testserver/admin:file/serialize-thumb-test/{thumb_info.key}"
    )


async def test_serialize_value_without_thumbnail_has_no_thumbnail_url(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="serialize-no-thumb-test")
    info = await storage.save(make_upload(), "a.png")
    field = ImageField("cover", storage=storage)
    value = await field.serialize_value(_make_request(), info.to_dict())
    assert "thumbnail_url" not in value


async def test_serialize_value_unknown_storage_passthrough():
    field = FileField("doc")
    stored = {"storage": "never-registered", "key": "a.txt", "url": "stale"}
    assert await field.serialize_value(_make_request(), stored) == stored


async def test_serialize_value_legacy_passthrough():
    """Without FileInfo metadata, values pass through unchanged (pre-storage behavior)."""
    field = FileField("doc")

    class FakeFile:
        url = "https://example.com/f.txt"

    fake = FakeFile()
    assert await field.serialize_value(_make_request(), fake) is fake
    assert await field.serialize_value(_make_request(), {"url": "x"}) == {"url": "x"}


# ── ImageField dimensions ─────────────────────────────────────────────────────


def test_image_field_enrich_adds_dimensions():
    field = ImageField("cover")
    info = FileInfo(
        filename="a.png", content_type="image/png", size=1, storage="s", key="a.png"
    )
    enriched = field._enrich_file_info(info, make_upload(make_png(12, 7), "a.png"))
    assert (enriched.width, enriched.height) == (12, 7)


def test_image_field_enrich_ignores_unreadable_image():
    field = ImageField("cover")
    info = FileInfo(
        filename="a.png", content_type="image/png", size=1, storage="s", key="a.png"
    )
    assert field._enrich_file_info(info, make_upload(b"not an image")) is info


def test_file_field_enrich_is_a_noop():
    field = FileField("doc")
    info = FileInfo(
        filename="a.txt", content_type="text/plain", size=1, storage="s", key="a.txt"
    )
    assert field._enrich_file_info(info, make_upload()) is info


# ── ImageField thumbnail generation ───────────────────────────────────────────


async def test_image_field_thumbnail_size_none_produces_no_thumbnail(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="thumb-none-test")
    field = ImageField("cover", storage=storage)  # thumbnail_size defaults to None
    upload = make_upload(make_png(20, 10), "cover.png", "image/png")
    info = await storage.save(upload, "cover.png")
    result = await field._post_store(info, upload)
    assert result.thumbnail is None


async def test_image_field_generates_bounded_thumbnail(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="thumb-gen-test")
    field = ImageField("cover", storage=storage, thumbnail_size=(5, 5))
    upload = make_upload(make_png(20, 10), "cover.png", "image/png")
    info = await storage.save(upload, "cover.png")
    result = await field._post_store(info, upload)

    assert result.thumbnail is not None
    assert result.thumbnail["key"] == "cover.thumb.png"
    assert result.thumbnail["width"] <= 5
    assert result.thumbnail["height"] <= 5
    # Aspect ratio (2:1) is preserved, modulo PIL's integer rounding.
    assert result.thumbnail["width"] > result.thumbnail["height"]
    with Image.open(tmp_path / result.thumbnail["key"]) as saved:
        assert saved.size == (result.thumbnail["width"], result.thumbnail["height"])


async def test_image_field_thumbnail_key_derivation_inserts_thumb_before_extension(
    tmp_path,
):
    storage = LocalStorage(base_dir=tmp_path, name="thumb-key-test")
    field = ImageField("cover", storage=storage, thumbnail_size=(5, 5))
    upload = make_upload(make_jpeg(20, 10), "cat.jpg", "image/jpeg")
    info = await storage.save(upload, "photos/cat.jpg")
    result = await field._post_store(info, upload)
    assert result.thumbnail["key"] == "photos/cat.thumb.jpg"


async def test_image_field_thumbnail_never_upscales(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="thumb-upscale-test")
    field = ImageField("cover", storage=storage, thumbnail_size=(500, 500))
    upload = make_upload(make_png(20, 10), "cover.png", "image/png")
    info = await storage.save(upload, "cover.png")
    result = await field._post_store(info, upload)
    assert (result.thumbnail["width"], result.thumbnail["height"]) == (20, 10)


async def test_image_field_thumbnail_generation_failure_falls_back(tmp_path):
    """A thumbnail failure must never fail the main upload: `_post_store`
    returns the info unchanged, with no `thumbnail` set."""
    storage = LocalStorage(base_dir=tmp_path, name="thumb-fail-test")
    field = ImageField("cover", storage=storage, thumbnail_size=(5, 5))
    info = FileInfo(
        filename="a.png", content_type="image/png", size=1, storage="s", key="a.png"
    )
    upload = make_upload(b"not an image")
    result = await field._post_store(info, upload)
    assert result.thumbnail is None


async def test_image_field_multiple_gets_one_thumbnail_per_file(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="thumb-multi-test")
    field = ImageField("gallery", storage=storage, multiple=True, thumbnail_size=(5, 5))
    upload1 = make_upload(make_png(20, 10), "a.png", "image/png")
    upload2 = make_upload(make_png(10, 20), "b.png", "image/png")
    info1 = await storage.save(upload1, "a.png")
    info2 = await storage.save(upload2, "b.png")
    result1 = await field._post_store(info1, upload1)
    result2 = await field._post_store(info2, upload2)

    assert result1.thumbnail["key"] == "a.thumb.png"
    assert result2.thumbnail["key"] == "b.thumb.png"
    assert (tmp_path / result1.thumbnail["key"]).exists()
    assert (tmp_path / result2.thumbnail["key"]).exists()


async def test_image_field_thumbnail_converts_rgba_source_reported_as_jpeg(tmp_path):
    """A real, correctly-decoded JPEG is never in P/RGBA mode, so this
    conversion guards a source whose reported format disagrees with its
    decoded mode. Reproduced here via a mocked `Image.open` result."""
    storage = LocalStorage(base_dir=tmp_path, name="thumb-rgba-jpeg-test")
    field = ImageField("cover", storage=storage, thumbnail_size=(5, 5))
    upload = make_upload(make_png(20, 10), "cover.png", "image/png")
    info = await storage.save(upload, "cover.png")

    def open_rgba_source(*_args, **_kwargs):
        source = Image.new("RGBA", (20, 10))
        source.format = "JPEG"
        return source

    # `Image.open` is called twice per store (dimension enrichment, then
    # thumbnailing); a fresh image per call avoids reusing one Pillow closes.
    with patch("PIL.Image.open", side_effect=open_rgba_source):
        result = await field._post_store(info, upload)

    assert result.thumbnail is not None
    with Image.open(tmp_path / result.thumbnail["key"]) as saved:
        assert saved.mode == "RGB"


async def test_image_field_thumbnail_falls_back_to_png_for_unsupported_save_format(
    tmp_path,
):
    """A source format that Pillow can't save under (raising `KeyError`)
    falls back to PNG rather than failing the upload."""
    storage = LocalStorage(base_dir=tmp_path, name="thumb-badformat-test")
    field = ImageField("cover", storage=storage, thumbnail_size=(5, 5))
    upload = make_upload(make_png(20, 10), "cover.png", "image/png")
    info = await storage.save(upload, "cover.png")

    def open_bogus_source(*_args, **_kwargs):
        source = Image.new("RGB", (20, 10))
        source.format = "BOGUS"
        return source

    with patch("PIL.Image.open", side_effect=open_bogus_source):
        result = await field._post_store(info, upload)

    assert result.thumbnail is not None
    assert result.thumbnail["key"] == "cover.thumb.png"
    with Image.open(tmp_path / result.thumbnail["key"]) as saved:
        assert saved.format == "PNG"


# ── LocalStorage.read ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_local_storage_read_returns_file_bytes(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="read-test")
    upload = make_upload(b"hello bytes", filename="test.txt")
    info = await storage.save(upload, "test.txt")
    data = await storage.read(info.key)
    assert data == b"hello bytes"


@pytest.mark.asyncio
async def test_local_storage_read_raises_file_not_found(tmp_path):
    storage = LocalStorage(base_dir=tmp_path, name="read-missing")
    with pytest.raises(FileNotFoundError):
        await storage.read("nonexistent/path.txt")


# ── BaseAdmin._storable_file_value ────────────────────────────────────────────


def test_storable_file_value_shapes():
    info = FileInfo(
        filename="a.txt", content_type="text/plain", size=1, storage="s", key="a.txt"
    )
    single = FileField("doc")
    multi = FileField("docs", multiple=True)
    assert BaseAdmin._storable_file_value(single, None) is None
    assert BaseAdmin._storable_file_value(multi, None) == []
    assert BaseAdmin._storable_file_value(single, info) == info.to_dict()
    assert BaseAdmin._storable_file_value(multi, [info, info.to_dict()]) == [
        info.to_dict(),
        info.to_dict(),
    ]
