"""Integration tests for starlette_admin.contrib.tortoise.ModelView.

Exercises the full admin HTTP surface (list, search, sort, filters, create,
edit, delete, detail, relation-lookup) against a real in-memory SQLite
database, plus the view-level branches that the HTTP routes cannot reach.
"""

import datetime
import re
import uuid
from enum import IntEnum, StrEnum

import pytest
import pytest_asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.contrib.tortoise import Admin, ModelView
from starlette_admin.exceptions import FormValidationError
from starlette_admin.fields import StringField
from starlette_admin.filters import FilterGroup, FilterRule
from starlette_admin.types import RequestAction
from tortoise import Tortoise, fields
from tortoise.exceptions import ValidationError
from tortoise.models import Model

from tests.integration.tortoise.utils import reset_schema, tortoise_init
from tests.utils import csrf_async_client


class Brand(StrEnum):
    APPLE = "Apple"
    SAMSUNG = "Samsung"
    OPPO = "OPPO"
    HUAWEI = "Huawei"
    INFINIX = "Infinix"


class Status(IntEnum):
    DRAFT = 1
    ACTIVE = 2


class Product(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=100)
    description = fields.TextField(null=True)
    price = fields.FloatField(default=0)
    rating = fields.DecimalField(max_digits=5, decimal_places=2, null=True)
    brand = fields.CharEnumField(Brand, null=True)
    status = fields.IntEnumField(Status, default=Status.DRAFT)
    in_stock = fields.BooleanField(default=True)
    quantity = fields.IntField(default=0)
    release_date = fields.DateField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    launched_at = fields.DatetimeField(null=True)
    open_at = fields.TimeField(null=True)
    config = fields.JSONField(null=True)
    token = fields.UUIDField(default=uuid.uuid4)
    sku = fields.CharField(max_length=20, default="server-sku")


class Counter(Model):
    """A model with no searchable string field."""

    id = fields.IntField(primary_key=True)
    value = fields.IntField(default=0)


class ProductView(ModelView):
    fields = [
        "id",
        "title",
        "description",
        "price",
        "rating",
        "brand",
        "status",
        "in_stock",
        "quantity",
        "release_date",
        "created_at",
        "launched_at",
        "open_at",
        "config",
        "token",
        StringField("sku", read_only=True),
    ]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]


_SEED = [
    {
        "title": "IPhone 9",
        "description": "An apple mobile which is nothing like apple",
        "price": 549,
        "rating": "4.69",
        "brand": Brand.APPLE,
        "status": Status.ACTIVE,
        "in_stock": True,
        "quantity": 94,
        "release_date": datetime.date(2024, 3, 1),
        "launched_at": datetime.datetime(2024, 3, 1, 12, 0),
    },
    {
        "title": "IPhone X",
        "description": "SIM-Free, Model A19211",
        "price": 899,
        "rating": "4.44",
        "brand": Brand.APPLE,
        "status": Status.ACTIVE,
        "in_stock": True,
        "quantity": 34,
        "release_date": datetime.date(2024, 6, 1),
        "launched_at": datetime.datetime(2024, 6, 1, 18, 0),
    },
    {
        "title": "Samsung Universe 9",
        "description": "Samsung's new variant",
        "price": 1249,
        "rating": None,
        "brand": Brand.SAMSUNG,
        "status": Status.DRAFT,
        "in_stock": False,
        "quantity": 36,
        "release_date": None,
        "launched_at": None,
    },
    {
        "title": "OPPOF19",
        "description": "OPPO F19 is officially announced on April 2021.",
        "price": 280,
        "rating": "4.30",
        "brand": Brand.OPPO,
        "status": Status.DRAFT,
        "in_stock": True,
        "quantity": 123,
        "release_date": datetime.date(2030, 1, 1),
        "launched_at": datetime.datetime(2030, 1, 1, 0, 0),
    },
    {
        "title": "Huawei P30",
        "description": "Huawei's re-badged P30 Pro New Edition",
        "price": 499,
        "rating": "4.09",
        "brand": Brand.HUAWEI,
        "status": Status.ACTIVE,
        "in_stock": False,
        "quantity": 32,
        "release_date": datetime.date(2024, 3, 1),
        "launched_at": datetime.datetime(2024, 3, 1, 12, 0),
    },
]


def _list_total(html: str) -> int:
    m = re.search(r"Showing \d+ to \d+ of (\d+)", html)
    return int(m.group(1)) if m else 0


def _request(action: RequestAction = RequestAction.LIST) -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [],
            "query_string": b"",
        }
    )
    request.state.action = action
    return request


@pytest_asyncio.fixture()
async def admin(tortoise_backend):
    backend, db_url = tortoise_backend
    await tortoise_init(backend, db_url, __name__)
    await Tortoise.generate_schemas()
    for row in _SEED:
        await Product.create(**row)
    admin = Admin()
    admin.add_view(ProductView(Product))
    admin.add_view(ModelView(Counter))
    yield admin
    await reset_schema(backend)
    await Tortoise.close_connections()


