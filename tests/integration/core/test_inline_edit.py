"""Integration tests for the list-page inline-edit feature (DESIGN.md).

Exercises the full path: `inline_editable_fields` startup validation, the
`GET`/`POST /_api/{key}/inline-edit` endpoints (running under
`RequestAction.INLINE_EDIT`), the row endpoint
(`GET /_api/{key}/inline-edit/row`) that re-renders one list row after a
save, permission gating, the single-field pipeline
(`request.state.inline_edit_field` narrows `get_fields_list`, so `edit()`
receives and persists only the edited field), the validation policy (a
failed save re-renders the field fragment with the submitted value and its
errors), and event tagging (`extra["inline"]=True`).
"""

from __future__ import annotations

from datetime import date

import pytest
from pydantic import Field
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette_admin import (
    BaseAdmin,
    BooleanField,
    ComputedField,
    DateField,
    FileField,
    HasMany,
    IntegerField,
    ListField,
    StringField,
    TextAreaField,
)
from starlette_admin.events import AdminEvent
from starlette_admin.exceptions import FormValidationError
from starlette_admin.types import RequestAction

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class Author(TinydbBaseModel):
    name: str

    async def __admin_repr__(self, request):
        return self.name


class Post(TinydbBaseModel):
    title: str
    content: str = ""
    views: int = 0
    published: bool = False
    happens_on: date | None = None
    authors: list[Author] = Field(default_factory=list)

    async def __admin_repr__(self, request):
        return self.title


class AuthorView(TinydbModelView):
    key = "inline-edit-author"
    fields = [IntegerField("id"), StringField("name")]


class PostView(TinydbModelView):
    key = "inline-edit-post"
    fields = [
        IntegerField("id"),
        StringField("title", required=True),
        TextAreaField("content"),
        IntegerField("views"),
        BooleanField("published"),
        DateField("happens_on"),
        HasMany("authors", key="inline-edit-author"),
    ]
    inline_editable_fields = ["title", "views", "published"]

    async def validate_data(self, data: dict) -> None:
        errors: dict = {}
        if data.get("title") == "FORBIDDEN":
            errors["title"] = "Title is forbidden"
        if data.get("content") == "FORBIDDEN":
            errors["content"] = "Content is forbidden"
        if data.get("title") == "CROSS":
            errors["content"] = "Content conflicts with title"
        if errors:
            raise FormValidationError(errors)


def _make_app() -> tuple[Starlette, BaseAdmin, PostView, AuthorView]:
    admin = BaseAdmin()
    app = Starlette()
    author_view = AuthorView(Author)
    post_view = PostView(Post)
    admin.add_view(author_view)
    admin.add_view(post_view)
    admin.mount_to(app)
    return app, admin, post_view, author_view


@pytest.fixture(autouse=True)
def _reset_db():
    AuthorView._db.truncate()
    PostView._db.truncate()
    PostView._db.insert(
        Post(title="Hello world", content="body", views=3).to_tinydb_doc()
    )


class TestInlineEditStartupValidation:
    def test_unknown_field_raises(self):
        class BadView(TinydbModelView):
            fields = [IntegerField("id"), StringField("title")]
            inline_editable_fields = ["nope"]

        with pytest.raises(ValueError, match="inline_editable_fields references"):
            BadView(Post)

    def test_excluded_from_list_raises(self):
        class BadView(TinydbModelView):
            fields = [IntegerField("id"), StringField("title")]
            exclude_fields_from_list = ["title"]
            inline_editable_fields = ["title"]

        with pytest.raises(ValueError, match="visible on the list page"):
            BadView(Post)

    def test_excluded_from_edit_raises(self):
        class BadView(TinydbModelView):
            fields = [IntegerField("id"), StringField("title")]
            exclude_fields_from_edit = ["title"]
            inline_editable_fields = ["title"]

        with pytest.raises(ValueError, match="editable on the edit page"):
            BadView(Post)

    def test_pk_field_raises(self):
        class BadView(TinydbModelView):
            fields = [IntegerField("id"), StringField("title")]
            inline_editable_fields = ["id"]

        with pytest.raises(ValueError, match="primary key"):
            BadView(Post)

    def test_container_field_raises(self):
        class BadView(TinydbModelView):
            fields = [
                IntegerField("id"),
                ListField(StringField("tag")),
            ]
            inline_editable_fields = ["tag"]

        with pytest.raises(ValueError, match="ListField"):
            BadView(Post)

    def test_computed_field_raises(self):
        class BadView(TinydbModelView):
            fields = [
                IntegerField("id"),
                ComputedField("summary", getter=lambda request, obj: "x"),
            ]
            inline_editable_fields = ["summary"]

        with pytest.raises(ValueError, match="ComputedField"):
            BadView(Post)

    def test_file_field_raises(self):
        class BadView(TinydbModelView):
            fields = [IntegerField("id"), FileField("attachment")]
            inline_editable_fields = ["attachment"]

        with pytest.raises(ValueError, match="FileField"):
            BadView(Post)

    def test_disabled_by_default(self):
        class PlainView(TinydbModelView):
            fields = [IntegerField("id"), StringField("title")]

        view = PlainView(Post)
        assert view.inline_editable_fields is None


