"""Tests for BaseModelView.form_layout."""

import pytest
from jinja2 import Environment
from markupsafe import Markup
from starlette.applications import Starlette
from starlette.requests import Request
from starlette_admin import (
    BaseAdmin,
    BaseWidget,
    Col,
    ColumnWidget,
    FieldRef,
    FieldsetWidget,
    HtmlWidget,
    IntegerField,
    PanelWidget,
    RowWidget,
    StringField,
    TabsWidget,
)
from starlette_admin.exceptions import FormValidationError

from tests.integration.core.tinydb_model_view import TinydbBaseModel, TinydbModelView
from tests.utils import CsrfTestClient


class Person(TinydbBaseModel):
    first_name: str = ""
    last_name: str = ""
    bio: str = ""
    secret: str = ""


class PersonViewNoFormLayout(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
        StringField("bio"),
    ]


class PersonView(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
        StringField("bio"),
        StringField("secret", exclude_from_create=True, exclude_from_edit=True),
    ]
    form_layout = [
        PanelWidget(title="Name", children=["first_name", "last_name"]),
        PanelWidget(
            title="Advanced",
            children=["bio", "secret"],
            collapsible=True,
            collapsed=True,
        ),
    ]


class PersonViewWithLeftover(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
    ]
    form_layout = [PanelWidget(title="Name", children=["first_name"])]


class PersonViewWithRow(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
        StringField("bio"),
        StringField("secret", exclude_from_create=True, exclude_from_edit=True),
    ]
    form_layout = [
        PanelWidget(
            title="Name", children=[("first_name", "last_name"), "bio", "secret"]
        ),
    ]


class PersonViewWithHiddenLabel(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
    ]
    form_layout = [
        FieldRef("first_name", show_label=False),
        FieldRef("last_name"),
    ]


class PersonViewWithInputGroup(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name", required=True),
        StringField("last_name"),
        StringField("bio"),
    ]
    form_layout = [
        FieldRef("first_name", prepend="@"),
        FieldRef("last_name", append='<i class="fa fa-phone"></i>'),
        FieldRef("bio"),
    ]

    async def validate_data(self, data: dict):
        if not data["first_name"]:
            raise FormValidationError({"first_name": "first_name is required"})


class PersonViewWithTopLevelShorthand(TinydbModelView):
    fields = [
        IntegerField("id"),
        StringField("first_name"),
        StringField("last_name"),
        StringField("bio"),
    ]
    form_layout = [
        "first_name",
        ("last_name", "bio"),
    ]


