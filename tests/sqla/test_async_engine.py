from typing import Any, Dict

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from sqlalchemy.orm import declarative_base
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.sqla.utils import get_async_test_engine

Base = declarative_base()

pytestmark = pytest.mark.asyncio


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))


class ProductView(ModelView):
    async def before_create(
        self, request: Request, data: Dict[str, Any], obj: Any
    ) -> None:
        assert isinstance(obj, Product)
        assert obj.id is None
        assert obj.title == "Infinix INBOOK"

    async def after_create(self, request: Request, obj: Any) -> None:
        assert isinstance(obj, Product)
        assert obj.id is not None

    async def before_edit(
        self, request: Request, data: Dict[str, Any], obj: Any
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


@pytest_asyncio.fixture()
async def engine():
    _engine = get_async_test_engine()
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await _engine.dispose()


@pytest_asyncio.fixture()
async def session(engine: AsyncEngine) -> AsyncSession:
    async with AsyncSession(engine) as session:
        yield session


@pytest_asyncio.fixture
async def client(engine: AsyncEngine):
    admin = Admin(engine)
    admin.add_view(ProductView(Product))
    app = Starlette()
    admin.mount_to(app)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


async def test_api(client: AsyncClient, session: AsyncSession):
    session.add(Product(title="Infinix INBOOK"))
    await session.commit()
    response = await client.get("/admin/api/product")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["title"] == "Infinix INBOOK"


async def test_create(client: AsyncClient, session: AsyncSession):
    response = await client.post(
        "/admin/product/create",
        data={"title": "Infinix INBOOK"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Product).where(Product.title == "Infinix INBOOK")
    product = (await session.execute(stmt)).scalar_one()
    assert product is not None


async def test_edit(client: AsyncClient, session: AsyncSession):
    session.add(Product(title="Infinix INBOOK"))
    await session.commit()
    response = await client.post(
        "/admin/product/edit/1",
        data={"title": "Infinix INBOOK 2"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Product).where(Product.title == "Infinix INBOOK 2")
    product = (await session.execute(stmt)).scalar_one()
    assert product is not None
    assert product.id == 1


async def test_delete(client: AsyncClient, session: AsyncSession):
    session.add(Product(title="Infinix INBOOK"))
    await session.commit()
    response = await client.post(
        "/admin/api/product/action", params={"name": "delete", "pks": [1]}
    )
    assert response.status_code == 200
    stmt = select(Product).where(Product.id == 1)
    product = (await session.execute(stmt)).one_or_none()
    assert product is None
