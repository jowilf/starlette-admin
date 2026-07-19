import uuid

import pytest
import pytest_asyncio
from httpx2 import ASGITransport, AsyncClient
from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.view import ModelView

from tests.integration.sqla.utils import Uuid, get_test_engine


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "user"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid1, unique=True
    )
    name: Mapped[str] = mapped_column(String(50))
    membership: Mapped["Membership"] = relationship(
        "Membership", back_populates="user", uselist=False
    )


class Membership(Base):
    __tablename__ = "membership"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid1, unique=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("user.id"), unique=True)
    user: Mapped["User"] = relationship("User", back_populates="membership")


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
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as c:
        yield c


@pytest.mark.asyncio
async def test_ensuring_pk(client: AsyncClient, engine: Engine):
    """
    Ensures PK is present in the serialized data and properly serialized as a string,
    even when the PK field is not listed in the view's `fields`.
    """
    user_id = uuid.uuid1()
    membership_id = uuid.uuid1()

    user = User(id=user_id, name="Jack")
    membership = Membership(id=membership_id, is_active=True, user=user)

    with Session(engine) as session:
        session.add(user)
        session.add(membership)
        session.commit()

    # select2 serialises the item through serialize() which always injects the PK
    # even when it is not part of view.fields (UserView.fields = ["name", "membership"])
    response = await client.get(
        "/admin/_api/user/relation-lookup",
        params={"pks": [str(user_id)]},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(user_id)

    # The detail page renders the full object including nested membership with its PK
    response = await client.get(f"/admin/user/detail?pk={user_id}")
    assert response.status_code == 200
    assert str(membership_id) in response.text
