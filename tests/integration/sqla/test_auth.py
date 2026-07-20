from collections.abc import Sequence

import pytest
import pytest_asyncio
from sqlalchemy import Integer, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import BaseField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.types import RequestAction

from tests.auth_provider import MyAuthProvider
from tests.integration.sqla.utils import get_test_engine
from tests.utils import csrf_async_client


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    super_admin_only_field: Mapped[int] = mapped_column(Integer, default=0)


class PostView(ModelView):
    def get_fields_list(
        self,
        request: Request,
        *,
        include_nested: bool = False,
        action: RequestAction | None = None,
    ) -> Sequence[BaseField]:
        fields = super().get_fields_list(
            request, include_nested=include_nested, action=action
        )
        if "super-admin" not in request.state.user_roles:
            fields = [f for f in fields if f.name != "super_admin_only_field"]
        return fields


class TestFieldAccess:
    @pytest.fixture
    def engine(self, sqla_backend) -> Engine:
        engine = get_test_engine()
        Base.metadata.create_all(engine)

        yield engine

        Base.metadata.drop_all(engine)

    @pytest.fixture
    def session(self, engine: Engine) -> Session:
        with Session(engine) as session:
            yield session

    @pytest_asyncio.fixture
    async def client(self, engine):
        admin = Admin(engine, auth_provider=MyAuthProvider())
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        async with csrf_async_client(app) as c:
            yield c

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_create(self, client, user_session, expected_value):
        client.cookies.set("session", user_session)
        response = await client.get("/admin/post/create")
        assert response.status_code == 200
        assert response.text.count('name="super_admin_only_field"') == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_session,expected_value",
        [
            ("super-admin", 5),
        ],
    )
    async def test_create(self, client, session, user_session, expected_value):
        dummy_data = {
            "title": "Dummy post",
            "content": "This is a content",
            "views": 10,
            "super_admin_only_field": 5,
        }
        client.cookies.set("session", user_session)
        response = await client.post(
            "/admin/post/create",
            data=dummy_data,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert session.get(Post, 1).super_admin_only_field == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_edit(self, client, session, user_session, expected_value):
        session.add(Post(title="Dummy post"))
        session.commit()
        client.cookies.set("session", user_session)
        response = await client.get("/admin/post/edit?pk=1")
        assert response.status_code == 200
        assert response.text.count('name="super_admin_only_field"') == expected_value

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_session,expected_value",
        [
            ("super-admin", 5),
            ("terry", 0),
        ],
    )
    async def test_edit(self, client, session, user_session, expected_value):
        session.add(Post(title="Dummy post"))
        session.commit()
        dummy_data = {
            "title": "Dummy post - edit",
            "content": "This is a content - edit",
            "views": 8,
            "super_admin_only_field": 5,
        }
        client.cookies.set("session", user_session)
        response = await client.post(
            "/admin/post/edit?pk=1",
            data=dummy_data,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert session.get(Post, 1).super_admin_only_field == expected_value
