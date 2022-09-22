from dataclasses import dataclass
from typing import TypedDict

import pytest
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


class DBConfig(TypedDict):
    host: str
    username: str
    password: str


@dataclass
class Config(DummyBaseModel):
    db: DBConfig
    nested: dict


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

    def test_crud(self, all):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(ConfigView)
        admin.mount_to(app)
        client = TestClient(app)

        response = client.get("/admin/config/create")
        assert response.status_code == 200
        for value in all:
            if value != "id":
                assert response.text.count(f'name="{value}"') == 1

        response = client.post(
            "/admin/config/create",
            data={
                "db.host": "localhost",
                "db.username": "username",
                "db.password": "password",
                "nested.level1": "dummy1",
                "nested.other.level2": "dummy2",
            },
        )
        assert response.status_code == 303
        assert ConfigView.db[1] == Config(
            id=1,
            db=DBConfig(host="localhost", username="username", password="password"),
            nested={"level1": "dummy1", "other": {"level2": "dummy2"}},
        )
