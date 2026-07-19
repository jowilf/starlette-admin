"""Tests for ListField: list-of-scalar and list-of-CollectionField.

Rewritten for Pydantic v2 (the original skipped on v2). The removed
/admin/_api/{key}?pks= endpoint is replaced with direct stored-value
assertions via view._get().
"""

import pytest
from pydantic import BaseModel, Field
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    CollectionField,
    IntegerField,
    ListField,
    StringField,
    URLField,
)

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class ExtraItem(BaseModel):
    key: str = ""
    value: str = ""


class Setting(TinydbBaseModel):
    hosts: list[str] = Field(default_factory=list)
    extras: list[ExtraItem] = Field(default_factory=list)


class SettingView(TinydbModelView):
    fields = [
        IntegerField("id"),
        ListField(URLField("hosts")),
        ListField(
            CollectionField(
                "extras",
                fields=[
                    StringField("key"),
                    StringField("value"),
                ],
            )
        ),
    ]


class TestListField:
    @pytest.fixture(autouse=True)
    def reset_db(self):
        SettingView._db.truncate()

    @pytest.fixture
    def client(self) -> TestClient:
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SettingView(Setting))
        admin.mount_to(app)
        return CsrfTestClient(app, base_url="http://testserver")

    def test_load_create_page(self, client: TestClient):
        response = client.get("/admin/setting/create")
        assert response.status_code == 200

    def test_create(self, client: TestClient):
        response = client.post(
            "/admin/setting/create",
            data={
                "hosts.1": "http://www.example1.com",
                "hosts.2": "http://www.example2.com",
                "extras.1.key": "key1",
                "extras.1.value": "value1",
                "extras.2.key": "key2",
                "extras.2.value": "value2",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        stored = SettingView._get(1)
        assert len(stored.hosts) == 2
        assert str(stored.hosts[0]) == "http://www.example1.com"
        assert str(stored.hosts[1]) == "http://www.example2.com"
        assert stored.extras == [
            ExtraItem(key="key1", value="value1"),
            ExtraItem(key="key2", value="value2"),
        ]

    def test_load_edit_page(self, client: TestClient):
        SettingView._db.insert(
            Setting(
                hosts=["http://www.example1.com"],
                extras=[ExtraItem(key="k", value="v")],
            ).to_tinydb_doc()
        )
        response = client.get("/admin/setting/edit?pk=1")
        assert response.status_code == 200

    def test_edit(self, client: TestClient):
        SettingView._db.insert(
            Setting(
                hosts=["http://www.example1.com", "http://www.example2.com"],
                extras=[
                    ExtraItem(key="key1", value="value1"),
                    ExtraItem(key="key2", value="value2"),
                ],
            ).to_tinydb_doc()
        )
        response = client.post(
            "/admin/setting/edit?pk=1",
            data={
                "hosts.1": "http://www.example1.edit.com",
                "hosts.2": "http://www.example2.edit.com",
                "extras.1.key": "key1-edit",
                "extras.1.value": "value1-edit",
                "extras.2.key": "key2-edit",
                "extras.2.value": "value2-edit",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        stored = SettingView._get(1)
        assert len(stored.hosts) == 2
        assert str(stored.hosts[0]) == "http://www.example1.edit.com"
        assert stored.extras == [
            ExtraItem(key="key1-edit", value="value1-edit"),
            ExtraItem(key="key2-edit", value="value2-edit"),
        ]

    def test_detail_page_renders_list(self, client: TestClient):
        """List values are visible on the detail page (serialization check)."""
        SettingView._db.insert(
            Setting(
                hosts=["http://www.example1.com"],
                extras=[ExtraItem(key="key1", value="value1")],
            ).to_tinydb_doc()
        )
        response = client.get("/admin/setting/detail?pk=1")
        assert response.status_code == 200
        assert "example1.com" in response.text
        assert "key1" in response.text