class TestInlineEditPermissions:
    def test_field_not_in_allowlist_is_403(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=content"
        )
        assert response.status_code == 403

    def test_can_edit_false_is_403(self):
        class LockedPostView(PostView):
            def can_edit(self, request):
                return False

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(LockedPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title"
        )
        assert response.status_code == 403

    def test_is_accessible_false_is_403(self):
        class HiddenPostView(PostView):
            def is_accessible(self, request):
                return False

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(HiddenPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title"
        )
        assert response.status_code == 403


class TestInlineEditGet:
    def test_get_renders_form_fragment(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title"
        )
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert 'value="Hello world"' in response.text

    def test_get_not_found(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit?pk=999&field=title"
        )
        assert response.status_code == 404


class TestInlineEditPost:
    def test_post_success_updates_and_returns_json(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "Updated title"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pk"] == "1" or data["pk"] == 1
        assert data["field"] == "title"
        # The message names the edited field, not the whole item.
        assert "Title" in data["msg"]
        assert "Updated title" in data["msg"]
        assert PostView._get(1).title == "Updated title"
        # Non-edited fields are untouched.
        assert PostView._get(1).content == "body"
        assert PostView._get(1).views == 3

    def test_post_field_validation_error_rerenders_fragment(self):
        """A validation failure re-renders the field fragment (HTML, not
        JSON) with the error attached, like the edit page re-renders its
        form on a failed submit."""
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": ""},
        )
        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert "invalid-feedback" in response.text
        assert PostView._get(1).title == "Hello world"

    def test_cross_field_hook_rejects_edited_field(self):
        """The cross-field `validate` hook still runs on an inline save and
        can reject the edited field's new value; the fragment comes back
        with the submitted value and the error message."""
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "FORBIDDEN"},
        )
        assert response.status_code == 422
        assert "text/html" in response.headers["content-type"]
        assert "Title is forbidden" in response.text
        # The submitted value is echoed back so the user's input is kept.
        assert 'value="FORBIDDEN"' in response.text
        assert PostView._get(1).title == "Hello world"

    def test_cross_field_error_on_other_field_is_labeled(self):
        """A message keyed to a field other than the edited one renders in
        the fragment's cross-errors block, prefixed with that field's
        label."""
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "CROSS"},
        )
        assert response.status_code == 422
        assert "inline-edit-cross-errors" in response.text
        assert "Content conflicts with title" in response.text
        assert PostView._get(1).title == "Hello world"

    def test_cross_field_hook_sees_only_edited_field(self):
        """Inline edit hands hooks a data dict holding only the edited field:
        a rule keyed to the unedited `content` field cannot fire, and the
        save succeeds."""
        PostView._db.update({"content": "FORBIDDEN"}, doc_ids=[1])
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=views",
            data={"views": "42"},
        )
        assert response.status_code == 200
        assert PostView._get(1).views == 42
        assert PostView._get(1).content == "FORBIDDEN"

    def test_post_unexpected_error_rerenders_fragment_500(self):
        """A non-validation failure inside `edit()` re-renders the field
        fragment (with the submitted value and a generic error), not the
        HTML error page, so the popover keeps the typed value."""

        class BoomPostView(PostView):
            async def edit(self, request, pk, data):
                raise RuntimeError("boom")

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(BoomPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "x"},
        )
        assert response.status_code == 500
        assert "text/html" in response.headers["content-type"]
        assert "Something went wrong!" in response.text
        assert 'value="x"' in response.text
        assert PostView._get(1).title == "Hello world"

    def test_post_not_in_allowlist_is_403(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=content",
            data={"content": "hacked"},
        )
        assert response.status_code == 403
        assert PostView._get(1).content == "body"


