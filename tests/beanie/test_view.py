import datetime
import json
import os
from enum import Enum
from typing import Annotated, List, Union

import pymongo
import pytest
import pytest_asyncio
from beanie import Document, Indexed, Link, init_beanie
from beanie.operators import In
from httpx import ASGITransport, AsyncClient
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import Field, SecretStr
from pymongo import IndexModel
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.fields import TagsField

from tests.beanie import MONGO_URL

MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "testdb")


class Brand(str, Enum):
    APPLE = "Apple"
    SAMSUNG = "Samsung"
    OPPO = "OPPO"
    HUAWEI = "Huawei"
    INFINIX = "Infinix"


class Product(Document):
    title: Annotated[str, Indexed(unique=True)] = Field(min_length=3)
    description: str
    price: float = Field(ge=0)
    brand: Brand
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)


class AnotherSameProduct(Document):
    title: Annotated[str, Indexed(unique=True)] = Field(min_length=3)
    description: str
    price: float = Field(ge=0)
    brand: Brand
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    dummy_tag: List[str] = Field(default_factory=list)


class Store(Document):
    name: str = Field(min_length=3)
    products: List[Link[Product]] = []


class User(Document):
    name: str = Field(min_length=3)
    store: Link[Store]


class ProductDescriptionTest(Document):
    description: str
    store: Link[Store]

    class Settings:
        indexes = [
            IndexModel([("description", pymongo.TEXT)]),
        ]


class StoreLoginConfig(Document):
    password: SecretStr
    hostname: SecretStr
    store: Link[Store]


class ProductDescriptionTestView(ModelView):
    full_text_override_order_by = True


