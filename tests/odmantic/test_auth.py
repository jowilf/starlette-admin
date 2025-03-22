from typing import Sequence

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from odmantic import Field, Model, SyncEngine
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import BaseField, RequestAction
from starlette_admin.contrib.odmantic import Admin, ModelView

from tests.auth_provider import MyAuthProvider


class Post(Model):
    title: str
    super_admin_only_field: int = Field(0)


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
    @pytest_asyncio.fixture
    async def client(self, sync_engine: SyncEngine):
        admin = Admin(sync_engine, auth_provider=MyAuthProvider())
        app = Starlette()
        admin.add_view(PostView(Post))
        admin.mount_to(app)
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://testserver"
        ) as c:
            yield c
        sync_engine.remove(Post)

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
            ("terry", 0),
        ],
    )
    async def test_create(
        self, client, user_session, expected_value, sync_engine: SyncEngine
    ):
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
        assert (
            sync_engine.find_one(
                Post, Post.title == "Dummy post"
            ).super_admin_only_field
            == expected_value
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "user_session,expected_value",
        [
            ("super-admin", 1),
            ("terry", 0),
        ],
    )
    async def test_render_edit(
        self, client, user_session, expected_value, sync_engine: SyncEngine
    ):
        post = sync_engine.save(Post(title="Dummy Post"))
        response = await client.get(
            f"/admin/post/edit/{post.id}", cookies={"session": user_session}
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
    async def test_edit(
        self, client, user_session, expected_value, sync_engine: SyncEngine
    ):
        post = sync_engine.save(Post(title="Dummy Post"))
        dummy_data = {
            "title": "Dummy post - edit",
            "content": "This is a content - edit",
            "views": 8,
            "super_admin_only_field": 5,
        }
        response = await client.post(
            f"/admin/post/edit/{post.id}",
            data=dummy_data,
            cookies={"session": user_session},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert (
            sync_engine.find_one(Post, Post.id == post.id).super_admin_only_field
            == expected_value
        )
