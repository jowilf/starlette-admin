import csv
import io
import zipfile
from typing import Any

import pytest
import pytest_asyncio
import sqlalchemy_file as sf
from httpx2 import AsyncClient
from sqlalchemy import Integer, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView
from starlette_admin.exceptions import FormValidationError
from starlette_admin.export import EXPORT_FORMATS, is_extra_available
from starlette_admin.importers import IMPORT_FORMATS

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


_AVAILABLE_EXPORT_FORMATS = sorted(
    fmt
    for fmt, exporter in EXPORT_FORMATS.items()
    if not exporter.requires or is_extra_available(exporter.requires)
)
_AVAILABLE_IMPORT_FORMATS = {
    fmt
    for fmt, importer in IMPORT_FORMATS.items()
    if not importer.requires or is_extra_available(importer.requires)
} - {
    # dbf uppercases headers to fit its 10-char field-name limit, so parsed
    # rows never match the view's mixed-case field labels/names.
    "dbf"
}


class Base(DeclarativeBase):
    pass


class Document(Base):
    __tablename__ = "document"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    attachment = mapped_column(sf.FileField())


class Tag(Base):
    __tablename__ = "tag"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class Category(Base):
    __tablename__ = "category"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(100), nullable=False)


class Item(Base):
    __tablename__ = "item"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))


class DocumentView(ModelView):
    key = "document"

    def can_import(self, request: Any) -> bool:
        return True


class TagView(ModelView):
    key = "tag"

    def can_import(self, request: Any) -> bool:
        return True


class CategoryView(ModelView):
    key = "category"

    def can_import(self, request: Any) -> bool:
        return True

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}
        label = data.get("label")
        if label is None or len(label) < 3:
            errors["label"] = "Label must be at least 3 characters"
        elif "invalid" in label.lower():
            errors["label"] = "Label cannot contain 'invalid'"
        if errors:
            raise FormValidationError(errors)
        await super().validate(request, data)


class ItemView(ModelView):
    key = "item"
    exporters = _AVAILABLE_EXPORT_FORMATS
    importers = [f for f in _AVAILABLE_EXPORT_FORMATS if f in _AVAILABLE_IMPORT_FORMATS]

    def can_import(self, request: Any) -> bool:
        return True


@pytest.fixture
def engine(sqla_backend, sqla_storage_factory) -> Engine:
    engine = get_test_engine()
    Base.metadata.create_all(engine)
    StorageManager._clear()
    StorageManager.add_storage("test", sqla_storage_factory("test-import-export"))
    yield engine
    for obj in StorageManager.get().list_objects():
        obj.delete()
    StorageManager.get().delete()
    Base.metadata.drop_all(engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine) -> Admin:
    admin = Admin(engine)
    admin.add_view(DocumentView(Document))
    admin.add_view(TagView(Tag))
    admin.add_view(CategoryView(Category))
    admin.add_view(ItemView(Item))
    return admin


@pytest.fixture
def app(admin: Admin) -> Starlette:
    application = Starlette()
    admin.mount_to(application)
    return application


@pytest_asyncio.fixture
async def client(app: Starlette) -> AsyncClient:
    async with csrf_async_client(app) as c:
        yield c


