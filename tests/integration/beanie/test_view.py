import datetime
import json
import os
import re
from enum import StrEnum
from typing import Annotated, Any

import pymongo
import pytest
import pytest_asyncio
from beanie import Document, Indexed, Link, init_beanie
from beanie.operators import In
from pydantic import Field, SecretStr
from pymongo import AsyncMongoClient, IndexModel
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.contrib.beanie import Admin, ModelView
from starlette_admin.fields import StringField, TagsField

from tests.utils import csrf_async_client

MONGO_DATABASE = os.environ.get("MONGO_DATABASE", "testdb")


class Brand(StrEnum):
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
    sku: str = "server-sku"


class AnotherSameProduct(Document):
    title: Annotated[str, Indexed(unique=True)] = Field(min_length=3)
    description: str
    price: float = Field(ge=0)
    brand: Brand
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)
    dummy_tag: list[str] = Field(default_factory=list)


class Store(Document):
    name: str = Field(min_length=3)
    products: list[Link[Product]] = []


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
    before_create_count = 0
    after_create_count = 0
    before_delete_count = 0
    after_delete_count = 0
    before_edit_count = 0
    after_edit_count = 0

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        self.before_create_count += 1

    async def after_create(self, request: Request, obj: Any) -> None:
        self.after_create_count -= 1

    async def before_delete(self, request: Request, obj: Any) -> None:
        self.before_delete_count += 1

    async def after_delete(self, request: Request, obj: Any) -> None:
        self.after_delete_count -= 1

    async def before_edit(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        self.before_edit_count += 1

    async def after_edit(self, request: Request, obj: Any) -> None:
        self.after_edit_count -= 1


def _list_total(html: str) -> int:
    m = re.search(r"Showing \d+ to \d+ of (\d+)", html)
    return int(m.group(1)) if m else 0


class TestBeanieView:
    @pytest_asyncio.fixture(loop_scope="function")
    async def admin(self, mongo_url):
        self.mongo_client = AsyncMongoClient(host=mongo_url)
        await self.mongo_client.drop_database(MONGO_DATABASE)
        await init_beanie(
            database=self.mongo_client.get_database(MONGO_DATABASE),
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
            fields = [
                "id",
                "title",
                "description",
                "price",
                "brand",
                "created_at",
                StringField("sku", read_only=True),
            ]
            exclude_fields_from_create = [Product.created_at]
            exclude_fields_from_edit = ["created_at"]

        self.product_test_view = ProductDescriptionTestView(ProductDescriptionTest)

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
        admin.add_view(self.product_test_view)
        admin.add_view(ModelView(StoreLoginConfig))
        admin.add_view(CustomizedProductView(AnotherSameProduct))

        yield admin

        await self.mongo_client.drop_database(MONGO_DATABASE)
        await self.mongo_client.close()

    @pytest_asyncio.fixture(loop_scope="function")
    async def app(self, admin):
        app = Starlette()
        admin.mount_to(app)
        return app

    @pytest_asyncio.fixture(loop_scope="function")
    async def client(self, app):
        async with csrf_async_client(app) as c:
            yield c

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_list(self, client, product_path):
        response = await client.get(f"/admin/{product_path}/list")
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_list_sort(self, client, product_path):
        response = await client.get(
            f"/admin/{product_path}/list", params={"sort": "title__desc"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 5
        # Samsung Universe 9 sorts last alphabetically when descending
        assert "Samsung Universe 9" in response.text

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_list_fulltext(self, client, product_path):
        response = await client.get(
            f"/admin/{product_path}/list", params={"q": "IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    @pytest.mark.parametrize("product_path", ["product", "another-same-product"])
    async def test_list_select2(self, client, product_path):
        response = await client.get(f"/admin/_api/{product_path}/relation-lookup")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5

    async def test_select2_by_pks(self, client):
        docs = await Product.find(
            {"title": {"$in": ["IPhone 9", "Samsung Universe 9"]}}
        ).to_list()
        pks = [str(d.id) for d in docs]
        response = await client.get(
            "/admin/_api/product/relation-lookup", params={"pks": pks}
        )
        assert response.status_code == 200
        data = response.json()
        # when pks are given, total == len(items) (not full collection count)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        titles = {item["title"] for item in data["items"]}
        assert titles == {"IPhone 9", "Samsung Universe 9"}

    async def test_select2_by_pks_unknown_pk(self, client):
        # an unknown pk is silently omitted from results
        from bson import ObjectId

        fake_pk = str(ObjectId())
        response = await client.get(
            "/admin/_api/product/relation-lookup", params={"pks": [fake_pk]}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_detail(
        self, client, document: Product | AnotherSameProduct, product_path: str
    ):
        doc = await document.find(document.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.get(f"/admin/{product_path}/detail?pk={id}")
        assert response.status_code == 200
        assert str(id) in response.text
        response = await client.get(f"/admin/{product_path}/detail?pk=invalid_id")
        assert response.status_code == 404

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_create(
        self, client, document: Product | AnotherSameProduct, product_path: str
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
        self, client, document: Product | AnotherSameProduct, product_path: str
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
        self, client, document: Product | AnotherSameProduct, product_path: str
    ):
        doc = await document.find(document.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/{product_path}/edit?pk={id}",
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
        self, client, document: Product | AnotherSameProduct, product_path: str
    ):
        doc = await document.find(Product.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/{product_path}/edit?pk={id}",
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
        self, client, document: Product | AnotherSameProduct, product_path: str
    ):
        doc = await document.find(document.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/{product_path}/edit?pk={id}",
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

    async def test_create_ignores_read_only_field(self, client):
        response = await client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                # sku is read-only: a submitted value must be ignored in favor
                # of the model default.
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        product = await Product.find(Product.title == "Infinix INBOOK").first_or_none()
        assert product is not None
        assert product.sku == "server-sku"

    async def test_edit_ignores_read_only_field(self, client):
        doc = await Product.find(Product.title == "IPhone 9").first_or_none()
        id = doc.id
        response = await client.post(
            f"/admin/product/edit?pk={id}",
            data={
                "title": "Infinix INBOOK",
                "description": (
                    "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year"
                    " Warranty"
                ),
                "price": 1049,
                "brand": "Infinix",
                # sku is read-only: attempting to change it via the edit form
                # must have no effect.
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        product = await Product.get(id)
        assert product.title == "Infinix INBOOK"
        assert product.sku == "server-sku"

    @pytest.mark.parametrize(
        "document,product_path",
        [(Product, "product"), (AnotherSameProduct, "another-same-product")],
    )
    async def test_delete(
        self, client, document: Product | AnotherSameProduct, product_path: str
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
            f"/admin/_api/{product_path}/action",
            params={"name": "delete", "pks": ids},
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
            f"/admin/another-same-product/edit?pk={id}",
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

        response = await client.get(
            "/admin/product-description-test/list", params={"q": "version 9"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1
        assert "IPhone version 9" in response.text

    async def test_create_hooks(self, client):
        # add store
        store = Store(name="Store 1")
        await store.save()

        product = ProductDescriptionTest(
            description="IPhone version 9. this is a very good phone",
            store=store,
        ).model_dump(mode="json")
        product["store"] = store.id
        assert self.product_test_view.before_create_count == 0
        assert self.product_test_view.after_create_count == 0
        response = await client.post(
            "/admin/product-description-test/create",
            data=product,
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert self.product_test_view.before_create_count == 1
        assert self.product_test_view.after_create_count == -1

    async def test_delete_hooks(self, client):
        store = Store(name="Store 1")
        await store.save()

        product = await ProductDescriptionTest(
            description="IPhone version 9. this is a very good phone",
            store=store,
        ).save()
        assert self.product_test_view.before_delete_count == 0
        assert self.product_test_view.after_delete_count == 0

        response = await client.post(
            "/admin/_api/product-description-test/action",
            params={"name": "delete", "pks": [product.id]},
        )
        assert response.status_code == 200

        assert self.product_test_view.before_delete_count == 1
        assert self.product_test_view.after_delete_count == -1

    async def test_edit_hooks(self, client):
        store = Store(name="Store 1")
        await store.save()

        product = await ProductDescriptionTest(
            description="IPhone version 9. this is a very good phone",
            store=store,
        ).save()

        assert self.product_test_view.before_edit_count == 0
        assert self.product_test_view.after_edit_count == 0

        response = await client.post(
            f"/admin/product-description-test/edit?pk={product.id}",
            data={"description": "Pinephone Pro", "store": store.id},
            follow_redirects=True,
        )

        assert response.status_code == 200

        assert self.product_test_view.before_edit_count == 1
        assert self.product_test_view.after_edit_count == -1

        await product.sync()

        assert product.description == "Pinephone Pro"

    async def test_unsearchable_document(self, client):
        store = Store(name="Store 1")
        await store.save()

        store_login_config = StoreLoginConfig(
            password=SecretStr("password"),
            hostname=SecretStr("hostname"),
            store=store,
        )
        await store_login_config.save()

        response = await client.get(
            "/admin/store-login-config/list", params={"q": "banana"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1  # no filtering on unsearchable fields

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

    async def test_exception_raised_from_handle_exception(self):
        with pytest.raises(Exception, match="Boom"):
            await ModelView(Product).handle_exception(None, Exception("Boom"))

    async def test_expression_field_normalization(self):

        class ProductViewExpr(ModelView):
            searchable_fields = [Product.title, Product.description]
            sortable_fields = [Product.title, "price"]
            fields_default_sort = [Product.title, (Product.price, True)]

        view = ProductViewExpr(Product)
        assert view.searchable_fields == ["title", "description"]
        assert view.sortable_fields == ["title", "price"]
        assert view.fields_default_sort == ["title", ("price", True)]


class TestBeanieFilters:
    """Filter system integration tests for the Beanie backend.

    Filter strings use the ``field__op=value`` shorthand parsed by
    ``BaseModelView._parse_filter_string``; see the MongoEngine counterpart in
    ``tests/integration/mongoengine/test_view.py::TestMongoFilters`` for the
    full syntax reference.
    """

    @pytest_asyncio.fixture(loop_scope="function")
    async def admin(self, mongo_url):
        mongo_client = AsyncMongoClient(host=mongo_url)
        await mongo_client.drop_database(MONGO_DATABASE)
        await init_beanie(
            database=mongo_client.get_database(MONGO_DATABASE),
            document_models=[Product],
        )
        past = datetime.datetime(2024, 1, 1)
        with open("./tests/data/products.json") as f:
            for product in json.load(f):
                await Product(**product, created_at=past).save()

        admin = Admin()
        admin.add_view(ModelView(Product))
        yield admin

        await mongo_client.drop_database(MONGO_DATABASE)
        await mongo_client.close()

    @pytest_asyncio.fixture(loop_scope="function")
    async def app(self, admin):
        app = Starlette()
        admin.mount_to(app)
        return app

    @pytest_asyncio.fixture(loop_scope="function")
    async def client(self, app):
        async with csrf_async_client(app) as c:
            yield c

    async def test_filter_string_contains(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": "title__contains=IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_string_not_contains(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": "title__not_contains=IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    async def test_filter_string_startswith(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": "title__startswith=IPhone"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_string_endswith(self, client):
        # "IPhone 9", "Samsung Universe 9", "OPPOF19" all end with "9"
        response = await client.get(
            "/admin/product/list", params={"filter": "title__endswith=9"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    async def test_filter_string_eq(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": 'title__eq="IPhone 9"'}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_filter_string_neq(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": 'title__neq="IPhone 9"'}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 4

    async def test_filter_numeric_gt(self, client):
        # price > 500: IPhone 9 (549), IPhone X (899), Samsung Universe 9 (1249)
        response = await client.get(
            "/admin/product/list", params={"filter": "price__gt=500"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    async def test_filter_numeric_lt(self, client):
        # price < 500: OPPOF19 (280), Huawei P30 (499)
        response = await client.get(
            "/admin/product/list", params={"filter": "price__lt=500"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_numeric_gte(self, client):
        # price >= 549: IPhone 9 (549), IPhone X (899), Samsung Universe 9 (1249)
        response = await client.get(
            "/admin/product/list", params={"filter": "price__gte=549"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    async def test_filter_numeric_lte(self, client):
        # price <= 499: OPPOF19 (280), Huawei P30 (499)
        response = await client.get(
            "/admin/product/list", params={"filter": "price__lte=499"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_numeric_between(self, client):
        # 500 <= price <= 900: IPhone 9 (549), IPhone X (899)
        response = await client.get(
            "/admin/product/list", params={"filter": "price__between=500..900"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_numeric_eq(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": "price__eq=549"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_filter_null_checks(self, client):
        # description is set for all test products, so none are null
        response = await client.get(
            "/admin/product/list", params={"filter": "description__is_null"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 0

        response = await client.get(
            "/admin/product/list", params={"filter": "description__is_not_null"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    async def test_filter_enum_eq(self, client):
        # Apple products: IPhone 9, IPhone X
        response = await client.get(
            "/admin/product/list", params={"filter": "brand__eq=Apple"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_enum_in(self, client):
        # Apple + Samsung: 3 products
        response = await client.get(
            "/admin/product/list", params={"filter": "brand__in=Apple,Samsung"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 3

    async def test_filter_enum_not_in(self, client):
        # Not Apple, not Samsung: OPPO + Huawei = 2
        response = await client.get(
            "/admin/product/list", params={"filter": "brand__not_in=Apple,Samsung"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_or_group(self, client):
        # brand == OPPO OR price > 1000: OPPOF19 + Samsung Universe 9
        response = await client.get(
            "/admin/product/list",
            params={"filter": "brand__eq=OPPO OR price__gt=1000"},
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_and_group(self, client):
        # brand == Apple AND price > 600: only IPhone X (899)
        response = await client.get(
            "/admin/product/list",
            params={"filter": "brand__eq=Apple AND price__gt=600"},
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_filter_combined_with_fulltext_search(self, client):
        # q=IPhone (regex on title/description) + brand=Apple → 2 Apple iPhones
        response = await client.get(
            "/admin/product/list",
            params={"q": "IPhone", "filter": "brand__eq=Apple"},
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_nested_groups(self, client):
        # (brand == Apple AND price > 600) OR brand == Samsung
        # → IPhone X (Apple, 899) + Samsung Universe 9
        response = await client.get(
            "/admin/product/list",
            params={
                "filter": "(brand__eq=Apple AND price__gt=600) OR brand__eq=Samsung"
            },
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_filter_datetime_in_past(self, client):
        # All products have created_at = 2024-01-01 (past)
        response = await client.get(
            "/admin/product/list", params={"filter": "created_at__in_past"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    async def test_filter_datetime_in_future(self, client):
        response = await client.get(
            "/admin/product/list", params={"filter": "created_at__in_future"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 0

    async def test_filter_objectid_eq(self, client):
        doc = await Product.find(Product.title == "IPhone 9").first_or_none()
        target_id = str(doc.id)
        response = await client.get(
            "/admin/product/list", params={"filter": f"id__eq={target_id}"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_filter_objectid_in(self, client):
        docs = await Product.find(
            {"title": {"$in": ["IPhone 9", "Huawei P30"]}}
        ).to_list()
        ids = ",".join(str(d.id) for d in docs)
        response = await client.get(
            "/admin/product/list", params={"filter": f"id__in={ids}"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 2
