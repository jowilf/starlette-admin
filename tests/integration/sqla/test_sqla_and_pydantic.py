from datetime import date, datetime, time

import pytest
import pytest_asyncio
from httpx2 import AsyncClient
from pydantic import BaseModel, Field
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Time,
    select,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client

pytestmark = pytest.mark.asyncio


class Base(DeclarativeBase):
    pass


class IDMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)


class User(Base, IDMixin):
    __tablename__ = "user"

    name: Mapped[str] = mapped_column(String(100))
    todos: Mapped[set["Todo"]] = relationship(
        "Todo", back_populates="user", collection_class=set
    )


class Todo(Base, IDMixin):
    __tablename__ = "todo"

    todo: Mapped[str] = mapped_column(String(255))
    completed: Mapped[bool | None] = mapped_column(Boolean)
    deadline: Mapped[datetime] = mapped_column(DateTime)
    completed_date: Mapped[date | None] = mapped_column(Date)
    completed_time: Mapped[time | None] = mapped_column(Time)

    user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("user.id"))
    user: Mapped["User"] = relationship("User", back_populates="todos")


class UserIn(BaseModel):
    id: int | None = Field(None, json_schema_extra={"primary_key": True})
    name: str = Field(max_length=100)


class TodoIn(BaseModel):
    id: int | None = Field(None, json_schema_extra={"primary_key": True})
    todo: str = Field(min_length=10)
    completed: bool | None
    deadline: datetime
    completed_date: date | None
    completed_time: time | None


@pytest.fixture
def engine() -> Engine:
    _engine = get_test_engine()
    Base.metadata.create_all(_engine)
    yield _engine
    Base.metadata.drop_all(_engine)


@pytest.fixture
def session(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


@pytest.fixture
def admin(engine: Engine):
    admin = Admin(engine)
    admin.add_view(ModelView(User, pydantic_model=UserIn))
    admin.add_view(ModelView(Todo, pydantic_model=TodoIn))
    return admin


@pytest.fixture
def app(admin: Admin):
    app = Starlette()
    admin.mount_to(app)
    return app


@pytest_asyncio.fixture
async def client(app):
    async with csrf_async_client(app) as c:
        yield c


async def test_create(client: AsyncClient, session: Session):
    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do something nice for someone I care about",
            "deadline": datetime.now().isoformat(),
            "completed": "on",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "Do something nice for someone I care about")
    todo = session.execute(stmt).scalar_one()
    assert todo is not None


async def test_create_validation_error(client: AsyncClient, session: Session):
    # A missing required field is caught by field-level validation, which
    # runs before (and short-circuits) model-level Pydantic validation.
    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do some",
            "completed_date": date.today().isoformat(),
            "completed_time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 422
    assert (
        '<div class="invalid-feedback">This field is required.</div>' in response.text
    )

    # Once field-level validation passes, Pydantic model errors surface.
    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do some",
            "deadline": datetime.now().isoformat(),
            "completed_date": date.today().isoformat(),
            "completed_time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 422
    assert (
        '<div class="invalid-feedback">ensure this value has at least 10'
        " characters</div>"
        in response.text
        or '<div class="invalid-feedback">String should have at least 10'  # pydantic v2
        " characters</div>"
        in response.text
    )


async def test_edit(client: AsyncClient, session: Session):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.get("/admin/todo/edit?pk=1")
    assert response.status_code == 200

    response = await client.post(
        "/admin/todo/edit?pk=1",
        data={
            "todo": "End magic things",
            "deadline": datetime(2022, 2, 1).isoformat(),
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "End magic things")
    todo = session.execute(stmt).scalar_one()
    assert todo is not None
    assert todo.id == 1
    assert todo.deadline == datetime(2022, 2, 1)


async def test_edit_validation_error(client: AsyncClient, session: Session):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.commit()

    # A missing required field is caught by field-level validation, which
    # runs before (and short-circuits) model-level Pydantic validation.
    response = await client.post(
        "/admin/todo/edit?pk=1",
        data={
            "todo": "Do some",
            "completed_date": date.today().isoformat(),
            "completed_time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 422
    assert (
        '<div class="invalid-feedback">This field is required.</div>' in response.text
    )

    # Once field-level validation passes, Pydantic model errors surface.
    response = await client.post(
        "/admin/todo/edit?pk=1",
        data={
            "todo": "Do some",
            "deadline": datetime(2022, 2, 1).isoformat(),
            "completed_date": date.today().isoformat(),
            "completed_time": datetime.now().strftime("%H:%M:%S"),
        },
    )
    assert response.status_code == 422
    assert (
        '<div class="invalid-feedback">ensure this value has at least 10'
        " characters</div>"
        in response.text
        or '<div class="invalid-feedback">String should have at least 10'  # pydantic v2
        " characters</div>"
        in response.text
    )


async def test_delete(client: AsyncClient, session: Session):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.post(
        "/admin/_api/todo/action", params={"name": "delete", "pks": [1]}
    )
    assert response.status_code == 200
    assert session.get(Todo, 1) is None


async def test_create_with_has_one_relationships(client: AsyncClient, session: Session):
    session.add(User(name="John Doe"))
    session.commit()

    response = await client.post(
        "/admin/todo/create",
        data={
            "todo": "Do something nice for someone I care about",
            "deadline": datetime.now().isoformat(),
            "completed": "on",
            "user": 1,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "Do something nice for someone I care about")
    todo = session.execute(stmt).scalar_one()
    assert todo.user.name == "John Doe"


async def test_edit_with_has_one_relationships(client: AsyncClient, session: Session):
    session.add(
        Todo(
            todo="Do some magic",
            deadline=datetime(2022, 1, 1),
            user=User(id=1, name="John Doe"),
        )
    )
    session.add(User(id=2, name="Tommy Sharp"))
    session.commit()

    response = await client.post(
        "/admin/todo/edit?pk=1",
        data={
            "todo": "Do some magic",
            "deadline": datetime.now().isoformat(),
            "completed": "on",
            "user": 2,
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(Todo).where(Todo.todo == "Do some magic")
    todo = session.execute(stmt).scalar_one()
    assert todo.user.name == "Tommy Sharp"


async def test_create_with_has_many_relationships(
    client: AsyncClient, session: Session
):
    session.add(Todo(todo="Do some magic", deadline=datetime(2022, 1, 1)))
    session.add(Todo(todo="Do something nice", deadline=datetime(2022, 1, 1)))
    session.commit()

    response = await client.post(
        "/admin/user/create",
        data={"name": "John Doe", "todos": [1, 2]},
        follow_redirects=False,
    )
    assert response.status_code == 303
    stmt = select(User).where(User.name == "John Doe")
    user = session.execute(stmt).scalar_one()
    assert len(user.todos) == 2
    assert sorted([t.todo for t in user.todos]) == [
        "Do some magic",
        "Do something nice",
    ]
