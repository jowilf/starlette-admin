import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.contrib.beanie._password import Password

from tests.beanie import MONGO_DATABASE

pytestmark = pytest.mark.asyncio


class User(Document):
    name: str
    password: Password


@pytest_asyncio.fixture
async def client(cli, db, fs):
    await init_beanie(
        database=cli[MONGO_DATABASE],
        document_models=[User],
    )  # type: ignore

    # prepare database
    await User.delete_all()
    users = [
        User(name="Pedro", password="12345678#$"),
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
    skip = 0
    limit = 10
    order = by name
    """
    response = await client.get(
        "/admin/api/user?skip=0&limit=10&where=&order_by=name asc"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert ["Pedro"] == [x["name"] for x in data["items"]]


async def test_password_mask(client: AsyncClient):
    response = await client.get("/admin/api/user?skip=0&limit=10&where=Pedr")
    assert response.status_code == 200
    data = response.json()
    print(data)
    assert data["total"] == 1
    assert ["Pedro"] == [x["name"] for x in data["items"]]
    assert data["items"][0]["password"] == "***"


# async def test_detail(client: AsyncClient):

#     assert "Pedro" in response.text
#     assert "pedro@gmail.com" in response.text


# async def test_create(client: AsyncClient):
#         "/admin/user/create",
#         },
#     assert users[0].dict(exclude={"id"}) == {


# async def test_edit(client: AsyncClient):

#         },

#     assert usuario.dict() == {


# async def test_delete(client: AsyncClient):

#         "/admin/api/user/action",