class TestFormLayoutValidation:
    def test_unknown_field_name_raises(self):
        class BadView(TinydbModelView):
            fields = [StringField("first_name")]
            form_layout = [PanelWidget(title="X", children=["does_not_exist"])]

        with pytest.raises(ValueError, match="does_not_exist"):
            BadView(Person)

    def test_field_in_two_panels_raises(self):
        class BadView(TinydbModelView):
            fields = [StringField("first_name"), StringField("last_name")]
            form_layout = [
                PanelWidget(title="A", children=["first_name"]),
                PanelWidget(title="B", children=["first_name", "last_name"]),
            ]

        with pytest.raises(ValueError, match="first_name"):
            BadView(Person)

    def test_leftover_fields_appended_as_trailing_form_fields(self):
        view = PersonViewWithLeftover(Person)
        assert len(view.form_layout) == 3
        trailing = view.form_layout[1:]
        assert all(isinstance(node, FieldRef) for node in trailing)
        assert [node.name for node in trailing] == ["id", "last_name"]

    def test_unknown_field_name_in_row_raises(self):
        class BadView(TinydbModelView):
            fields = [StringField("first_name"), StringField("last_name")]
            form_layout = [
                PanelWidget(title="X", children=[("first_name", "does_not_exist")])
            ]

        with pytest.raises(ValueError, match="does_not_exist"):
            BadView(Person)

    def test_field_in_row_and_elsewhere_raises(self):
        class BadView(TinydbModelView):
            fields = [StringField("first_name"), StringField("last_name")]
            form_layout = [
                PanelWidget(title="A", children=[("first_name", "last_name")]),
                PanelWidget(title="B", children=["first_name"]),
            ]

        with pytest.raises(ValueError, match="first_name"):
            BadView(Person)

    def test_top_level_string_normalizes_to_field_ref(self):
        class ShorthandView(TinydbModelView):
            fields = [StringField("first_name"), StringField("last_name")]
            form_layout = ["first_name", PanelWidget(title="B", children=["last_name"])]

        view = ShorthandView(Person)
        assert isinstance(view.form_layout[0], FieldRef)
        assert view.form_layout[0].name == "first_name"

    def test_top_level_tuple_normalizes_to_row_widget(self):
        class ShorthandView(TinydbModelView):
            fields = [StringField("first_name"), StringField("last_name")]
            form_layout = [("first_name", "last_name")]

        view = ShorthandView(Person)
        row = view.form_layout[0]
        assert isinstance(row, RowWidget)
        assert [col.widget.name for col in row.children] == ["first_name", "last_name"]

    def test_top_level_shorthand_unknown_field_raises(self):
        class BadView(TinydbModelView):
            fields = [StringField("first_name")]
            form_layout = ["does_not_exist"]

        with pytest.raises(ValueError, match="does_not_exist"):
            BadView(Person)

    def test_field_nested_several_containers_deep_is_found(self):
        """The recursive normalizer/validator must reach a field referenced
        inside a panel, inside a tab, inside a column."""

        class DeepView(TinydbModelView):
            fields = [StringField("first_name"), StringField("last_name")]
            form_layout = [
                PanelWidget(
                    title="Outer",
                    children=[
                        TabsWidget(
                            tabs=[
                                (
                                    "Tab",
                                    ColumnWidget(children=["first_name"]),
                                )
                            ]
                        )
                    ],
                ),
            ]

        view = DeepView(Person)
        # `last_name` was never referenced, so it's appended as a trailing
        # top-level FieldRef -- proving the leftover computation also sees
        # through the nesting.
        assert isinstance(view.form_layout[1], FieldRef)
        assert view.form_layout[1].name == "last_name"

    def test_unknown_field_nested_several_containers_deep_raises(self):
        class BadView(TinydbModelView):
            fields = [StringField("first_name")]
            form_layout = [
                PanelWidget(
                    title="Outer",
                    children=[
                        TabsWidget(
                            tabs=[("Tab", ColumnWidget(children=["does_not_exist"]))]
                        )
                    ],
                ),
            ]

        with pytest.raises(ValueError, match="does_not_exist"):
            BadView(Person)


def _fake_request(action: str = "CREATE"):
    from unittest.mock import MagicMock

    from starlette.datastructures import State
    from starlette_admin.types import RequestAction

    request = MagicMock()
    request.state = State()
    request.state.action = RequestAction(action)
    return request


def _field_names(widget: BaseWidget | None) -> list[str]:
    """Depth-first list of every resolved `FieldRef.name` in `widget`."""
    if widget is None:
        return []
    if isinstance(widget, FieldRef):
        return [widget.name]
    if isinstance(widget, RowWidget):
        names = []
        for child in widget.children:
            names.extend(
                _field_names(child.widget if isinstance(child, Col) else child)
            )
        return names
    if isinstance(widget, (ColumnWidget, PanelWidget, FieldsetWidget)):
        names = []
        for child in widget.children:
            names.extend(_field_names(child))
        return names
    if isinstance(widget, TabsWidget):
        names = []
        for _label, child in widget.tabs:
            names.extend(_field_names(child))
        return names
    return []


