import json
import tempfile
from typing import Optional

import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from httpx import AsyncClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.contrib.beanie._file import File

from tests.beanie import MONGO_DATABASE

pytestmark = pytest.mark.asyncio


class Post(Document):
    name: str
    file: Optional[File] = None


@pytest_asyncio.fixture
async def client(cli, db, fs):
    await init_beanie(
        database=cli[MONGO_DATABASE],
        document_models=[Post],
    )  # type: ignore

    # prepare database
    await Post.delete_all()
    posts = [
        Post(name="post1"),
        Post(name="post2"),
    ]
    await Post.insert_many(posts)

    admin = Admin(fs=fs)
    app = Starlette()
    admin.add_view(ModelView(Post))
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
        "/admin/api/post?skip=0&limit=10&where=&order_by=name asc"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2
    assert ["post1", "post2"] == [x["name"] for x in data["items"]]


async def test_create(client: AsyncClient):
    response = await client.post(
        "/admin/post/create",
        data={
            "name": "post3",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert await Post.find_one(Post.name == "post3") is not None


@pytest.fixture
def fake_file_content():
    return b"Hello World"


@pytest.fixture
def fake_file(fake_file_content):
    file = tempfile.NamedTemporaryFile(suffix=".txt")
    file.write(fake_file_content)
    file.seek(0)
    return file


async def test_create_with_file(client: AsyncClient, fake_file, fake_file_content):
    response = await client.post(
        "/admin/post/create",
        data={
            "name": "post4",
        },
        files={"file": ("file.txt", fake_file, "text/plain")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert await Post.find_one(Post.name == "post4") is not None

    # test Serve file Api
    where = {
        "and": [
            {
                "name": {
                    "eq": "post4",
                }
            }
        ],
    }
    where_json = json.dumps(where)
    response = await client.get(f"/admin/api/post?where={where_json}")
    url = response.json()["items"][0]["file"]["url"]
    response = await client.get(url)
    assert response.status_code == 200


async def test_serve_api_file_fail(client: AsyncClient, fake_file, fake_file_content):
    response = await client.post(
        "/admin/post/create",
        data={
            "name": "post5",
        },
        files={"file": ("file.txt", fake_file, "text/plain")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert await Post.find_one(Post.name == "post5") is not None

    # test Serve file Api
    where = {
        "and": [
            {
                "name": {
                    "eq": "post5",
                }
            }
        ],
    }
    where_json = json.dumps(where)
    response = await client.get(f"/admin/api/post?where={where_json}")
    url = response.json()["items"][0]["file"]["url"]
    # add to url 'xyz' to get error
    url = url + "xyz"
    response = await client.get(url)
    assert response.status_code == 404  # not found!
