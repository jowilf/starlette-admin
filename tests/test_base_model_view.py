from typing import List

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
    tags: List[str] = Field(default_factory=list)


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

    def test_hidden_from_list_field_attribute(self):
        """hidden_from_list should default to False and be settable."""
        visible_field = StringField("title")
        hidden_field = StringField("content", hidden_from_list=True)

        assert visible_field.hidden_from_list is False
        assert hidden_field.hidden_from_list is True

    def test_hidden_from_list_still_in_field_list(self):
        """Fields with hidden_from_list=True should still appear in get_fields_list."""

        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                StringField("content", hidden_from_list=True),
                IntegerField("views"),
            )

        view_instance = PostView()
        list_fields = view_instance.get_fields_list(None, RequestAction.LIST)
        assert tuple(f.name for f in list_fields) == ("id", "title", "content", "views")

    def test_hidden_from_list_excluded_field_not_in_list(self):
        """Fields with both exclude_from_list and hidden_from_list should be excluded."""

        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                StringField("content", hidden_from_list=True, exclude_from_list=True),
                IntegerField("views"),
            )

        view_instance = PostView()
        list_fields = view_instance.get_fields_list(None, RequestAction.LIST)
        assert tuple(f.name for f in list_fields) == ("id", "title", "views")

    def test_merged_datatables_options_hidden_columns(self):
        """_merged_datatables_options should generate columnDefs for hidden_from_list fields."""

        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                StringField("content", hidden_from_list=True),
                IntegerField("views"),
                TagsField("tags", hidden_from_list=True),
            )

        view_instance = PostView()
        opts = view_instance._merged_datatables_options(None)
        assert "columnDefs" in opts
        # content is at index 2 in list fields -> target 4 (+2 for checkbox and detail columns)
        # tags is at index 4 -> target 6
        hidden_def = opts["columnDefs"][0]
        assert hidden_def["visible"] is False
        assert hidden_def["targets"] == [4, 6]

    def test_merged_datatables_options_no_hidden(self):
        """_merged_datatables_options should return empty dict when no hidden fields."""

        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                IntegerField("views"),
            )

        view_instance = PostView()
        opts = view_instance._merged_datatables_options(None)
        assert opts == {}

    def test_merged_datatables_options_preserves_user_options(self):
        """_merged_datatables_options should merge with existing datatables_options."""

        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                StringField("content", hidden_from_list=True),
            )
            datatables_options = {"pageLength": 50}

        view_instance = PostView()
        opts = view_instance._merged_datatables_options(None)
        assert opts["pageLength"] == 50
        assert "columnDefs" in opts
        assert opts["columnDefs"][0]["targets"] == [4]

    def test_merged_datatables_options_merges_existing_column_defs(self):
        """_merged_datatables_options should append to existing columnDefs."""

        class PostView(DummyModelView):
            model = Post
            fields = (
                IntegerField("id"),
                StringField("title"),
                StringField("content", hidden_from_list=True),
            )
            datatables_options = {
                "columnDefs": [{"className": "text-center", "targets": [1]}]
            }

        view_instance = PostView()
        opts = view_instance._merged_datatables_options(None)
        assert len(opts["columnDefs"]) == 2
        assert opts["columnDefs"][0] == {"className": "text-center", "targets": [1]}
        assert opts["columnDefs"][1] == {"visible": False, "targets": [4]}
