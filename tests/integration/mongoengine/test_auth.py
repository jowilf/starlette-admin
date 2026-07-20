from collections.abc import Sequence

import mongoengine as me
import pytest
import pytest_asyncio
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import BaseField
from starlette_admin.contrib.mongoengine import Admin, ModelView
from starlette_admin.types import RequestAction

from tests.auth_provider import MyAuthProvider
from tests.utils import csrf_async_client


class Post(me.Document):
    title = me.StringField()
    super_admin_only_field = me.IntField(default=0)


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
    @pytest.fixture(autouse=True)
    def _db(self, mongo_url):
        connect(host=mongo_url, uuidRepresentation="standard")
        yield
        Post.drop_collection()
        disconnect()

    @pytest_asyncio.fixture
    async def client(self):
        admin = Admin(auth_provider=MyAuthProvider())
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
            ("terry", 0),
        ],
    )
    async def test_create(self, client, user_session, expected_value):
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
        assert (
            Post.objects(title="Dummy post").get().super_admin_only_field
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
    async def test_render_edit(self, client, user_session, expected_value):
        post = Post(title="Dummy post").save()
        client.cookies.set("session", user_session)
        response = await client.get(f"/admin/post/edit?pk={post.id}")
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
    async def test_edit(self, client, user_session, expected_value):
        post = Post(title="Dummy post").save()
        dummy_data = {
            "title": "Dummy post - edit",
            "content": "This is a content - edit",
            "views": 8,
            "super_admin_only_field": 5,
        }
        client.cookies.set("session", user_session)
        response = await client.post(
            f"/admin/post/edit?pk={post.id}",
            data=dummy_data,
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Post.objects(id=post.id).get().super_admin_only_field == expected_value