async def test_export_csv_with_sqlalchemy_file_field(
    client: AsyncClient, session: Session, fake_image
) -> None:
    """Exporting a view with sqlalchemy-file fields returns a ZIP bundle.

    The URL-only file references produced by the SQLA file-field serializer are
    rewritten to ``assets/url/...`` paths in the CSV; in a real deployment the
    exporter would fetch those files over HTTP and include them in the ZIP.
    """
    doc = Document(
        title="Report",
        attachment=sf.File(fake_image, filename="report.png"),
    )
    session.add(doc)
    session.commit()

    response = await client.post(
        "/admin/_api/document/action",
        params={"name": "export"},
        data={"scope": "page", "format": "csv"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    with zipfile.ZipFile(io.BytesIO(response.content)) as zf:
        names = set(zf.namelist())
        assert "document.csv" in names
        csv_text = zf.read("document.csv").decode()
        assert "Report" in csv_text
        assert "assets/url/" in csv_text


async def test_export_csv_without_file_field(
    client: AsyncClient, session: Session
) -> None:
    """Exporting a view without file fields returns the CSV directly."""
    session.add(Tag(name="urgent"))
    session.commit()

    response = await client.post(
        "/admin/_api/tag/action",
        params={"name": "export"},
        data={"scope": "page", "format": "csv"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert b"urgent" in response.content


async def test_import_csv_ignores_sqlalchemy_file_field(
    client: AsyncClient, session: Session
) -> None:
    """FileField is always excluded from import: an `attachment` column in the
    upload is ignored, and the created record's file field stays empty."""
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["title", "attachment"])
    writer.writeheader()
    writer.writerow({"title": "Imported report", "attachment": "assets/url/report.png"})
    csv_bytes = csv_buffer.getvalue().encode()

    response = await client.post(
        "/admin/_api/document/import",
        data={"format": "csv"},
        files={"file": ("import.csv", io.BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rows_total"] == 1
    assert data["rows_created"] == 1
    assert not data["has_errors"]

    doc = session.query(Document).filter_by(title="Imported report").one()
    assert doc.attachment is None


async def test_import_csv_without_file_field(
    client: AsyncClient, session: Session
) -> None:
    """Importing a plain CSV works for views without file fields."""
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["name"])
    writer.writeheader()
    writer.writerow({"name": "imported-tag"})
    csv_bytes = csv_buffer.getvalue().encode()

    response = await client.post(
        "/admin/_api/tag/import",
        data={"format": "csv"},
        files={"file": ("import.csv", io.BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rows_total"] == 1
    assert data["rows_created"] == 1
    assert not data["has_errors"]

    tag = session.query(Tag).filter_by(name="imported-tag").one()
    assert tag.name == "imported-tag"


async def test_import_csv_with_validation_errors(
    client: AsyncClient, session: Session
) -> None:
    """Validation errors during import are reported per row; valid rows are created."""
    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["label"])
    writer.writeheader()
    writer.writerow({"label": "valid-label"})
    writer.writerow({"label": "ab"})
    writer.writerow({"label": "this-is-invalid"})
    csv_bytes = csv_buffer.getvalue().encode()

    response = await client.post(
        "/admin/_api/category/import",
        data={"format": "csv"},
        files={"file": ("import.csv", io.BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rows_total"] == 3
    assert data["rows_created"] == 1
    assert data["has_errors"] is True
    assert len(data["errors"]) == 2
    assert data["errors"][0] == {
        "row": 2,
        "field": "label",
        "message": "Label must be at least 3 characters",
    }
    assert data["errors"][1] == {
        "row": 3,
        "field": "label",
        "message": "Label cannot contain 'invalid'",
    }

    created = session.query(Category).filter_by(label="valid-label").one()
    assert created.label == "valid-label"


async def test_import_csv_recovers_from_integrity_error(
    client: AsyncClient, session: Session
) -> None:
    """A UNIQUE constraint violation on one row (e.g. a duplicate primary key)
    is reported as a row error without poisoning the SQLAlchemy session, so
    later rows in the same upload still get created."""
    session.add(Tag(id=1, name="existing"))
    session.commit()

    csv_buffer = io.StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=["id", "name"])
    writer.writeheader()
    writer.writerow({"id": 1, "name": "duplicate-id"})
    writer.writerow({"id": 2, "name": "new-tag"})
    csv_bytes = csv_buffer.getvalue().encode()

    response = await client.post(
        "/admin/_api/tag/import",
        data={"format": "csv"},
        files={"file": ("import.csv", io.BytesIO(csv_bytes), "text/csv")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rows_total"] == 2
    assert data["rows_created"] == 1
    assert data["has_errors"] is True
    assert len(data["errors"]) == 1
    assert data["errors"][0]["row"] == 1

    tag = session.query(Tag).filter_by(name="new-tag").one()
    assert tag.id == 2


@pytest.mark.parametrize("format", _AVAILABLE_EXPORT_FORMATS)
async def test_export_import_roundtrip_all_formats(
    client: AsyncClient, session: Session, format: str
) -> None:
    session.add(Item(name="roundtrip"))
    session.commit()

    response = await client.post(
        "/admin/_api/item/action",
        params={"name": "export"},
        data={"scope": "page", "format": format},
    )
    assert response.status_code == 200
    content = response.content

    if format not in _AVAILABLE_IMPORT_FORMATS:
        pytest.skip(f"{format!r} has no importer; export-only format")

    session.query(Item).delete()
    session.commit()

    response = await client.post(
        "/admin/_api/item/import",
        data={"format": format},
        files={
            "file": (
                f"import.{format}",
                io.BytesIO(content),
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["rows_total"] == 1
    assert data["rows_created"] == 1
    assert not data["has_errors"]

    item = session.query(Item).filter_by(name="roundtrip").one()
    assert item.name == "roundtrip"
