import base64
import json
import tempfile
from typing import Optional

import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.contrib.beanie._file import Image

from tests.beanie import MONGO_DATABASE

pytestmark = pytest.mark.asyncio


class User(Document):
    name: str
    avatar: Optional[Image] = None


@pytest_asyncio.fixture
async def client(cli, db, fs):
    await init_beanie(
        database=cli[MONGO_DATABASE],
        document_models=[User],
    )  # type: ignore

    # prepare database
    await User.delete_all()
    users = [
        User(name="Pedro"),
        User(name="Juan"),
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
    assert data["total"] == 2
    assert len(data["items"]) == 2  # limit!
    assert ["Juan", "Pedro"] == [x["name"] for x in data["items"]]


async def test_create(client: AsyncClient):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "admin",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert await User.find_one(User.name == "admin") is not None


@pytest.fixture
def fake_image_content():
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAAAXNSR0IArs4c6QAAAHNJREFUKFOdkLEKwCAMRM/JwUFwdPb"
        "/v8RPEDcdBQcHJyUt0hQ6hGY6Li8XEhVjXM45aK3xVXNOtNagcs6LRAgB1toX23tHSgkUpEopyxhzGRw"
        "+EHljjBv03oM3KJYP1lofkJoHJs3T/4Gi1aJjxO+RPnwDur2EF1gNZukAAAAASUVORK5CYII="
    )


@pytest.fixture
def fake_image(fake_image_content):
    file = tempfile.NamedTemporaryFile(suffix=".png")
    file.write(fake_image_content)
    file.seek(0)
    return file


async def test_create_with_image(client: AsyncClient, fake_image, fake_image_content):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "admin",
        },
        files={"avatar": ("image.png", fake_image, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert await User.find_one(User.name == "admin") is not None

    # test Serve file Api
    where = {
        "and": [
            {
                "name": {
                    "eq": "admin",
                }
            }
        ],
    }
    where_json = json.dumps(where)
    response = await client.get(f"/admin/api/user?where={where_json}")
    url = response.json()["items"][0]["avatar"]["url"]
    response = await client.get(url)
    assert response.status_code == 200


async def test_serve_api_image_fail(
    client: AsyncClient, fake_image, fake_image_content
):
    response = await client.post(
        "/admin/user/create",
        data={
            "name": "admin",
        },
        files={"avatar": ("image.png", fake_image, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert await User.find_one(User.name == "admin") is not None

    # test Serve file Api
    where = {
        "and": [
            {
                "name": {
                    "eq": "admin",
                }
            }
        ],
    }
    where_json = json.dumps(where)
    response = await client.get(f"/admin/api/user?where={where_json}")
    url = response.json()["items"][0]["avatar"]["url"]
    # add to url 'xyz' to get error
    url = url + "xyz"
    response = await client.get(url)
    assert response.status_code == 404  # not found!
