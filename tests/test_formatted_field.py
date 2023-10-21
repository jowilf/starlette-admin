import datetime

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin import (
    BaseAdmin,
    DateField,
    FormattedField,
    IntegerField,
    StringField,
)

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Person(DummyBaseModel):
    first_name: str
    last_name: str
    date_of_birth: datetime.date


class PersonView(DummyModelView):
    model = Person
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
        DateField("date_of_birth"),
        FormattedField(
            "full_name",
            label="Full Name",
            func=lambda request, obj: f"{obj.first_name} {obj.last_name}",
        ),
        FormattedField(
            "age",
            label="Age",
            func=lambda request, obj: (datetime.date.today() - obj.date_of_birth).days
            // 365,
        ),
    ]


class TestFormattedField:
    @pytest.fixture
    def client(self) -> TestClient:
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PersonView)
        admin.mount_to(app)
        return TestClient(app, base_url="http://testserver")

    def test_load_create_page(self, client: TestClient):
        response = client.get("/admin/person/create")
        assert response.status_code == 200

    def test_create(self, client: TestClient):
        response = client.post(
            "/admin/person/create",
            data={
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": datetime.date(1990, 1, 1),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert PersonView.db[1] == Person(
            id=1,
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1),
        )

    def test_api(self, client: TestClient):
        PersonView.db[1] = Person(
            id=1,
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1),
        )
        response = client.get("/admin/api/person", params={"pks": [1]})
        assert response.json()["total"] == 1
        item = response.json()["items"][0]
        assert item["id"] == 1
        assert item["full_name"] == "John Doe"
        assert (
            int(item["age"])
            == (datetime.date.today() - datetime.date(1990, 1, 1)).days // 365
        )

    def test_load_edit_page(self, client):
        response = client.get("/admin/person/edit/1")
        assert response.status_code == 200

    def test_edit(self, client: TestClient):
        PersonView.db[1] = Person(
            id=1,
            first_name="John",
            last_name="Doe",
            date_of_birth=datetime.date(1990, 1, 1),
        )
        response = client.post(
            "/admin/person/edit/1",
            data={
                "first_name": "John-edit",
                "last_name": "Doe-edit",
                "date_of_birth": "1990-01-02",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert PersonView.db[1] == Person(
            id=1,
            first_name="John-edit",
            last_name="Doe-edit",
            date_of_birth=datetime.date(1990, 1, 2),
        )
