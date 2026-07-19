import html
from datetime import date, datetime
from enum import StrEnum

import pytest
from pydantic import Field
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    BooleanField,
    DateField,
    DateTimeField,
    EnumField,
    IntegerField,
    JSONField,
    StringField,
    TagsField,
)
from starlette_admin.exceptions import FormValidationError

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class Status(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"


class Item(TinydbBaseModel):
    title: str | None = None
    priority: int | None = None
    published: bool | None = None
    status: str | None = None
    scheduled: date | None = None
    created_at: datetime | None = None
    labels: list[str] = Field(default_factory=list)
    meta: dict | None = None


class ItemView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title", default="New item"),
        IntegerField("priority", default=3),
        BooleanField("published", default=True),
        EnumField("status", enum=Status, default=Status.DRAFT),
        DateField("scheduled", default=date(2025, 1, 1)),
        DateTimeField("created_at", default=lambda: datetime(2025, 1, 1, 8, 30)),
        TagsField("labels", default=["a", "b"]),
        JSONField("meta", default={"x": 1}),
    ]


class CallableDefaultItem(TinydbBaseModel):
    title: str | None = None


class CallableDefaultItemView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title", default=lambda request: f"from-{request.method}"),
    ]


class ValidationItem(TinydbBaseModel):
    title: str | None = None


class ValidationItemView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title", default="Default title"),
    ]

    async def validate_data(self, data: dict) -> None:
        raise FormValidationError({"title": "always fails"})


class ReadOnlyItem(TinydbBaseModel):
    title: str | None = None
    sku: str = "server-sku"


class ReadOnlyItemView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        StringField("sku", read_only=True),
    ]


@pytest.fixture
def client() -> TestClient:
    admin = BaseAdmin()
    app = Starlette()
    admin.add_view(ItemView(Item))
    admin.add_view(CallableDefaultItemView(CallableDefaultItem))
    admin.add_view(ValidationItemView(ValidationItem))
    admin.add_view(ReadOnlyItemView(ReadOnlyItem))
    admin.mount_to(app)
    ItemView._db.truncate()
    CallableDefaultItemView._db.truncate()
    ValidationItemView._db.truncate()
    ReadOnlyItemView._db.truncate()
    return CsrfTestClient(app, base_url="http://testserver")


class TestFieldDefaults:
    def test_create_page_prefills_static_defaults(self, client: TestClient) -> None:
        response = client.get("/admin/item/create")
        assert response.status_code == 200
        text = html.unescape(response.text)

        # text input
        assert 'value="New item"' in text
        # integer input
        assert 'value="3"' in text
        # boolean switch checked
        assert 'type="checkbox"' in text
        assert "checked" in text
        # enum selected option
        assert '<option value="draft"' in text
        assert "selected>DRAFT" in text
        # date input
        assert 'value="2025-01-01"' in text
        # datetime default is serialized to ISO format for the picker input
        assert 'value="2025-01-01T08:30:00"' in text
        # tags input has selected options
        assert '<option selected="selected">a</option>' in text
        assert '<option selected="selected">b</option>' in text
        # json input
        assert '"x": 1' in text

    def test_create_page_uses_callable_default(self, client: TestClient) -> None:
        response = client.get("/admin/callable-default-item/create")
        assert response.status_code == 200
        assert 'value="from-GET"' in response.text

    def test_edit_page_ignores_default(self, client: TestClient) -> None:
        doc_id = ItemView._db.insert(Item(title="Existing item").to_tinydb_doc())
        response = client.get(f"/admin/item/edit?pk={doc_id}")
        assert response.status_code == 200
        assert 'value="Existing item"' in response.text
        assert "New item" not in response.text

    def test_validation_error_keeps_submitted_value(self, client: TestClient) -> None:
        response = client.post(
            "/admin/validation-item/create",
            data={"title": "Submitted title"},
            follow_redirects=False,
        )
        assert response.status_code == 422
        assert 'value="Submitted title"' in response.text
        assert "Default title" not in response.text


class TestReadOnlyField:
    def test_create_ignores_read_only_field(self, client: TestClient) -> None:
        response = client.post(
            "/admin/read-only-item/create",
            data={
                "title": "New item",
                # sku is read-only: a submitted value must be ignored in favor
                # of the model default.
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        item = ReadOnlyItemView._get(1)
        assert item is not None
        assert item.sku == "server-sku"

    def test_edit_ignores_read_only_field(self, client: TestClient) -> None:
        doc_id = ReadOnlyItemView._db.insert(
            ReadOnlyItem(title="Existing item").to_tinydb_doc()
        )
        response = client.post(
            f"/admin/read-only-item/edit?pk={doc_id}",
            data={
                "title": "Updated item",
                # sku is read-only: attempting to change it via the edit form
                # must have no effect.
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        item = ReadOnlyItemView._get(doc_id)
        assert item is not None
        assert item.title == "Updated item"
        assert item.sku == "server-sku"
