"""Merged sync / async SQLAlchemy engine tests.

The ``engine`` fixture is parametrized as ``["sync", "async"]`` and
``sqla_backend`` is parametrized as ``["sqlite", "mysql", "postgres"]``. Every test runs six times (3 database backends x 2 engine types).

A thin ``_SyncToAsync`` adapter wraps the sync ``sqlalchemy.orm.Session`` so
that all test functions can use the same ``await session.*`` call sites
regardless of the underlying engine.  Storage is selected per database backend:
SQLite uses MinIO; MySQL and PostgreSQL use a temporary local directory.
"""

import enum
import json
import os
from typing import Any

import pytest
import sqlalchemy_file as sf
from httpx2 import AsyncClient
from sqlalchemy import (
    Boolean,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    Session,
    mapped_column,
    relationship,
    selectinload,
)
from sqlalchemy_file.storage import StorageManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import StringField
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.integration.sqla.utils import get_async_test_engine, get_test_engine
from tests.utils import csrf_async_client, has_invalid_feedback


class Base(DeclarativeBase):
    pass


# Models


class Brand(enum.StrEnum):
    APPLE = "Apple"
    SAMSUNG = "Samsung"
    OPPO = "OPPO"
    HUAWEI = "Huawei"
    INFINIX = "Infinix"


class Product(Base):
    __tablename__ = "product"
    id: Mapped[int] = mapped_column("Product / ID", Integer, primary_key=True)
    title: Mapped[str] = mapped_column("Product / Title", String(100))
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[float | None] = mapped_column(Float)
    brand: Mapped[Brand | None] = mapped_column(Enum(Brand))
    in_stock: Mapped[bool | None] = mapped_column(Boolean)
    sku: Mapped[str | None] = mapped_column(String(50), default="server-sku")
    image = mapped_column(sf.ImageField(thumbnail_size=(128, 128)))
    user_name: Mapped[str | None] = mapped_column(String(100), ForeignKey("user.name"))
    user: Mapped["User"] = relationship("User", back_populates="products")


class User(Base):
    __tablename__ = "user"
    name: Mapped[str] = mapped_column(String(100), primary_key=True)
    files = mapped_column(sf.FileField(multiple=True))
    products: Mapped[list["Product"]] = relationship("Product", back_populates="user")
    # reproduces https://github.com/jowilf/starlette-admin/issues/507
    product_titles = association_proxy("products", "titles")


# Views