class TestResolveFormLayout:
    def test_defaults_to_flat_field_list_when_unset(self):
        view = PersonViewNoFormLayout(Person)
        request = _fake_request()
        tree = view.resolve_form_layout(request)
        assert isinstance(tree, ColumnWidget)
        # "id" is the pk and is excluded from create/edit by default
        # (show_pk_in_forms=False), so it never reaches resolve_form_layout.
        assert _field_names(tree) == ["first_name", "last_name", "bio"]
        assert all(isinstance(child, FieldRef) for child in tree.children)

    def test_returns_none_when_unset_and_no_fields_accessible(self):
        """With no `form_layout` and every field excluded from create, there's
        nothing to fall back to, so the flat-list branch has no fields to
        wrap and resolution yields `None` instead of an empty widget tree."""

        class AllHiddenView(TinydbModelView):
            fields = [
                StringField("first_name", exclude_from_create=True),
            ]

        view = AllHiddenView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        assert tree is None

    def test_resolves_declared_panels_in_order(self):
        """ "id" is the only field left out of the declared form_layout, but as
        the pk it's excluded from create forms, so the trailing FieldRef
        that would otherwise hold it has nothing to show and is dropped."""
        view = PersonView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        titles = [panel.title for panel in tree.children]
        assert titles == ["Name", "Advanced"]

    def test_excluded_field_drops_from_its_panel(self):
        """`secret` is excluded from create, so it's absent from the
        'Advanced' panel's resolved children."""
        view = PersonView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        advanced = next(p for p in tree.children if p.title == "Advanced")
        assert _field_names(advanced) == ["bio"]

    def test_panel_omitted_when_no_fields_remain_visible(self):
        class OnlySecretView(TinydbModelView):
            show_pk_in_forms = True
            fields = [
                IntegerField("id"),
                StringField("visible"),
                StringField("hidden", exclude_from_create=True),
            ]
            form_layout = [
                PanelWidget(title="Hidden", children=["hidden"]),
                PanelWidget(title="Visible", children=["visible", "id"]),
            ]

        view = OnlySecretView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        titles = [panel.title for panel in tree.children]
        assert titles == ["Visible"]

    def test_fieldset_resolves_and_prunes_hidden_fields(self):
        class FieldsetView(TinydbModelView):
            show_pk_in_forms = True
            fields = [
                IntegerField("id"),
                StringField("visible"),
                StringField("hidden", exclude_from_create=True),
            ]
            form_layout = [
                FieldsetWidget(legend="Hidden", children=["hidden"]),
                FieldsetWidget(legend="Visible", children=["visible", "id"]),
            ]

        view = FieldsetView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        legends = [fieldset.legend for fieldset in tree.children]
        assert legends == ["Visible"]
        assert _field_names(tree.children[0]) == ["visible", "id"]

    def test_row_groups_multiple_fields_together(self):
        view = PersonViewWithRow(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        panel = tree.children[0]
        # `secret` is excluded from create, so the trailing single-field
        # entry it would otherwise occupy is dropped entirely.
        assert isinstance(panel.children[0], RowWidget)
        assert [c.widget.name for c in panel.children[0].children] == [
            "first_name",
            "last_name",
        ]
        assert [c.name for c in panel.children[1:]] == ["bio"]

    def test_top_level_shorthand_resolves_to_field_and_row(self):
        view = PersonViewWithTopLevelShorthand(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        first, second = tree.children
        assert isinstance(first, FieldRef)
        assert first.name == "first_name"
        assert isinstance(second, RowWidget)
        assert [c.widget.name for c in second.children] == ["last_name", "bio"]

    def test_row_field_hidden_leaves_row_with_remaining_fields(self):
        class PartiallyHiddenRowView(TinydbModelView):
            fields = [
                IntegerField("id"),
                StringField("first_name"),
                StringField("last_name", exclude_from_create=True),
            ]
            form_layout = [
                PanelWidget(title="Name", children=[("first_name", "last_name")]),
            ]

        view = PartiallyHiddenRowView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        panel = tree.children[0]
        assert _field_names(panel) == ["first_name"]

    def test_single_field_panel_hides_its_label(self):
        """`PersonViewWithLeftover`'s panel declares only "first_name", so
        the panel title alone identifies the field and its label is
        redundant."""
        view = PersonViewWithLeftover(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        panel = tree.children[0]
        assert isinstance(panel, PanelWidget)
        assert len(panel.children) == 1
        assert panel.children[0].name == "first_name"
        assert panel.children[0].show_label is False

    def test_panel_reduced_to_one_field_by_hiding_hides_its_label(self):
        """`PersonView`'s "Advanced" panel declares two fields, but `secret`
        is excluded from create, so only `bio` remains visible -- and its
        label is hidden too, same as if the panel had declared one field."""
        view = PersonView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        advanced = next(p for p in tree.children if p.title == "Advanced")
        assert len(advanced.children) == 1
        assert advanced.children[0].name == "bio"
        assert advanced.children[0].show_label is False

    def test_static_content_always_renders(self):
        class HtmlView(TinydbModelView):
            fields = [StringField("first_name")]
            form_layout = [
                HtmlWidget(html="<p class='hint'>Fill carefully</p>"),
                "first_name",
            ]

        view = HtmlView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        assert isinstance(tree.children[0], HtmlWidget)
        assert isinstance(tree.children[1], FieldRef)

    def test_tabs_resolve_and_drop_empty_tabs(self):
        class TabbedView(TinydbModelView):
            fields = [
                StringField("first_name"),
                StringField("last_name", exclude_from_create=True),
            ]
            form_layout = [
                TabsWidget(
                    tabs=[
                        ("Identity", ColumnWidget(children=["first_name"])),
                        ("Extra", ColumnWidget(children=["last_name"])),
                    ]
                )
            ]

        view = TabbedView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        tabs_widget = tree.children[0]
        assert isinstance(tabs_widget, TabsWidget)
        # "Extra" holds only `last_name`, hidden on create, so its column
        # resolves to nothing and the tab itself is dropped.
        assert [label for label, _ in tabs_widget.tabs] == ["Identity"]

    def test_tab_list_shorthand_normalizes_to_column_of_rows(self):
        """A tab's widget may be a list of top-level-style entries -- a bare
        name for its own row, a tuple for a side-by-side row -- exactly
        like a top-level `form_layout`, sparing an explicit `ColumnWidget`
        wrapper."""

        class TabbedView(TinydbModelView):
            fields = [
                StringField("first_name"),
                StringField("last_name"),
                StringField("bio"),
            ]
            form_layout = [
                TabsWidget(tabs=[("Identity", ["first_name", ("last_name", "bio")])])
            ]

        view = TabbedView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        tabs_widget = tree.children[0]
        label, column = tabs_widget.tabs[0]
        assert label == "Identity"
        assert isinstance(column, ColumnWidget)
        first, row = column.children
        assert isinstance(first, FieldRef)
        assert first.name == "first_name"
        assert isinstance(row, RowWidget)
        assert [c.widget.name for c in row.children] == ["last_name", "bio"]

    def test_custom_widget_subclass_always_renders(self):
        class StaticNoteWidget(BaseWidget):
            async def render(self, request: Request, env: Environment) -> Markup:
                return Markup('<div data-testid="static-note">Static note</div>')

        class CustomWidgetView(TinydbModelView):
            fields = [StringField("first_name")]
            form_layout = [StaticNoteWidget(), "first_name"]

        view = CustomWidgetView(Person)
        request = _fake_request(action="CREATE")
        tree = view.resolve_form_layout(request)
        assert isinstance(tree.children[0], StaticNoteWidget)


class TestFormLayoutRendering:
    @pytest.fixture(autouse=True)
    def reset_db(self):
        PersonView._db.truncate()

    @pytest.fixture
    def client(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PersonView(Person))
        admin.mount_to(app)
        return CsrfTestClient(app, base_url="http://testserver")

    def test_create_page_renders_panel_cards(self, client):
        response = client.get("/admin/person/create")
        assert response.status_code == 200
        # one card for the page header + one per PanelWidget
        assert response.text.count('<div class="card">') == 3
        assert "Name" in response.text
        assert "Advanced" in response.text
        # collapsible + collapsed panel starts hidden (no "show" class)
        assert 'aria-expanded="false"' in response.text
        # each visible field name appears exactly once
        for name in ("first_name", "last_name", "bio"):
            assert response.text.count(f'name="{name}"') == 1
        # excluded from create: not rendered at all
        assert response.text.count('name="secret"') == 0

    def test_row_fields_render_side_by_side(self, client):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PersonViewWithRow(Person))
        admin.mount_to(app)
        row_client = CsrfTestClient(app, base_url="http://testserver")

        response = row_client.get("/admin/person/create")
        assert response.status_code == 200
        # first_name and last_name share a RowWidget row, as equal-width
        # flex columns...
        first_name_pos = response.text.index('name="first_name"')
        last_name_pos = response.text.index('name="last_name"')
        row_pos = response.text.rindex(
            '<div class="row row-deck row-cards">', 0, first_name_pos
        )
        assert row_pos < first_name_pos < last_name_pos
        assert response.text[row_pos:last_name_pos].count('class="col-12 col-md"') == 2
        # ...while bio, not inside any row, has no column wrapper at all.
        bio_pos = response.text.index('name="bio"')
        between = response.text[last_name_pos:bio_pos]
        assert "col-12 col-md" not in between

    def test_form_field_show_label_false_omits_label(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PersonViewWithHiddenLabel(Person))
        admin.mount_to(app)
        hidden_label_client = CsrfTestClient(app, base_url="http://testserver")

        response = hidden_label_client.get("/admin/person/create")
        assert response.status_code == 200
        first_name_pos = response.text.index('name="first_name"')
        last_name_pos = response.text.index('name="last_name"')
        # first_name has no label between its <div class="mb-3"> wrapper and
        # its input; last_name (default show_label=True) does.
        assert 'for="first_name"' not in response.text[:first_name_pos]
        assert 'for="last_name"' in response.text[:last_name_pos]

    def test_single_field_panel_renders_without_label(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PersonViewWithLeftover(Person))
        admin.mount_to(app)
        leftover_client = CsrfTestClient(app, base_url="http://testserver")

        response = leftover_client.get("/admin/person/create")
        assert response.status_code == 200
        # "Name" panel declares only "first_name", so its label is
        # redundant with the panel title and is omitted; "last_name" (a
        # trailing, unpanelled FieldRef) keeps its label.
        first_name_pos = response.text.index('name="first_name"')
        last_name_pos = response.text.index('name="last_name"')
        assert 'for="first_name"' not in response.text[:first_name_pos]
        assert 'for="last_name"' in response.text[first_name_pos:last_name_pos]

    def test_create_and_edit_round_trip_with_form_layout(self, client):
        response = client.post(
            "/admin/person/create",
            data={"first_name": "Ada", "last_name": "Lovelace", "bio": "Mathematician"},
            follow_redirects=False,
        )
        assert response.status_code == 303
        stored = PersonView._get(1)
        assert stored.first_name == "Ada"
        assert stored.bio == "Mathematician"

        response = client.get("/admin/person/edit", params={"pk": 1})
        assert response.status_code == 200
        assert response.text.count('<div class="card">') == 3
        assert 'value="Ada"' in response.text


class TestFieldRefInputGroup:
    @pytest.fixture(autouse=True)
    def reset_db(self):
        PersonViewWithInputGroup._db.truncate()

    @pytest.fixture
    def client(self):
        admin = BaseAdmin()
        app = Starlette()
        admin.add_view(PersonViewWithInputGroup(Person))
        admin.mount_to(app)
        return CsrfTestClient(app, base_url="http://testserver")

    def test_prepend_and_append_render_as_input_group(self, client):
        response = client.get("/admin/person/create")
        assert response.status_code == 200

        first_name_pos = response.text.index('name="first_name"')
        last_name_pos = response.text.index('name="last_name"')
        bio_pos = response.text.index('name="bio"')

        # first_name: plain-text prepend addon before the input.
        before_first_name = response.text[:first_name_pos]
        assert '<div class="input-group' in before_first_name
        assert (
            '<span class="input-group-text">@</span>'
            in response.text[
                before_first_name.rindex('<div class="input-group') : first_name_pos
            ]
        )

        # last_name: raw-HTML append addon after the input, unescaped.
        between_last_name_and_bio = response.text[last_name_pos:bio_pos]
        assert (
            '<span class="input-group-text"><i class="fa fa-phone"></i></span>'
            in between_last_name_and_bio
        )

        # bio has no addons configured, so it must render byte-identical to
        # the plain (no input-group) markup: no input-group wrapper at all.
        between_bio_and_end = response.text[bio_pos:]
        next_input_group = between_bio_and_end.find('class="input-group')
        next_field = between_bio_and_end.find("<input", 1)
        assert next_input_group == -1 or (
            next_field != -1 and next_input_group > next_field
        )

    def test_validation_error_still_renders_invalid_feedback(self, client):
        response = client.post(
            "/admin/person/create",
            data={"first_name": "", "last_name": "Lovelace", "bio": ""},
        )
        assert response.status_code == 422
        assert "invalid-feedback" in response.text
        # the input-group wrapper is still emitted around the errored field.
        first_name_pos = response.text.index('name="first_name"')
        before_first_name = response.text[:first_name_pos]
        assert '<div class="input-group' in before_first_name
