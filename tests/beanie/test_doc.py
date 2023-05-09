import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from beanie.operators import In
from bson import ObjectId
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView

from tests.beanie import MONGO_DATABASE

pytestmark = pytest.mark.asyncio


class User(Document):
    name: str
    lastname: str


@pytest_asyncio.fixture
async def client(cli, db, fs):
    await init_beanie(
        database=cli[MONGO_DATABASE],
        document_models=[User],
    )  # type: ignore

    # prepare database
    await User.delete_all()
    users = [
        User(name="Pedro", lastname="Garcia"),
        User(name="Pedrito", lastname="Moreno"),
        User(name="Juan", lastname="Perez"),
        User(name="Carlos", lastname="Tevez"),
    ]
    await User.insert_many(users)

    admin = Admin(fs=fs)
    app = Starlette()
    admin.add_view(ModelView(User))
    admin.mount_to(app)
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


async def test_api(client: AsyncClient):
    """
    skip = 1
    limit = 2
    order = by name
    """
    response = await client.get(
        "/admin/api/user?skip=1&limit=2&where=&order_by=name asc"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4
    assert len(data["items"]) == 2  # limit!
    assert ["Juan", "Pedrito"] == [x["name"] for x in data["items"]]


async def test_full_text_search(client: AsyncClient):
    response = await client.get("/admin/api/user?skip=0&limit=10&where=Pedr")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert ["Pedro", "Pedrito"] == [x["name"] for x in data["items"]]


async def test_detail(client: AsyncClient):
    user = await User.find(User.name == "Pedro").first_or_none()

    response = await client.get(f"/admin/user/detail/{user.id}")
    assert response.status_code == 200
    assert "Pedro" in response.text
    assert "Garcia" in response.text


async def test_create(client: AsyncClient):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "John",
            "lastname": "Doe",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    users = await User.find(User.name == "John").to_list()
    assert len(users) == 1
    assert users[0].dict(exclude={"id"}) == {
        "name": "John",
        "lastname": "Doe",
    }


async def test_edit(client: AsyncClient):
    user = await User.find(User.name == "Pedro").first_or_none()

    response = await client.post(
        f"/admin/user/edit/{user.id}",
        data={
            "name": "Pedro",
            "lastname": "Marmol",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    usuario = await User.get(user.id)

    assert usuario.dict() == {
        "id": ObjectId(user.id),
        "name": "Pedro",
        "lastname": "Marmol",
    }


async def test_delete(client: AsyncClient):
    users = await User.find(In(User.name, ["Juan", "Carlos"])).to_list()

    response = await client.post(
        "/admin/api/user/action",
        params={"name": "delete", "pks": [u.id for u in users]},
    )
    assert response.status_code == 200
    assert len(await User.find(In(User.name, ["Juan", "Carlos"])).to_list()) == 0
