import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, relationship
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.sqla.utils import Uuid, get_test_engine

Base = declarative_base()


class User(Base):
    __tablename__ = "user"

    id = Column(Uuid, primary_key=True, default=uuid.uuid1, unique=True)
    name = Column(String(50))
    membership = relationship("Membership", back_populates="user", uselist=False)


class Membership(Base):
    __tablename__ = "membership"

    id = Column(Uuid, primary_key=True, default=uuid.uuid1, unique=True)
    is_active = Column(Boolean, default=True)

    user_id = Column(Uuid, ForeignKey("user.id"), unique=True)
    user = relationship("User", back_populates="membership")


class UserView(ModelView):
    fields = ["name", "membership"]


@pytest.fixture
def engine() -> Engine:
    engine = get_test_engine()

    Base.metadata.create_all(engine)

    try:
        yield engine

    finally:
        Base.metadata.drop_all(engine)


@pytest.fixture
def app(engine: Engine):
    app = Starlette()

    admin = Admin(engine)
    admin.add_view(UserView(User))
    admin.add_view(ModelView(Membership))
    admin.mount_to(app)

    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as c:
        yield c


@pytest.mark.asyncio
async def test_ensuring_pk(client: AsyncClient, engine: Engine):
    """
    Ensures PK is present in the serialized data and properly serialized as a string.
    """
    user_id = uuid.uuid1()
    membership_id = uuid.uuid1()

    user = User(id=user_id, name="Jack")
    membership = Membership(id=membership_id, is_active=True, user=user)

    with Session(engine) as session:
        session.add(user)
        session.add(membership)
        session.commit()

    response = await client.get("/admin/api/user")
    data = response.json()

    assert [(str(user_id), str(membership_id))] == [
        (x["id"], x["membership"]["id"]) for x in data["items"]
    ]
