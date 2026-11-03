import uuid
from collections.abc import Generator
from uuid import UUID

import pytest
import pytest_asyncio
from httpx2 import AsyncClient
from sqlalchemy import String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from sqlalchemy_utils import PasswordType, UUIDType
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


class PasswordBase(DeclarativeBase):
    pass


class User(PasswordBase):
    __tablename__ = "password_user"

    uuid: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(100))
    password: Mapped[str | None] = mapped_column(
        PasswordType(schemes=["pbkdf2_sha512"])
    )


@pytest.fixture
def engine(fake_image) -> Generator[Engine]:
    _engine = get_test_engine()
    PasswordBase.metadata.create_all(_engine)
    yield _engine
    PasswordBase.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Generator[Session]:
    with Session(engine) as session:
        yield session


@pytest_asyncio.fixture
async def client(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(User))
    app = Starlette()
    admin.mount_to(app)
    async with csrf_async_client(app) as c:
        yield c


async def _create_user(
    client: AsyncClient, session: Session, email: str, password: str
) -> User:
    response = await client.post(
        "/admin/user/create",
        data={"email": email, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303
    return session.execute(select(User).where(User.email == email)).scalar_one()


async def test_password_field_not_serialized_on_edit(
    client: AsyncClient, session: Session
) -> None:
    """The stored hash must not be rendered into the edit form."""
    user = await _create_user(client, session, "user1@example.com", "secret123")
    original_hash = user.password

    response = await client.get(f"/admin/user/edit?pk={user.uuid}")
    assert response.status_code == 200

    assert "secret123" not in response.text
    assert str(original_hash) not in response.text


async def test_password_not_overwritten_when_left_blank_on_edit(
    client: AsyncClient, session: Session
) -> None:
    """Submitting an empty password on edit must preserve the existing one."""
    user = await _create_user(client, session, "user2@example.com", "original_pass")
    original_hash = user.password

    response = await client.post(
        f"/admin/user/edit?pk={user.uuid}",
        data={"email": "user2@example.com", "password": ""},
        follow_redirects=False,
    )
    assert response.status_code == 303

    session.refresh(user)
    assert user.password == original_hash


async def test_password_updated_when_new_value_provided_on_edit(
    client: AsyncClient, session: Session
) -> None:
    """Submitting a new password on edit must update the stored one."""
    user = await _create_user(client, session, "user3@example.com", "old_pass")
    original_hash = user.password

    response = await client.post(
        f"/admin/user/edit?pk={user.uuid}",
        data={"email": "user3@example.com", "password": "new_secret"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    session.refresh(user)
    assert user.password != original_hash
