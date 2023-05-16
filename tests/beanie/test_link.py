from typing import List

import pytest
import pytest_asyncio
from beanie import Document, Link, init_beanie
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView

from tests.beanie import MONGO_DATABASE

pytestmark = pytest.mark.asyncio


# has one
class Owner(Document):
    name: str


# has many
class Window(Document):
    x: int = 10
    y: int = 10


class House(Document):
    name: str
    windows: List[Link[Window]]
    owner: Link[Owner]


@pytest_asyncio.fixture
async def client(cli, db, fs):
    await init_beanie(
        database=cli[MONGO_DATABASE],
        document_models=[Owner, Window, House],
    )  # type: ignore

    # prepare database
    await Owner.delete_all()
    await House.delete_all()
    await Window.delete_all()

    owner = Owner(name="Peter")
    await Owner.insert_one(owner)
    ow = await Owner.find_many(Owner.name == "Peter").to_list()

    windows = [
        Window(x=100, y=100),
        Window(x=200, y=200),
    ]
    await Window.insert_many(windows)
    ws = await Window.find_all().to_list()
    ids = []
    for x in ws:
        ids.append(x.id)

    houses = [House(name="Home", windows=ids, owner=ow[0].id)]
    await House.insert_many(houses)

    admin = Admin(fs=fs)
    app = Starlette()
    admin.add_view(ModelView(Window))
    admin.add_view(ModelView(House))
    admin.mount_to(app)
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


# async def test_relations(client):
#     pass


async def test_relations(client):
    ow = await Owner.find_many(Owner.name == "Peter").to_list()
    owner_id = ow[0].id

    ws = await Window.find_all().to_list()
    ids = []
    for x in ws:
        ids.append(x.id)

    response = await client.post(
        "/admin/house/create",
        data={"name": "Oscar's House", "windows": ids, "owner": owner_id},
        follow_redirects=False,
    )
    assert response.status_code == 303
    house = await House.find(House.name == "Oscar's House", fetch_links=True).to_list()
    assert len(house[0].windows) == 2
    assert house[0].owner.name == "Peter"