@pytest_asyncio.fixture()
async def app(admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture()
async def client(app):
    async with csrf_async_client(app) as c:
        yield c


@pytest_asyncio.fixture()
async def product_view(admin):
    return admin._views[0]


class TestList:
    async def test_list(self, client):
        response = await client.get("/admin/product/list")
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    async def test_list_sort_desc(self, client):
        response = await client.get(
            "/admin/product/list", params={"sort": "title__desc"}
        )
        assert response.status_code == 200
        assert _list_total(response.text) == 5

    async def test_list_pagination(self, client):
        response = await client.get(
            "/admin/product/list", params={"page": 2, "page_size": 10}
        )
        assert response.status_code == 200

    async def test_list_fulltext(self, client):
        response = await client.get("/admin/product/list", params={"q": "iphone"})
        assert response.status_code == 200
        assert _list_total(response.text) == 2

    async def test_list_fulltext_no_match(self, client):
        response = await client.get("/admin/product/list", params={"q": "zzz"})
        assert response.status_code == 200
        assert _list_total(response.text) == 0

    async def test_fulltext_without_searchable_string_field_matches_all(self, client):
        """A model with no string-like searchable field yields an empty Q,
        so the search box filters nothing out.
        """
        await Counter.create(value=1)
        response = await client.get("/admin/counter/list", params={"q": "anything"})
        assert response.status_code == 200
        assert _list_total(response.text) == 1

    async def test_relation_lookup(self, client):
        response = await client.get("/admin/_api/product/relation-lookup")
        assert response.status_code == 200
        assert response.json()["total"] == 5

    async def test_relation_lookup_by_pks(self, client):
        products = await Product.filter(brand=Brand.APPLE)
        pks = [str(p.id) for p in products]
        response = await client.get(
            "/admin/_api/product/relation-lookup", params={"pks": pks}
        )
        assert response.status_code == 200
        assert response.json()["total"] == 2

    async def test_relation_lookup_invalid_pk_is_omitted(self, client):
        response = await client.get(
            "/admin/_api/product/relation-lookup", params={"pks": ["not-an-int"]}
        )
        assert response.status_code == 200
        assert response.json()["items"] == []


class TestFiltersThroughUrl:
    @pytest.mark.parametrize(
        "filter_str,expected",
        [
            ('title__contains="iphone"', 2),
            ('title__not_contains="iphone"', 3),
            ('title__startswith="ip"', 2),
            ('title__endswith="9"', 3),
            ('title__eq="iphone 9"', 1),
            ('title__neq="iphone 9"', 4),
            ("description__is_null", 0),
            ("description__is_not_null", 5),
            ("rating__is_null", 1),
            ("price__eq=549", 1),
            ("price__neq=549", 4),
            ("price__gt=549", 2),
            ("price__lt=549", 2),
            ("price__gte=549", 3),
            ("price__lte=549", 3),
            ("price__between=280..549", 3),
            ("in_stock__is_true", 3),
            ("in_stock__is_false", 2),
            ('brand__eq="Apple"', 2),
            ('brand__neq="Apple"', 3),
            ("brand__in=Apple,Samsung", 3),
            ("brand__not_in=Apple,Samsung", 2),
            ("status__in=2", 3),
            ("release_date__eq=2024-03-01", 2),
            ("release_date__between=2024-01-01..2024-12-31", 3),
            ("release_date__in_past", 3),
            ("release_date__in_future", 1),
            ("launched_at__between=2024-01-01T00:00:00..2024-12-31T23:59:59", 3),
            ("launched_at__in_past", 3),
            ("launched_at__in_future", 1),
            ("open_at__is_null", 5),
            ("open_at__is_not_null", 0),
            ('title__contains="iphone" AND price__gt=600', 1),
            ('(title__contains="iphone" OR title__contains="huawei")', 3),
        ],
    )
    async def test_filters(self, client, filter_str, expected):
        response = await client.get(
            "/admin/product/list", params={"filter": filter_str}
        )
        assert response.status_code == 200, response.text
        assert _list_total(response.text) == expected

    async def test_datetime_equal_filter(self, client, product_view):
        request = _request()
        group = FilterGroup(
            rules=[
                FilterRule(
                    field="launched_at",
                    filter="eq",
                    value=datetime.datetime(2024, 3, 1, 12, 0),
                )
            ]
        )
        assert await product_view.count(request, filters=group) == 2

    async def test_unknown_filter_yields_no_filtering(self, client, product_view):
        """A rule whose slug has no registered filter is skipped, leaving the
        whole group empty ("no filtering").
        """
        request = _request()
        group = FilterGroup(
            rules=[FilterRule(field="title", filter="unknown_op", value="x")]
        )
        assert await product_view.count(request, filters=group) == 5


class TestCrud:
    async def test_detail(self, client):
        product = await Product.filter(title="IPhone 9").first()
        response = await client.get(f"/admin/product/detail?pk={product.id}")
        assert response.status_code == 200
        assert "IPhone 9" in response.text

    async def test_detail_invalid_pk(self, client):
        response = await client.get("/admin/product/detail?pk=not-an-int")
        assert response.status_code == 404

    async def test_detail_unknown_pk(self, client):
        response = await client.get("/admin/product/detail?pk=999999")
        assert response.status_code == 404

    async def test_create(self, client):
        response = await client.post(
            "/admin/product/create",
            data={
                "title": "Infinix INBOOK",
                "description": "Infinix Inbook X1",
                "price": 1049,
                "rating": "4.5",
                "brand": "Infinix",
                "status": "1",
                "in_stock": "on",
                "quantity": 5,
                "release_date": "2025-01-01",
                "launched_at": "2025-01-01T10:00:00",
                "token": str(uuid.uuid4()),
                "config": '{"color": "grey"}',
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert await Product.all().count() == 6
        product = await Product.get(title="Infinix INBOOK")
        assert product.brand == Brand.INFINIX
        assert product.status == Status.DRAFT
        assert product.config == {"color": "grey"}
        assert product.created_at is not None

    async def test_create_validation_error(self, client):
        response = await client.post(
            "/admin/product/create",
            data={
                "title": "x" * 300,
                "price": 10,
                "status": "1",
                "quantity": 1,
                "token": str(uuid.uuid4()),
            },
        )
        assert response.status_code == 422
        assert await Product.all().count() == 5

    async def test_create_ignores_read_only_field(self, client):
        response = await client.post(
            "/admin/product/create",
            data={
                "title": "Read only test",
                "price": 10,
                "status": "1",
                "quantity": 1,
                "token": str(uuid.uuid4()),
                "sku": "hacked-sku",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        product = await Product.get(title="Read only test")
        assert product.sku == "server-sku"

    async def test_edit(self, client):
        product = await Product.filter(title="IPhone 9").first()
        response = await client.post(
            f"/admin/product/edit?pk={product.id}",
            data={
                "title": "IPhone 9 Pro",
                "description": "Updated",
                "price": 599,
                "rating": "4.8",
                "brand": "Apple",
                "status": "2",
                "quantity": 90,
                "release_date": "2024-03-02",
                "launched_at": "2024-03-02T12:00:00",
                "token": str(product.token),
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        updated = await Product.get(pk=product.id)
        assert updated.title == "IPhone 9 Pro"
        assert updated.in_stock is False  # unchecked checkbox
        assert updated.created_at == product.created_at  # excluded from edit

    async def test_edit_validation_error(self, client):
        product = await Product.filter(title="IPhone 9").first()
        response = await client.post(
            f"/admin/product/edit?pk={product.id}",
            data={
                "title": "x" * 300,
                "price": 10,
                "status": "1",
                "quantity": 1,
                "token": str(product.token),
            },
        )
        assert response.status_code == 422
        assert (await Product.get(pk=product.id)).title == "IPhone 9"

    async def test_delete(self, client):
        pks = [
            str(p.id)
            for p in await Product.filter(title__in=["IPhone 9", "Huawei P30"])
        ]
        response = await client.post(
            "/admin/_api/product/action",
            params={"name": "delete", "pks": pks},
        )
        assert response.status_code == 200
        assert await Product.all().count() == 3

    async def test_delete_skips_unknown_pk(self, client, product_view):
        request = _request()
        assert await product_view.delete(request, [999999]) == 0


class TestViewDirect:
    """View-level branches the HTTP routes cannot reach."""

    async def test_find_all_unlimited(self, client, product_view):
        request = _request()
        rows = await product_view.find_all(request, skip=0, limit=-1)
        assert len(rows) == 5

    async def test_find_all_skip_with_limit(self, client, product_view):
        request = _request()
        rows = await product_view.find_all(
            request, skip=2, limit=2, sorts=[("title", "asc")]
        )
        assert [r.title for r in rows] == ["IPhone X", "OPPOF19"]

    async def test_find_by_pks_skips_invalid(self, client, product_view):
        request = _request()
        product = await Product.filter(title="IPhone 9").first()
        rows = await product_view.find_by_pks(request, [product.id, "not-an-int"])
        assert [r.id for r in rows] == [product.id]

    async def test_serialized_pk_value(self, client, product_view):
        request = _request()
        product = await Product.filter(title="IPhone 9").first()
        assert (
            await product_view.get_serialized_pk_value(request, product) == product.id
        )

    async def test_handle_exception_unparseable_validation_error(
        self, client, product_view
    ):
        with pytest.raises(ValidationError):
            await product_view.handle_exception(
                _request(), ValidationError("no field prefix here")
            )

    async def test_handle_exception_validation_error_unknown_field(
        self, client, product_view
    ):
        with pytest.raises(ValidationError):
            await product_view.handle_exception(
                _request(), ValidationError("nofield: message")
            )

    async def test_handle_exception_validation_error_known_field(
        self, client, product_view
    ):
        with pytest.raises(FormValidationError) as exc_info:
            await product_view.handle_exception(
                _request(), ValidationError("title: too long")
            )
        assert exc_info.value.errors == {"title": "too long"}

    async def test_handle_exception_other_error_is_reraised(self, client, product_view):
        with pytest.raises(RuntimeError):
            await product_view.handle_exception(_request(), RuntimeError("boom"))
