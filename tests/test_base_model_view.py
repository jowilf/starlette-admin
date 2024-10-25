from pydantic import Field
from starlette_admin import (
    IntegerField,
    RequestAction,
    StringField,
    TagsField,
    TextAreaField,
)

from tests.dummy_model_view import DummyBaseModel, DummyModelView


class Post(DummyBaseModel):
    title: str
    content: str
    views: int = 0
    tags: list[str] = Field(default_factory=list)


class TestView:
    def test_basic(self):
        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                TextAreaField("content"),
                IntegerField("views"),
                TagsField("tags"),
            )
            searchable_fields = ("title", "content")
            sortable_fields = ("id", "title", "content", "views")

        view_instance = PostView()
        assert view_instance.fields[0].exclude_from_create
        assert view_instance.fields[0].exclude_from_edit

        assert tuple(f.name for f in view_instance.fields if f.orderable) == (
            "id",
            "title",
            "content",
            "views",
        )
        assert tuple(f.name for f in view_instance.fields if f.searchable) == (
            "title",
            "content",
        )

    def test_force_include_pk_in_form(self):
        class PostViewWithPkInForm(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                TextAreaField("content"),
                IntegerField("views"),
                TagsField("tags"),
            )
            form_include_pk = True

        view_instance = PostViewWithPkInForm()
        assert not view_instance.fields[0].exclude_from_create
        assert not view_instance.fields[0].exclude_from_edit

    def test_fields_exclusion(self):
        class PostViewWithExclusion(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                TextAreaField("content"),
                IntegerField("views"),
                TagsField("tags"),
            )
            form_include_pk = True
            exclude_fields_from_list = ["content"]
            exclude_fields_from_detail = ["tags"]
            exclude_fields_from_create = ["tags", "views"]
            exclude_fields_from_edit = ["views", "id"]

        view_instance = PostViewWithExclusion()
        assert tuple(
            f.name for f in view_instance.get_fields_list(None, RequestAction.LIST)
        ) == (
            "id",
            "title",
            "views",
            "tags",
        )
        assert tuple(
            f.name for f in view_instance.get_fields_list(None, RequestAction.DETAIL)
        ) == (
            "id",
            "title",
            "content",
            "views",
        )
        assert tuple(
            f.name for f in view_instance.get_fields_list(None, RequestAction.CREATE)
        ) == (
            "id",
            "title",
            "content",
        )
        assert tuple(
            f.name for f in view_instance.get_fields_list(None, RequestAction.EDIT)
        ) == (
            "title",
            "content",
            "tags",
        )