class ProductView(ModelView):
    fields = [
        "id",
        "title",
        "description",
        "price",
        "brand",
        "in_stock",
        "image",
        "user",
        StringField("sku", read_only=True),
    ]
    sortable_fields = ["id", "title", "price", "user"]
    sortable_field_mapping = {"user": User.name}
    searchable_fields = ["id", "title", "price", "description", "user", "in_stock"]

    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, Product)
        assert obj.id is None

    async def after_create(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def before_edit(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def after_edit(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def before_delete(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def after_delete(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None


class UserView(ModelView):
    show_pk_in_forms = True
    searchable_fields = ["name", "products"]


# Sync-to-async session adapter


class _SyncToAsync:
    """Wraps a sync ``sqlalchemy.orm.Session`` behind an async interface.

    Allows test functions to use ``await session.execute(...)`` and
    ``await session.get(...)`` uniformly across both the sync and async
    parametrize legs without duplicating test code.
    """

    def __init__(self, session: Session) -> None:
        self._s = session

    def add(self, obj: Any) -> None:
        self._s.add(obj)

    async def commit(self) -> None:
        self._s.commit()

    async def execute(self, stmt: Any) -> Any:
        return self._s.execute(stmt)

    async def get(self, model: type, pk: Any) -> Any:
        return self._s.get(model, pk)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _seed(session_or_async_session, fake_image) -> None:
    """Sync seed helper (called inside both sync and async setup paths)."""
    with open("./tests/data/products.json") as f:
        products = [Product(**p) for p in json.load(f)]
    products[0].image = sf.File(fake_image, filename="image.png")
    session_or_async_session.add_all(products)
    users = [
        User(name="Doe", files=[sf.File("Hello", filename="hello.txt")]),
        User(name="Terry", files=[]),
        User(name="admin"),
    ]
    products[3].user = users[0]
    products[4].user = users[1]
    session_or_async_session.add_all(users)


@pytest.fixture(params=["sync", "async"])
async def engine(request, fake_image, sqla_backend, sqla_storage_factory):
    """Parametrized engine fixture.

    Runs every test against all combinations of database backend
    (sqlite/mysql/postgres) and engine type (sync/async).
    """
    if request.param == "sync":
        eng: Engine | AsyncEngine = get_test_engine()
        Base.metadata.create_all(eng)
        StorageManager._clear()
        StorageManager.add_storage("test", sqla_storage_factory("test-sqla"))
        with Session(eng) as s:
            _seed(s, fake_image)
            s.commit()
        yield eng
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        Base.metadata.drop_all(eng)
    else:
        eng = get_async_test_engine()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        StorageManager._clear()
        StorageManager.add_storage("test", sqla_storage_factory("test-sqla"))
        async with AsyncSession(eng) as s:
            _seed(s, fake_image)
            await s.commit()
        yield eng
        for obj in StorageManager.get().list_objects():
            obj.delete()
        StorageManager.get().delete()
        async with eng.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await eng.dispose()


@pytest.fixture
async def session(engine: Engine | AsyncEngine):
    """Async-compatible session for both sync and async engine legs."""
    if isinstance(engine, AsyncEngine):
        async with AsyncSession(engine) as s:
            yield s
    else:
        with Session(engine) as s:
            yield _SyncToAsync(s)


@pytest.fixture
def admin(engine: Engine | AsyncEngine):
    adm = Admin(engine)
    adm.add_view(UserView(User))
    adm.add_view(ProductView(Product))
    return adm


@pytest.fixture
def app(admin: Admin):
    application = Starlette()
    admin.mount_to(application)
    return application


@pytest.fixture
async def client(app):
    async with csrf_async_client(app) as c:
        yield c


# ── Tests ─────────────────────────────────────────────────────────────────────


async def test_file_serving_api(
    admin: Admin, app: Starlette, client: AsyncClient, session
):
    assert len(admin._views) == 2
    assert (
        app.url_path_for("admin:api:file", storage="test", file_id="test_id")
        == "/admin/_api/file/test/test_id"
    )
    response = await client.get("/admin/_api/file/test/test_id")
    assert response.status_code == 404
    result = await session.execute(select(Product).where(Product.id == 1))
    path = result.scalar_one().image.path
    response = await client.get(f"/admin/_api/file/{path}")
    assert response.status_code == 200


async def test_list_page(client: AsyncClient):
    response = await client.get(
        "/admin/product/list",
        params={"page": 2, "page_size": 10, "sort": "title__desc"},
    )
    assert response.status_code == 200


async def test_list_find_by_pks_select2(client: AsyncClient):
    response = await client.get(
        "/admin/_api/product/relation-lookup",
        params={"pks": ["2", "3"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 2
    assert sorted(x["id"] for x in data["items"]) == [2, 3]


async def test_list_fulltext_search(client: AsyncClient):
    response = await client.get("/admin/product/list", params={"q": "IPhone"})
    assert response.status_code == 200


async def test_list_filter_boolean(client: AsyncClient):
    filt = "in_stock__is_true OR in_stock__is_false"
    response = await client.get("/admin/product/list", params={"filter": filt})
    assert response.status_code == 200


async def test_list_filter_string(client: AsyncClient):
    filt = "description__contains=App AND title__not_contains=Samsung"
    response = await client.get("/admin/product/list", params={"filter": filt})
    assert response.status_code == 200


async def test_list_filter_numeric(client: AsyncClient):
    filt = "price__gt=500 OR price__between=200..500"
    response = await client.get("/admin/product/list", params={"filter": filt})
    assert response.status_code == 200


async def test_list_filter_null_checks(client: AsyncClient):
    filt = "id__neq=5 AND in_stock__is_null"
    response = await client.get("/admin/product/list", params={"filter": filt})
    assert response.status_code == 200


@pytest.mark.parametrize(
    "resource,filt",
    [
        ("user", "products__is_null"),
        ("user", "products__is_not_null"),
        ("user", "products__is_not_null AND name__eq=Doe"),
        ("user", "products__is_not_null OR name__eq=admin"),
        ("product", "user__is_not_null"),
        ("product", "user__is_null"),
        ("product", "user__is_not_null AND title__eq=OPPOF19"),
        ("product", "user__is_not_null OR title__eq=OPPOF19"),
    ],
)
async def test_list_filter_relationships(client: AsyncClient, resource: str, filt: str):
    response = await client.get(f"/admin/{resource}/list", params={"filter": filt})
    assert response.status_code == 200


async def test_detail(client: AsyncClient):
    response = await client.get("/admin/product/detail?pk=1")
    assert response.status_code == 200
    response = await client.get("/admin/product/detail?pk=9")
    assert response.status_code == 404


async def test_create(client: AsyncClient, session):
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year Warranty"
            ),
            "price": 1049,
            "brand": "Infinix",
            # sku is read-only: a submitted value must be ignored in favor of
            # the column default.
            "sku": "hacked-sku",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(Product).where(Product.title == "Infinix INBOOK")
    )
    product = result.scalar_one()
    assert product is not None
    assert product.sku == "server-sku"


async def test_edit(client: AsyncClient, session):
    data = {
        "title": "Infinix INBOOK",
        "description": (
            "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year Warranty"
        ),
        "price": 1049,
        "brand": "Infinix",
        # sku is read-only: attempting to change it via the edit form must
        # have no effect. Every seeded product got the "server-sku" default
        # since products.json does not set sku.
        "sku": "hacked-sku",
    }
    response = await client.post(
        "/admin/product/edit?pk=1", data=data, follow_redirects=False
    )
    assert response.status_code == 303
    product = await session.get(Product, 1)
    assert product is not None
    assert product.title == data["title"]
    assert product.description == data["description"]
    assert product.price == data["price"]
    assert product.brand == data["brand"]
    assert product.sku == "server-sku"


async def test_delete(client: AsyncClient, session):
    response = await client.post(
        "/admin/_api/product/action", params={"name": "delete", "pks": [1, 3, 5]}
    )
    assert response.status_code == 200
    result = await session.execute(
        select(func.count(Product.id)).where(Product.id.in_([1, 3, 5]))
    )
    assert result.scalars().unique().all()[0] == 0


async def test_create_with_image(client: AsyncClient, session, fake_image):
    fake_image.seek(0)
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year Warranty"
            ),
            "price": 1049,
            "brand": "Infinix",
        },
        files={"image": ("image.png", fake_image, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(Product).where(Product.title == "Infinix INBOOK")
    )
    product = result.scalar_one()
    assert product.image.filename == "image.png"
    response = await client.get(f"/admin/_api/file/{product.image.path}")
    assert response.status_code == 200


async def test_edit_with_image(client: AsyncClient, session, fake_image):
    fake_image.seek(0)
    response = await client.post(
        "/admin/product/edit?pk=1",
        data={
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year Warranty"
            ),
            "price": "",
            "brand": "Infinix",
        },
        files={"image": ("image_edit.png", fake_image, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(Product).where(Product.title == "Infinix INBOOK")
    )
    product = result.scalar_one()
    assert product.image.filename == "image_edit.png"


async def test_edit_without_delete_image(client: AsyncClient, session):
    response = await client.post(
        "/admin/product/edit?pk=1",
        data={
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year Warranty"
            ),
            "price": "",
            "brand": "Infinix",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(Product).where(Product.title == "Infinix INBOOK")
    )
    product = result.scalar_one()
    assert product.image.filename == "image.png"


async def test_delete_image(client: AsyncClient, session):
    response = await client.post(
        "/admin/product/edit?pk=1",
        data={
            "title": "Infinix INBOOK",
            "description": (
                "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey - 1 Year Warranty"
            ),
            "price": 1049,
            "brand": "Infinix",
            "_image-delete": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    product = await session.get(Product, 1)
    assert product.image is None


async def test_file_validation_error(client: AsyncClient, fake_invalid_image):
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK",
            "description": "Infinix Inbook X1 Ci3",
            "price": "",
            "brand": "Infinix",
        },
        files={"image": ("image.png", fake_invalid_image, "image/png")},
    )
    assert response.status_code == 422
    assert has_invalid_feedback(response.text, "Upload a valid image file.")


async def test_create_with_empty_file(client: AsyncClient, session, fake_empty_file):
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK",
            "description": "Infinix Inbook X1 Ci3",
            "price": "",
            "brand": "Infinix",
        },
        files={"image": ("image.png", fake_empty_file, "image/png")},
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(Product).where(Product.title == "Infinix INBOOK")
    )
    product = result.scalar_one()
    assert product.image is None


async def test_create_with_multiple_files(client: AsyncClient, session, fake_image):
    fake_image.seek(0)
    response = await client.post(
        "/admin/user/create",
        data={"name": "John", "products": [1, 3, 5]},
        files=[
            ("files", ("text1.txt", fake_image, "text/plain")),
            ("files", ("text2", fake_image, "")),
        ],
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(User).where(User.name == "John").options(selectinload(User.products))
    )
    user = result.scalar_one()
    assert [x.id for x in user.products] == [1, 3, 5]
    assert [x.filename for x in user.files] == ["text1.txt", "text2"]

    response = await client.get("/admin/user/detail?pk=John")
    assert response.status_code == 200


async def test_edit_with_multiple_files(
    client: AsyncClient, session, fake_image_content
):
    response = await client.post(
        "/admin/user/edit?pk=admin",
        data={"name": "John", "products": [2, 3]},
        files=[
            ("files", ("new1.txt", fake_image_content, "text/plain")),
            ("files", ("new2.txt", fake_image_content, "text/plain")),
            ("files", ("new3.txt", fake_image_content, "text/plain")),
        ],
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(User).where(User.name == "John").options(selectinload(User.products))
    )
    user = result.scalar_one()
    assert [x.id for x in user.products] == [2, 3]
    assert len(user.files) == 3
    assert [x.filename for x in user.files] == ["new1.txt", "new2.txt", "new3.txt"]


async def test_edit_without_delete_multiple_files(
    client: AsyncClient, session, fake_empty_file
):
    response = await client.post(
        "/admin/user/edit?pk=Doe",
        data={"name": "Doe", "products": []},
        files=[("files", ("new1.txt", fake_empty_file, "text/plain"))],
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(User).where(User.name == "Doe").options(selectinload(User.products))
    )
    user = result.scalar_one()
    assert user.products == []
    assert len(user.files) == 1
    assert user.files[0].filename == "hello.txt"


async def test_edit_erase_old_files(client: AsyncClient, session):
    response = await client.post(
        "/admin/user/edit?pk=Doe",
        data={"name": "Doe", "products": [], "_files-delete": "on"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(User).where(User.name == "Doe").options(selectinload(User.products))
    )
    user = result.scalar_one()
    assert user.products == []
    assert user.files is None


async def test_create_with_relationships(client: AsyncClient, session):
    response = await client.post(
        "/admin/product/create",
        data={
            "title": "Infinix INBOOK of Doe",
            "description": "Infinix Inbook X1 Ci3 10th 8GB 256GB 14 Win10 Grey",
            "price": 1049,
            "brand": "Infinix",
            "user": "Doe",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    result = await session.execute(
        select(Product)
        .where(Product.title == "Infinix INBOOK of Doe")
        .options(selectinload(Product.user))
    )
    product = result.scalar_one()
    assert product.user.name == "Doe"

    response = await client.get(
        "/admin/_api/product/relation-lookup", params={"pks": [str(product.id)]}
    )
    assert response.status_code == 200
    assert response.json()["items"][0]["id"] == product.id


@pytest.mark.skipif(
    os.environ.get("SQLA_ENGINE", "").startswith("postgresql"),
    reason="PostgreSQL considers NULLS FIRST for DESC order",
)
async def test_sortable_field_mapping_1(client: AsyncClient):
    response = await client.get(
        "/admin/product/list",
        params={"sort": "user__desc", "page_size": 10},
    )
    assert response.status_code == 200


@pytest.mark.skipif(
    not os.environ.get("SQLA_ENGINE", "").startswith("postgresql"),
    reason="MySQL and SQLite consider NULLS LAST for DESC order",
)
async def test_sortable_field_mapping_2(client: AsyncClient):
    response = await client.get(
        "/admin/product/list",
        params={"sort": "user__asc", "page_size": 10},
    )
    assert response.status_code == 200