class TestBeanieView:

    @pytest_asyncio.fixture(loop_scope="function")
    async def admin(self):
        self.motor_client = AsyncIOMotorClient(host=MONGO_URL)
        await self.motor_client.drop_database(MONGO_DATABASE)
        await init_beanie(
            database=self.motor_client.get_database(MONGO_DATABASE),
            document_models=[
                Product,
                Store,
                User,
                ProductDescriptionTest,
                StoreLoginConfig,
                AnotherSameProduct,
            ],
        )
        with open("./tests/data/products.json") as f:
            for product in json.load(f):
                await Product(**product).save()
                await AnotherSameProduct(**product).save()

        class ProductView(ModelView):
            exclude_fields_from_create = [Product.created_at]
            exclude_fields_from_edit = ["created_at"]

        class StoreView(ModelView):
            exclude_fields_from_list = ["id"]

        class CustomizedProductView(ModelView):
            fields = [
                "id",
                Product.title,
                "description",
                "price",
                "brand",
                "created_at",
                TagsField("dummy_tag", label="Dummy Tag"),
                TagsField("field_not_in_model", label="Field not in Model"),
            ]
            exclude_fields_from_create = [Product.created_at]
            exclude_fields_from_edit = ["created_at"]
            exclude_fields_from_list = [Product.id]

        admin = Admin()
        admin.add_view(StoreView(Store))
        admin.add_view(ProductView(Product))
        admin.add_view(ModelView(User))
        admin.add_view(ProductDescriptionTestView(ProductDescriptionTest))
        admin.add_view(ModelView(StoreLoginConfig))
        admin.add_view(CustomizedProductView(AnotherSameProduct))

        yield admin

        await self.motor_client.drop_database(MONGO_DATABASE)
        self.motor_client.close()

    @pytest_asyncio.fixture(loop_scope="function")
    async def app(self, admin):
        app = Starlette()
        admin.mount_to(app)
        return app

    @pytest_asyncio.fixture(loop_scope="function")
    async def client(self, app):
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as c:
            yield c

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_api(self, client, product_path):
        response = await client.get(
            f"/admin/api/{product_path}?skip=1&where={{}}&limit=2&order_by=title desc"
        )
        data = response.json()
        assert data["total"] == 5
        assert len(data["items"]) == 2
        assert [x["title"] for x in data["items"]] == ["OPPOF19", "IPhone X"]
        # Find by pks
        response = await client.get(
            f"/admin/api/{product_path}",
            params={"pks": [x["id"] for x in data["items"]]},
        )
        assert {"IPhone X", "OPPOF19"} == {x["title"] for x in response.json()["items"]}

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_api_fulltext(self, client, product_path):
        response = await client.get(
            f"/admin/api/{product_path}?where=IPhone&order_by=price asc"
        )
        data = response.json()
        assert data["total"] == 2
        assert [x["title"] for x in data["items"]] == ["IPhone 9", "IPhone X"]

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_api_query1(self, client, product_path):
        where = (
            '{"or": [{"title": {"eq": "IPhone 9"}}, {"price": {"between": [200,'
            " 500]}}]}"
        )
        response = await client.get(
            f"/admin/api/{product_path}?where={where}&order_by=price asc"
        )
        data = response.json()
        assert data["total"] == 3
        assert [x["title"] for x in data["items"]] == [
            "OPPOF19",
            "Huawei P30",
            "IPhone 9",
        ]

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_api_query2(self, client, product_path):
        where = (
            '{"and": [{"brand": {"eq": "Apple"}}, {"price": {"not_between": [500,'
            " 600]}}]}"
        )
        response = await client.get(f"/admin/api/{product_path}?where={where}")
        data = response.json()
        assert data["total"] == 1
        assert [x["title"] for x in data["items"]] == ["IPhone X"]

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_api_query3(self, client, product_path):
        response = await client.get(
            f"/admin/api/{product_path}?order_by=price desc&limit=2"
        )
        data = response.json()
        assert data["total"] == 5
        assert [x["title"] for x in data["items"]] == ["Samsung Universe 9", "IPhone X"]

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_detail(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        doc = await document.find(document.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.get(f"/admin/{product_path}/detail/{id}")
        assert response.status_code == 200
        assert str(id) in response.text
        response = await client.get(f"/admin/{product_path}/detail/invalid_id")
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_create(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        response = await client.post(
            f"/admin/{product_path}/create",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (await document.count()) == 6
        assert (
            await document.find(document.title == "Infinix INBOOK").first_or_none()
        ) is not None

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_create_validation_error(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        response = await client.post(
            f"/admin/{product_path}/create",
            data={
                "title": "In",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
        )
        assert response.status_code == 422
        assert "String should have" in response.text
        assert (await document.count()) == 5

        product = await document.find(document.brand == "Infinix").first_or_none()
        assert product is None

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_edit(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        doc = await document.find(document.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/{product_path}/edit/{id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (await document.count()) == 5
        assert (await document.get(id)).title == "Infinix INBOOK"
        assert (
            await document.find(Product.title == "IPhone 9").first_or_none()
        ) is None

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_edit_validation_error(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        doc = await document.find(Product.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/{product_path}/edit/{id}",
            data={
                "title": "In",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
            },
        )
        assert response.status_code == 422
        assert "String should have" in response.text
        assert (await document.count()) == 5
        assert (await document.find(Product.brand == "Infinix").first_or_none()) is None

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_edit_excluded_field(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        doc = await document.find(document.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/{product_path}/edit/{id}",
            data={
                "title": "IPhone 9",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                "created_at": "2023-01-01T00:00:00Z",
            },
        )
        assert response.status_code == 303
        assert (await document.count()) == 5
        # get the product again
        doc2 = await document.find(document.title == "IPhone 9").first_or_none()

        assert doc2.created_at == doc.created_at

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_delete(
        self, client, document: Union[Product, AnotherSameProduct], product_path: str
    ):
        ids = [
            str(x.id)
            for x in (
                await document.find(
                    In(document.title, ["IPhone 9", "Huawei P30", "OPPOF19"])
                ).to_list()
            )
        ]
        response = await client.post(
            f"/admin/api/{product_path}/action", params={"name": "delete", "pks": ids}
        )
        assert response.status_code == 200
        assert (
            await document.find(
                In(document.title, ["IPhone 9", "Huawei P30", "OPPOF19"])
            ).count()
        ) == 0

    async def test_edit_explicitly_defined_field(self, client):
        doc = await AnotherSameProduct.find(
            AnotherSameProduct.title == "IPhone 9"
        ).first_or_none()
        assert doc is not None
        id = doc.id
        response = await client.post(
            f"/admin/another-same-product/edit/{id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                "dummy_tag": ["test-tag-1"],
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (await AnotherSameProduct.count()) == 5

        await doc.sync()
        assert doc.dummy_tag == ["test-tag-1"]

    async def test_full_text_index(self, client):

        # add store
        store = Store(name="Store 1")
        await store.save()

        # add product with description
        product = ProductDescriptionTest(
            description="IPhone version 9. this is a very good phone",
            store=store,
        )
        product2 = ProductDescriptionTest(
            description="IPhone X this is a very good phone",
            store=store,
        )
        await product.save()
        await product2.save()

        # search by description
        response = await client.get(
            "/admin/api/product-description-test?where=version%209"
        )
        data = response.json()
        assert data["total"] == 1
        assert [x["description"] for x in data["items"]] == [
            "IPhone version 9. this is a very good phone"
        ]

    async def test_unsearchable_document(self, client):
        # add store
        store = Store(name="Store 1")
        await store.save()

        # add StoreLoginConfig
        store_login_config = StoreLoginConfig(
            password=SecretStr("password"),
            hostname=SecretStr("hostname"),
            store=store,
        )

        await store_login_config.save()

        # try to search by password
        response = await client.get("/admin/api/store-login-config?where=banana")

        data = response.json()
        assert data["total"] == 1  # no filtering done here

    async def test_init_modelview_invalid_field(self):

        class BadProductModelView(ModelView):
            exclude_fields_from_detail = [1]

        with pytest.raises(ValueError):
            BadProductModelView(Product)

    async def test_invalid_explicit_modelview_field(self):

        class BadProductModelView(ModelView):
            fields = ["non-existent-field"]

        with pytest.raises(ValueError):
            BadProductModelView(Product)
