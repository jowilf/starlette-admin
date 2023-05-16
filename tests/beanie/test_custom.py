from enum import Enum
from typing import Optional

import pytest
import pytest_asyncio
from beanie import Document, init_beanie
from httpx import AsyncClient
from pydantic import BaseModel, Field
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.contrib.beanie._slug import Slug

from tests.beanie import MONGO_DATABASE

pytestmark = pytest.mark.asyncio


class Country(str, Enum):
    Argentina = "Argentina"
    USA = "USA"


class Info(BaseModel):
    key: str
    value: int


class Address(Document):
    street: str = Field(..., max_length=10, description="Street Name")
    number: int
    country: Country
    info: Info
    slug: Optional[Slug]


class CustomView(ModelView):
    exclude_fields_from_list = ["id", "revision_id"]
    exclude_fields_from_detail = ["id", "revision_id"]
    exclude_fields_from_create = ["id", "revision_id", "created_at", "updated_at"]
    exclude_fields_from_edit = ["id", "revision_id", "created_at", "updated_at"]


@pytest_asyncio.fixture
async def client(cli, db, fs):
    await init_beanie(
        database=cli[MONGO_DATABASE],
        document_models=[Address],
    )  # type: ignore

    # prepare database
    await Address.delete_all()

    admin = Admin(fs=fs)
    app = Starlette()
    admin.add_view(CustomView(Address))
    admin.mount_to(app)
    async with AsyncClient(app=app, base_url="http://testserver") as c:
        yield c


async def test_create(client: AsyncClient):
    response = await client.post(
        "/admin/address/create",
        data={
            "street": "5th avenue",
            "number": 12345,
            "country": "USA",
            "info.key": "distance",
            "info.value": 1000,
            "slug": "it is a slug",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    address = await Address.find(Address.street == "5th avenue").to_list()
    assert address[0].country == Country.USA
    assert address[0].info.value == 1000


# async def test_api(client: AsyncClient):
#     """
#     order = by name
#     """


# async def test_full_text_search(client: AsyncClient):


# async def test_detail(client: AsyncClient):

#     assert "Pedro" in response.text
#     assert "pedro@gmail.com" in response.text


# async def test_edit(client: AsyncClient):

#         },

#     assert usuario.dict() == {


# async def test_delete(client: AsyncClient):

#         "/admin/api/user/action",
