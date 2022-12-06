import json

import pytest
import pytest_asyncio
from httpx import AsyncClient
from odmantic import Model, Reference, SyncEngine
from starlette.applications import Starlette
from starlette_admin.contrib.odmantic import Admin, ModelView

pytestmark = pytest.mark.asyncio


class Author(Model):
    name: str


class Quote(Model):
    quote: str
    author: Author = Reference()


@pytest.fixture()
def prepare_database(sync_engine: SyncEngine):
    sync_engine.remove(Author)
    sync_engine.remove(Quote)
    sync_engine.save_all(
        [
            Quote(
                quote="Strive not to be a success, but rather to be of value.",
                author=Author(name="Albert Einstein"),
            ),
            Quote(
                quote="Your time is limited, so don’t waste it living someone else’s life.",
                author=Author(name="Steve Jobs"),
            ),
            Quote(
                quote="Either you run the day, or the day runs you.",
                author=Author(name="Jim Rohn"),
            ),
        ]
    )


@pytest_asyncio.fixture
async def client(prepare_database, sync_engine: SyncEngine):
    admin = Admin(sync_engine)
    app = Starlette()
    admin.add_view(ModelView(Author))
    admin.add_view(ModelView(Quote))
    admin.mount_to(app)
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


async def test_api(client: AsyncClient):
    response = await client.get("/admin/api/author?skip=1&limit=2&order_by=name desc")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert ["Jim Rohn", "Albert Einstein"] == [x["name"] for x in data["items"]]
    # Find by pks
    response = await client.get(
        "/admin/api/author", params={"pks": [x["id"] for x in data["items"]]}
    )
    assert {"Jim Rohn", "Albert Einstein"} == {
        x["name"] for x in response.json()["items"]
    }


async def test_deep_search(client: AsyncClient, sync_engine: SyncEngine):
    where = {
        "or": [
            {"name": {"startswith": "Albert"}},
            {"name": {"contains": "Rohn"}},
        ]
    }
    response = await client.get(
        "/admin/api/author", params={"where": json.dumps(where), "order_by": "name asc"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert data["items"][0]["name"] == "Albert Einstein"
    assert data["items"][1]["name"] == "Jim Rohn"


async def test_detail(client: AsyncClient, sync_engine: SyncEngine):
    quote = sync_engine.find_one(Quote)
    response = await client.get(f"/admin/quote/detail/{quote.id}")
    assert response.status_code == 200
    assert quote.quote in response.text


async def test_create(client: AsyncClient, sync_engine: SyncEngine):
    kevin = sync_engine.save(Author(name="Kevin Kruse"))
    response = await client.post(
        "/admin/quote/create",
        data={
            "quote": "Life isn’t about getting and having, it’s about giving and being.",
            "author": kevin.id,
        },
    )
    assert response.status_code == 303
    quote = sync_engine.find_one(Quote, Quote.quote.match(r"^Life isn’t"))
    assert (
        quote.quote
        == "Life isn’t about getting and having, it’s about giving and being."
    )
    assert quote.author.name == "Kevin Kruse"


async def test_edit(client: AsyncClient, sync_engine: SyncEngine):
    kevin = sync_engine.save(Author(name="Kevin Kruse"))
    quote = sync_engine.find_one(Quote, Quote.quote.match(r"^Strive not"))
    response = await client.post(
        f"/admin/quote/edit/{quote.id}",
        data={
            "quote": "Life isn’t about getting and having, it’s about giving and being.",
            "author": kevin.id,
        },
    )
    assert response.status_code == 303
    assert sync_engine.find_one(Quote, Quote.quote.match(r"^Strive not")) is None
    quote = sync_engine.find_one(Quote, Quote.quote.match(r"^Life isn’t"))
    assert (
        quote.quote
        == "Life isn’t about getting and having, it’s about giving and being."
    )
    assert quote.author.name == "Kevin Kruse"


async def test_delete(client: AsyncClient, sync_engine: SyncEngine):
    authors = sync_engine.find(Author, Author.name.in_(["Jim Rohn", "Albert Einstein"]))
    response = await client.post(
        "/admin/api/author/action",
        params={"name": "delete", "pks": [a.id for a in authors]},
    )
    assert response.status_code == 200
    assert (
        len(
            list(
                sync_engine.find(
                    Author, Author.name.in_(["Jim Rohn", "Albert Einstein"])
                )
            )
        )
        == 0
    )
