from typing import List

import pytest
from pydantic import BaseModel, Field, HttpUrl
from starlette.applications import Starlette
from starlette.testclient import TestClient

from starlette_admin import BaseAdmin, CollectionField, ListField, StringField, URLField, IntegerField
from tests.dummy_model_view import DummyBaseModel, DummyModelView


class ExtraItem(BaseModel):
    key: str
    value: str


class Setting(DummyBaseModel):
    hosts: List[HttpUrl] = Field(default_factory=list)
    extras: List[ExtraItem] = Field(default_factory=list)


class SettingView(DummyModelView):
    model = Setting
    fields = (
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
    )


class TestListField:
    @pytest.fixture
    def client(self) -> TestClient:
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(SettingView)
        admin.mount_to(app)
        return TestClient(app, base_url="http://testserver")

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
        assert SettingView.db[1] == Setting(
            id=1,
            hosts=[
                HttpUrl("http://www.example1.com", scheme="http"),
                HttpUrl("http://www.example2.com", scheme="http"),
            ],
            extras=[
                ExtraItem(key="key1", value="value1"),
                ExtraItem(key="key2", value="value2"),
            ],
        )

    def test_api(self, client: TestClient):
        SettingView.db[1] = Setting(
            id=1,
            hosts=[
                HttpUrl("http://www.example1.com", scheme="http"),
                HttpUrl("http://www.example2.com", scheme="http"),
            ],
            extras=[
                ExtraItem(key="key1", value="value1"),
                ExtraItem(key="key2", value="value2"),
            ],
        )
        response = client.get("/admin/api/setting", params={"pks": [1]})
        assert Setting(**response.json()["items"][0]) == SettingView.db[1]

    def test_load_edit_page(self, client):
        response = client.get("/admin/setting/edit/1")
        assert response.status_code == 200

    def test_edit(self, client: TestClient):
        SettingView.db[1] = Setting(
            id=1,
            hosts=[
                HttpUrl("http://www.example1.com", scheme="http"),
                HttpUrl("http://www.example2.com", scheme="http"),
            ],
            extras=[
                ExtraItem(key="key1", value="value1"),
                ExtraItem(key="key2", value="value2"),
            ],
        )
        response = client.post(
            "/admin/setting/edit/1",
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
        assert SettingView.db[1] == Setting(
            id=1,
            hosts=[
                HttpUrl("http://www.example1.edit.com", scheme="http"),
                HttpUrl("http://www.example2.edit.com", scheme="http"),
            ],
            extras=[
                ExtraItem(key="key1-edit", value="value1-edit"),
                ExtraItem(key="key2-edit", value="value2-edit"),
            ],
        )
