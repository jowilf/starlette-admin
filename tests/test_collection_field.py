from dataclasses import dataclass
from typing import Optional

import pytest
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    CollectionField,
    IntegerField,
    PasswordField,
    StringField,
)

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class DBConfig(BaseModel):
    host: str
    username: str
    password: Optional[str]


@dataclass()
class Config(DummyBaseModel):
    db: DBConfig
    nested: Optional[dict]


class ConfigView(DummyModelView):
    model = Config
    fields = (
        IntegerField("id"),
        CollectionField(
            "db",
            fields=[
                StringField("host"),
                StringField("username"),
                PasswordField("password"),
            ],
        ),
        CollectionField(
            "nested",
            fields=[
                StringField("level1"),
                CollectionField("other", fields=[StringField("level2")]),
            ],
        ),
    )
    # exclude_fields_from_list = ("nested.other.level2",)


class TestCollectionField:
    @pytest.fixture
    def client(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(ConfigView)
        admin.mount_to(app)
        return TestClient(app, base_url="http://testserver")

    @pytest.fixture
    def all(self):
        return (
            "id",
            "db.host",
            "db.username",
            "db.password",
            "nested.level1",
            "nested.other.level2",
        )

    def test_view_default_values(self, all):
        config_view = ConfigView()
        assert (
            tuple(config_view.searchable_fields)
            == tuple(config_view.sortable_fields)
            == tuple(config_view.export_fields)
            == all
        )

    def test_form_ids(self, all, client):
        response = client.get("/admin/config/create")
        assert response.status_code == 200
        for value in all:
            if value != "id":
                assert response.text.count(f'name="{value}"') == 1

    def test_create(self, all, client):
        response = client.post(
            "/admin/config/create",
            data={
                "db.host": "localhost",
                "db.username": "username",
                "db.password": "password",
                "nested.level1": "dummy1",
                "nested.other.level2": "dummy2",
            },
            follow_redirects=False
        )
        assert response.status_code == 303
        assert ConfigView.db[1] == Config(
            id=1,
            db=DBConfig(host="localhost", username="username", password="password"),
            nested={"level1": "dummy1", "other": {"level2": "dummy2"}},
        )

    def test_api(self, client):
        ConfigView.db[1] = Config(
            id=1,
            db=DBConfig(host="localhost", username="username", password="password"),
            nested={"level1": "dummy1", "other": {"level2": "dummy2"}},
        )
        ConfigView.db[2] = Config(
            id=2,
            db=DBConfig(host="localhost2", username="username2", password="password2"),
            nested={"level1": "dummy1", "other": None},
        )
        response = client.get("/admin/api/config", params={"pks": [1, 2]})
        assert response.status_code == 200
        assert response.json()["items"][0]["db"] == DBConfig(
            host="localhost", username="username", password="password"
        )
        assert response.json()["items"][0]["nested"] == {
            "level1": "dummy1",
            "other": {"level2": "dummy2"},
        }
        assert response.json()["items"][1]["db"] == DBConfig(
            host="localhost2", username="username2", password="password2"
        )
        assert response.json()["items"][1]["nested"] == {
            "level1": "dummy1",
            "other": None,
        }

    def test_edit(self, client):
        ConfigView.db[1] = Config(
            id=1,
            db=DBConfig(host="localhost", username="username", password="password"),
            nested={"level1": "dummy1", "other": {"level2": "dummy2"}},
        )
        response = client.post(
            "/admin/config/edit/1",
            data={
                "db.host": "localhost:3306",
                "db.username": "dbuser",
                "db.password": "dbpass",
                "nested.level1": "dummy11",
                "nested.other.level2": "dummy22",
            },
            follow_redirects=False
        )
        assert response.status_code == 303
        assert ConfigView.db[1] == Config(
            id=1,
            db=DBConfig(host="localhost:3306", username="dbuser", password="dbpass"),
            nested={"level1": "dummy11", "other": {"level2": "dummy22"}},
        )
