import mongoengine as me
import pytest
from mongoengine import connect, disconnect
from starlette.applications import Starlette
from starlette.testclient import TestClient
from starlette_admin.contrib.mongoengine import Admin, ModelView

from tests.mongoengine import MONGO_URL


class Category(me.EmbeddedDocument):
    name = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    content = me.StringField()
    category = me.EmbeddedDocumentField(Category)
    comments = me.EmbeddedDocumentListField(Comment)


class TestEmbeddedDocument:
    def setup_method(self, method):
        connect(host=MONGO_URL, uuidRepresentation="standard")
        Post(
            name="Dummy post",
            content="Dummy content",
            category=Category(name="dummy"),
            comments=[Comment(content="Nice")],
        ).save()

    def teardown_method(self, method):
        Post.drop_collection()
        disconnect()

    @pytest.fixture
    def client(self):
        admin = Admin()
        app = Starlette()
        admin.add_view(ModelView(Post))
        admin.mount_to(app)
        return TestClient(app, base_url="http://testserver")

    def test_create(self, client):
        response = client.post(
            "/admin/post/create",
            data={
                "name": "His mother had always taught him",
                "content": "Lorem ipsum dolor sit amet consectetur adipisicing elit",
                "category.name": "education",
                "comments.1.content": "Nice article!",
                "comments.2.content": "Good work!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Post.objects.count() == 2
        post = Post.objects(name="His mother had always taught him").get()
        assert post is not None
        assert post.category.name == "education"
        assert len(post.comments) == 2
        assert post.comments[0].content == "Nice article!"
        assert post.comments[1].content == "Good work!"

    def test_edit(self, client):
        id = Post.objects(name="Dummy post").get().id
        response = client.post(
            f"/admin/post/edit/{id}",
            data={
                "name": "His mother had always taught him",
                "content": "Lorem ipsum dolor sit amet consectetur adipisicing elit",
                "category.name": "education",
                "comments.1.content": "Nice article!",
                "comments.2.content": "Good work!",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert Post.objects.count() == 1
        post = Post.objects(name="His mother had always taught him").get()
        assert post is not None
        assert post.category.name == "education"
        assert len(post.comments) == 2
        assert post.comments[0].content == "Nice article!"
        assert post.comments[1].content == "Good work!"
