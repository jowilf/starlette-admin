"""Tests for CollectionField (nested pydantic models in create/edit forms).

Rewritten for pydantic v2 (the original skipped on v2). The removed
/admin/_api/{key}?pks= endpoint is replaced with a detail-page
serialization check.
"""

import pytest
from pydantic import BaseModel
from starlette.applications import Starlette
from starlette_admin import (
    BaseAdmin,
    CollectionField,
    IntegerField,
    PasswordField,
    StringField,
)

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class DBConfig(BaseModel):
    host: str = ""
    username: str = ""
    password: str | None = None


class Config(TinydbBaseModel):
    db: DBConfig = DBConfig()
    nested: dict | None = None


class ConfigView(TinydbModelView):
    fields = [
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
                CollectionField(
                    "other", fields=[StringField("level2"), StringField("excluded")]
                ),
            ],
        ),
    ]
    exclude_fields_from_create = ("nested.other.excluded",)
    exclude_fields_from_edit = ("nested.other.excluded",)


class TestCollectionField:
    @pytest.fixture(autouse=True)
    def reset_db(self):
        ConfigView._db.truncate()

    @pytest.fixture
    def client(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(ConfigView(Config))
        admin.mount_to(app)
        return CsrfTestClient(app, base_url="http://testserver")

    @pytest.fixture
    def all_fields(self):
        return (
            "id",
            "db.host",
            "db.username",
            "db.password",
            "nested.level1",
            "nested.other.level2",
            "nested.other.excluded",
        )

    def test_view_default_values(self, all_fields):
        config_view = ConfigView(Config)
        assert (
            tuple(config_view.searchable_fields)
            == tuple(config_view.sortable_fields)
            == all_fields
        )

    def test_form_ids(self, all_fields, client):
        response = client.get("/admin/config/create")
        assert response.status_code == 200
        for value in all_fields:
            if value not in ["id", "nested.other.excluded"]:
                assert response.text.count(f'name="{value}"') == 1
            else:
                assert response.text.count(f'name="{value}"') == 0

    def test_create(self, all_fields, client):
        response = client.post(
            "/admin/config/create",
            data={
                "db.host": "localhost",
                "db.username": "username",
                "db.password": "password",
                "nested.level1": "dummy1",
                "nested.other.level2": "dummy2",
                "nested.other.excluded": "will be ignored",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        stored = ConfigView._get(1)
        assert stored.db == DBConfig(
            host="localhost", username="username", password="password"
        )
        assert stored.nested == {"level1": "dummy1", "other": {"level2": "dummy2"}}

    def test_field_serialization(self, client):
        """Detail page renders nested CollectionField values correctly."""
        ConfigView._db.insert(
            Config(
                db=DBConfig(host="localhost", username="username", password="password"),
                nested={
                    "level1": "dummy1",
                    "other": {"level2": "dummy2", "excluded": "dummy3"},
                },
            ).to_tinydb_doc()
        )
        ConfigView._db.insert(
            Config(
                db=DBConfig(
                    host="localhost2", username="username2", password="password2"
                ),
                nested={"level1": "dummy1", "other": None},
            ).to_tinydb_doc()
        )
        response = client.get("/admin/config/detail?pk=1")
        assert response.status_code == 200
        assert "localhost" in response.text
        assert "dummy1" in response.text
        assert "dummy2" in response.text

        response = client.get("/admin/config/detail?pk=2")
        assert response.status_code == 200
        assert "localhost2" in response.text

    def test_edit(self, client):
        ConfigView._db.insert(
            Config(
                db=DBConfig(host="localhost", username="username", password="password"),
                nested={"level1": "dummy1", "other": {"level2": "dummy2"}},
            ).to_tinydb_doc()
        )
        response = client.post(
            "/admin/config/edit?pk=1",
            data={
                "db.host": "localhost:3306",
                "db.username": "dbuser",
                "db.password": "dbpass",
                "nested.level1": "dummy11",
                "nested.other.level2": "dummy22",
                "nested.other.excluded": "will be ignored",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        stored = ConfigView._get(1)
        assert stored.db == DBConfig(
            host="localhost:3306", username="dbuser", password="dbpass"
        )
        assert stored.nested == {"level1": "dummy11", "other": {"level2": "dummy22"}}
