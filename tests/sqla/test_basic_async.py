import pytest
from async_asgi_testclient import TestClient
from sqlalchemy import Column, Integer, String, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.sqla.utils import get_async_test_engine

engine = get_async_test_engine()

Base = declarative_base()


class Product(Base):
    __tablename__ = "product"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))


class ProductView(ModelView, model=Product):
    pass


@pytest.mark.asyncio
async def test_basic_async():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    admin = Admin(engine)
    admin.add_view(ProductView)
    app = Starlette()
    admin.mount_to(app)

    client = TestClient(app)
    response = await client.post(
        "/admin/product/create",
        form={"title": "Infinix INBOOK"},
        allow_redirects=False,
    )
    assert response.status_code == 303
    async with AsyncSession(engine) as session:
        stmt = select(Product).where(Product.title == "Infinix INBOOK")
        product = (await session.execute(stmt)).scalar_one()
        assert product is not None

    response = await client.post(
        "/admin/product/edit/1",
        form={"title": "Infinix INBOOK 2"},
        allow_redirects=False,
    )
    assert response.status_code == 303
    async with AsyncSession(engine) as session:
        stmt = select(Product).where(Product.title == "Infinix INBOOK 2")
        product = (await session.execute(stmt)).scalar_one()
        assert product is not None

    response = await client.get("/admin/api/product")
    assert response.status_code == 200
    assert response.json()["items"][0]["title"] == "Infinix INBOOK 2"

    response = await client.delete("/admin/api/product", query_string={"pks": [1]})
    assert response.status_code == 204

    async with AsyncSession(engine) as session:
        stmt = select(Product).where(Product.title == "Infinix INBOOK 2")
        product = (await session.execute(stmt)).one_or_none()
        assert product is None

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
