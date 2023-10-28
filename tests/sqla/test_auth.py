from typing import Sequence

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import Column, Integer, String
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import BaseField, RequestAction
from starlette_admin.contrib.sqla import Admin, ModelView

from tests.auth_provider import MyAuthProvider
from tests.sqla.utils import get_test_engine

Base = declarative_base()


class Post(Base):
    __tablename__ = "post"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    super_admin_only_field = Column(Integer, default=0)


class PostView(ModelView):
    def get_fields_list(
        self,
        request: Request,
        action: RequestAction = RequestAction.LIST,
    ) -> Sequence[BaseField]:
        fields = super().get_fields_list(request, action)
        if "super-admin" not in request.state.user_roles:
            fields = [f for f in fields if f.name != "super_admin_only_field"]
        return fields


class TestFieldAccess:
    @pytest.fixture
    def engine(self) -> Engine:
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
        async with AsyncClient(app=app, base_url="http://testserver") as c:
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
        response = await client.get(
            "/admin/post/create", cookies={"session": user_session}
        )
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
        response = await client.post(
            "/admin/post/create",
            data=dummy_data,
            cookies={"session": user_session},
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
        response = await client.get(
            "/admin/post/edit/1", cookies={"session": user_session}
        )
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
        response = await client.post(
            "/admin/post/edit/1",
            data=dummy_data,
            cookies={"session": user_session},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert session.get(Post, 1).super_admin_only_field == expected_value
