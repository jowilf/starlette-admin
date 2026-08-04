from unittest.mock import MagicMock

from pydantic import Field
from starlette_admin import (
    IntegerField,
    RequestAction,
    StringField,
    TagsField,
    TextAreaField,
)

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView


class Post(TinydbBaseModel):
    title: str = ""
    content: str = ""
    views: int = 0
    tags: list[str] = Field(default_factory=list)


class TestView:
    def test_basic(self):
        class PostView(TinydbModelView):
            fields = [
                IntegerField("id"),
                StringField("title"),
                TextAreaField("content"),
                IntegerField("views"),
                TagsField("tags"),
            ]
            searchable_fields = ("title", "content")
            sortable_fields = ("id", "title", "content", "views")

        view_instance = PostView(Post)
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
        class PostViewWithPkInForm(TinydbModelView):
            fields = [
                IntegerField("id"),
                StringField("title"),
                TextAreaField("content"),
                IntegerField("views"),
                TagsField("tags"),
            ]
            show_pk_in_forms = True

        view_instance = PostViewWithPkInForm(Post)
        assert not view_instance.fields[0].exclude_from_create
        assert not view_instance.fields[0].exclude_from_edit

    def test_fields_exclusion(self):
        class PostViewWithExclusion(TinydbModelView):
            fields = [
                IntegerField("id"),
                StringField("title"),
                TextAreaField("content"),
                IntegerField("views"),
                TagsField("tags"),
            ]
            show_pk_in_forms = True
            exclude_fields_from_list = ["content"]
            exclude_fields_from_detail = ["tags"]
            exclude_fields_from_create = ["tags", "views"]
            exclude_fields_from_edit = ["views", "id"]

        def req(action: RequestAction) -> MagicMock:
            r = MagicMock()
            r.state.action = action
            return r

        view_instance = PostViewWithExclusion(Post)
        assert tuple(
            f.name for f in view_instance.get_fields_list(req(RequestAction.LIST))
        ) == (
            "id",
            "title",
            "views",
            "tags",
        )
        assert tuple(
            f.name for f in view_instance.get_fields_list(req(RequestAction.DETAIL))
        ) == (
            "id",
            "title",
            "content",
            "views",
        )
        assert tuple(
            f.name for f in view_instance.get_fields_list(req(RequestAction.CREATE))
        ) == (
            "id",
            "title",
            "content",
        )
        assert tuple(
            f.name for f in view_instance.get_fields_list(req(RequestAction.EDIT))
        ) == (
            "title",
            "content",
            "tags",
        )