class TestInlineEditRow:
    """`GET /_api/{key}/inline-edit/row` renders one list `<tr>` through the
    same `_list_row.html` the list page uses, so the client can swap the
    edited row in place after a save."""

    def test_row_renders_list_markup(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get("/admin/_api/inline-edit-post/inline-edit/row?pk=1")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "<tr" in response.text
        assert 'data-pk="1"' in response.text
        assert "Hello world" in response.text
        assert 'data-inline-editable="1"' in response.text
        assert "row-checkbox" in response.text

    def test_row_honors_visible_columns(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit/row?pk=1&cols=title"
        )
        assert response.status_code == 200
        assert 'data-column="title"' in response.text
        assert 'data-column="views"' not in response.text

    def test_row_not_found(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get("/admin/_api/inline-edit-post/inline-edit/row?pk=999")
        assert response.status_code == 404

    def test_row_is_accessible_false_is_403(self):
        class HiddenPostView(PostView):
            def is_accessible(self, request):
                return False

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(HiddenPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.get("/admin/_api/inline-edit-post/inline-edit/row?pk=1")
        assert response.status_code == 403


class TestInlineEditEvents:
    def test_events_tagged_inline(self):
        app, admin, _post_view, _author_view = _make_app()
        seen = []
        admin.events.on(AdminEvent.BEFORE_EDIT, seen.append)
        admin.events.on(AdminEvent.AFTER_EDIT, seen.append)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "Tagged"},
        )
        assert response.status_code == 200
        assert len(seen) == 2
        for ctx in seen:
            assert ctx.extra.get("inline") is True

    def test_regular_edit_page_not_tagged_inline(self):
        app, admin, _post_view, _author_view = _make_app()
        seen = []
        admin.events.on(AdminEvent.AFTER_EDIT, seen.append)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.post(
            "/admin/inline-edit-post/edit?pk=1",
            data={
                "title": "Via edit page",
                "content": "body",
                "views": "3",
                "happens_on": "",
            },
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert len(seen) == 1
        assert "inline" not in seen[0].extra


class TestInlineEditSingleField:
    """An inline save hands `edit()` a data dict holding only the edited
    field, and every other field is persisted untouched (no serialize/parse
    round-trip of unedited values)."""

    def test_edit_receives_only_the_edited_field(self):
        captured: dict = {}

        class CapturingPostView(PostView):
            async def edit(self, request, pk, data):
                captured["data"] = dict(data)
                return await super().edit(request, pk, data)

        admin = BaseAdmin()
        app = Starlette()
        author_view = AuthorView(Author)
        admin.add_view(author_view)
        admin.add_view(CapturingPostView(Post))
        admin.mount_to(app)

        author_pk = AuthorView._db.insert(Author(name="Alice").to_tinydb_doc())
        alice = AuthorView._get(author_pk)
        seeded = Post(
            title="Hello world",
            content="body",
            views=3,
            published=True,
            happens_on=date(2026, 1, 2),
            authors=[alice],
        )
        PostView._db.update(seeded.to_tinydb_doc(), doc_ids=[1])

        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "New title"},
        )
        assert response.status_code == 200

        assert captured["data"] == {"title": "New title"}

        persisted = PostView._get(1)
        assert persisted.title == "New title"
        assert persisted.content == "body"
        assert persisted.views == 3
        assert persisted.happens_on == date(2026, 1, 2)
        assert persisted.published is True
        assert [a.id for a in persisted.authors] == [author_pk]

    def test_other_fields_are_not_validated(self):
        """Validation narrows with the pipeline: a required unedited field
        (`title`) is not re-validated when another field is saved inline."""
        PostView._db.update({"title": ""}, doc_ids=[1])
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=views",
            data={"views": "7"},
        )
        assert response.status_code == 200
        assert PostView._get(1).views == 7
        assert PostView._get(1).title == ""


class TestInlineEditListPageAssets:
    def test_assets_included_when_enabled(self):
        _app, _admin, _post_view, _author_view = _make_app()
        client = CsrfTestClient(_app, base_url="http://testserver")
        response = client.get("/admin/inline-edit-post/list")
        assert response.status_code == 200
        assert "js/form.js" in response.text
        assert "css/inline-edit.css" in response.text
        assert 'data-inline-editable="1"' in response.text
        assert 'data-field="title"' in response.text

    def test_assets_excluded_when_disabled(self):
        class PlainPostView(PostView):
            inline_editable_fields = None

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(PlainPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.get("/admin/inline-edit-post/list")
        assert response.status_code == 200
        assert "css/inline-edit.css" not in response.text
        assert "data-inline-editable" not in response.text


class TestInlineEditFieldAccessibility:
    def test_field_inaccessible_during_inline_edit_is_403(self):
        class RestrictedPostView(PostView):
            def can_access_field(self, request, field, action=None):
                action = action if action is not None else request.state.action
                return not (
                    field.name == "title" and action == RequestAction.INLINE_EDIT
                )

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(RestrictedPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.get(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title"
        )
        assert response.status_code == 403

    def test_post_http_exception_is_reraised(self):
        class ExceptionPostView(PostView):
            async def edit(self, request, pk, data):
                raise HTTPException(status_code=500)

        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(AuthorView(Author))
        admin.add_view(ExceptionPostView(Post))
        admin.mount_to(app)
        client = CsrfTestClient(app, base_url="http://testserver")
        response = client.post(
            "/admin/_api/inline-edit-post/inline-edit?pk=1&field=title",
            data={"title": "Updated"},
        )
        assert response.status_code == 500
