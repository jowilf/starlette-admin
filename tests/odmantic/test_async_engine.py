import json
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import pytest
import pytest_asyncio
from httpx import AsyncClient
from odmantic import AIOEngine, EmbeddedModel, Field, Model
from requests import Request
from starlette.applications import Starlette
from starlette_admin.contrib.odmantic import Admin, ModelView

if sys.version_info < (3, 9):
    pytest.skip(
        "Skipping the test due to a segment fault error with odmantic on Python 3.8, and the library is not "
        "currently maintained",
        allow_module_level=True,
    )

pytestmark = pytest.mark.asyncio


class Address(EmbeddedModel):
    city: str = Field(min_length=5)
    state: str


class Hobby(EmbeddedModel):
    name: str = Field(max_length=10)
    reason: str


class User(Model):
    name: str = Field(min_length=3)
    address: Address
    hobbies: List[Hobby]
    birthday: Optional[datetime]


class UserView(ModelView):
    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, User)
        assert obj.id is not None

    async def after_create(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, User)
        assert obj.id is not None

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, User)
        assert obj.id is not None

    async def after_edit(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, User)
        assert obj.id is not None

    async def before_delete(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, User)
        assert obj.id is not None

    async def after_delete(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, User)
        assert obj.id is not None


@pytest_asyncio.fixture()
async def prepare_database(aio_engine: AIOEngine):
    await aio_engine.remove(User)
    await aio_engine.save_all(
        [
            User(
                name="Terry Medhurst",
                address=Address(city="Washington", state="DC"),
                hobbies=[],
                birthday=datetime(2000, 12, 10),
            ),
            User(
                name="Sheldon Cole",
                address=Address(city="Louisville", state="KY"),
                hobbies=[],
                birthday=datetime(2014, 1, 16),
            ),
            User(
                name="Hills Terrill",
                address=Address(city="Grass Valley", state="CA"),
                hobbies=[],
                birthday=datetime(2007, 11, 6),
            ),
        ]
    )


@pytest_asyncio.fixture
async def client(prepare_database, aio_engine: AIOEngine):
    admin = Admin(aio_engine)
    app = Starlette()
    admin.add_view(UserView(User))
    admin.mount_to(app)
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


async def test_api(client: AsyncClient):
    response = await client.get(
        "/admin/api/user?skip=1&limit=2&where={}&order_by=name asc"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert ["Sheldon Cole", "Terry Medhurst"] == [x["name"] for x in data["items"]]
    # Find by pks
    response = await client.get(
        "/admin/api/user", params={"pks": [x["id"] for x in data["items"]]}
    )
    assert {"Sheldon Cole", "Terry Medhurst"} == {
        x["name"] for x in response.json()["items"]
    }


async def test_full_text_search(client: AsyncClient):
    response = await client.get("/admin/api/user?where=Terr&order_by=name asc")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert ["Hills Terrill", "Terry Medhurst"] == [x["name"] for x in data["items"]]


async def test_deep_search(client: AsyncClient, aio_engine: AIOEngine):
    id = (await aio_engine.find_one(User, User.name == "Hills Terrill")).id
    where = {
        "and": [
            {"id": {"neq": str(id)}},
            {"birthday": {"between": ["1999-01-01T00:00:00", "2010-01-01T00:00:00"]}},
        ]
    }
    response = await client.get("/admin/api/user", params={"where": json.dumps(where)})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["name"] == "Terry Medhurst"


async def test_detail(client: AsyncClient, aio_engine: AIOEngine):
    id = (await aio_engine.find_one(User, User.name == "Hills Terrill")).id
    response = await client.get(f"/admin/user/detail/{id}")
    assert response.status_code == 200
    assert str(id) in response.text


async def test_create(client: AsyncClient, aio_engine: AIOEngine):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "John Doe",
            "birthday": "1999-01-01T00:00:00",
            "address.city": "Nashville",
            "address.state": "TN",
            "hobbies.1.name": "sports",
            "hobbies.1.reason": "good health",
            "hobbies.2.name": "music",
            "hobbies.2.reason": "concentration :)",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    users = await aio_engine.find(User, User.name == "John Doe")
    assert len(users) == 1
    assert users[0].dict(exclude={"id"}) == {
        "name": "John Doe",
        "birthday": datetime(1999, 1, 1),
        "address": {
            "city": "Nashville",
            "state": "TN",
        },
        "hobbies": [
            {
                "name": "sports",
                "reason": "good health",
            },
            {
                "name": "music",
                "reason": "concentration :)",
            },
        ],
    }


async def test_create_validation_error(client: AsyncClient, aio_engine: AIOEngine):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "Jo",
            "birthday": "1999-01-01T00:00:00",
            "address.city": "Nash",
            "address.state": "TN",
            "hobbies.1.name": "sports",
            "hobbies.1.reason": "good health",
            "hobbies.2.name": "music,danse,all",
            "hobbies.2.reason": "concentration :)",
        },
        follow_redirects=False,
    )
    assert response.text.count('class="invalid-feedback">') == 3
    assert response.text.count("ensure this value has at least 3 characters") == 1
    assert response.text.count("ensure this value has at least 5 characters") == 1
    assert response.text.count("ensure this value has at most 10 characters") == 1
    assert response.status_code == 422
    assert (await aio_engine.find_one(User, User.name == "Jo")) is None


async def test_edit(client: AsyncClient, aio_engine: AIOEngine):
    id = (await aio_engine.find_one(User, User.name == "Hills Terrill")).id
    response = await client.post(
        f"/admin/user/edit/{id}",
        data={
            "name": "John Doe",
            "birthday": "1999-01-01T00:00:00",
            "address.city": "Nashville",
            "address.state": "TN",
            "hobbies.1.name": "sports",
            "hobbies.1.reason": "good health",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    users = await aio_engine.find(User, User.id == id)
    assert len(users) == 1
    assert users[0] == {
        "id": id,
        "name": "John Doe",
        "birthday": datetime(1999, 1, 1),
        "address": {
            "city": "Nashville",
            "state": "TN",
        },
        "hobbies": [
            {
                "name": "sports",
                "reason": "good health",
            },
        ],
    }


async def test_edit_validation_error(client: AsyncClient, aio_engine: AIOEngine):
    id = (await aio_engine.find_one(User, User.name == "Hills Terrill")).id
    response = await client.post(
        f"/admin/user/edit/{id}",
        data={
            "name": "Jo",
            "birthday": "1999-01-01T00:00:00",
            "address.city": "Nash",
            "address.state": "TN",
            "hobbies.1.name": "sports",
            "hobbies.1.reason": "good health",
            "hobbies.2.name": "music,danse,all",
            "hobbies.2.reason": "concentration :)",
        },
        follow_redirects=False,
    )
    assert response.text.count('class="invalid-feedback">') == 3
    assert response.text.count("ensure this value has at least 3 characters") == 1
    assert response.text.count("ensure this value has at least 5 characters") == 1
    assert response.text.count("ensure this value has at most 10 characters") == 1
    assert response.status_code == 422
    assert (await aio_engine.find_one(User, User.name == "Hills Terrill")) is not None
    assert (await aio_engine.find_one(User, User.name == "Jo")) is None


async def test_delete(client: AsyncClient, aio_engine: AIOEngine):
    users = await aio_engine.find(
        User, User.name.in_(["Hills Terrill", "Sheldon Cole"])
    )
    response = await client.post(
        "/admin/api/user/action",
        params={"name": "delete", "pks": [u.id for u in users]},
    )
    assert response.status_code == 200
    assert (
        len(
            await aio_engine.find(
                User, User.name.in_(["Hills Terrill", "Sheldon Cole"])
            )
        )
        == 0
    )
