# Views: ModelView, relations, inline edit, inline forms, form layout

## Naming and routing

Defaults derive from the model class name: key `post` (URL `/admin/post/list`), menu label `Posts`, display name `Post`. Override at registration:

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

The primary key is auto-detected; set `pk_attr` only when detection fails. Primary keys are excluded from create and edit forms unless `show_pk_in_forms = True`.

## List page controls

```python
class PostView(ModelView):
    searchable_fields = ["title", "content"]      # global search + filter builder
    sortable_fields = ["title", "created_at"]     # clickable column headers
    fields_default_sort = [("created_at", True)]  # tuple with True = descending; chain for multi-column
    page_size = 25
    page_size_options = [25, 50, 100, -1]
    show_goto_page = True         # "go to page" input
    search_auto_submit = True     # filter as the user types
    show_detail_search = True     # search box for inline relationship tables on detail page
    row_click_navigate = False    # default True: clicking a row opens the detail page
```

Unauthorized sort parameters in the URL are silently ignored. Rows are never clickable for users failing `can_view_detail`.

## Inline edit

`inline_editable_fields` enables single-field editing from the list page: clicking an editable cell opens a popover with the field's standard form widget, pre-filled with the current value (x-editable style). Opt-in, disabled by default.

```python
class PostView(ModelView):
    fields = ["id", "title", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Startup validation (fail fast): every listed name must exist in `fields`, must not be the primary key, must not be excluded from the list page or the edit form, and must not be a `CollectionField`, `ListField`, `ComputedField`, `FileField`, or `ImageField`. Violations raise `ValueError` at view construction.

Behavior:

- Permissions reuse the standard model: the popover renders and saves only when `is_accessible(request)` and `can_edit(request)` both return `True`.
- An inline save validates and writes **only the edited field**. Its `required` check and `validators` chain run exactly as on the edit page; other fields are bypassed, so stale invalid data elsewhere never blocks the save.
- The view's `validate()` hook still runs, but `data` contains only the edited field: guard cross-field rules with `"name" in data` checks. A rule keyed to a field the user did not edit never fires; exclude fields with cross-field invariants from `inline_editable_fields`.
- `before_edit`, `after_edit`, and `after_edit_committed` hooks and the standard edit events fire normally, with single-field `data`/`old_data`. Detect an inline save via `request.state.action == RequestAction.INLINE_EDIT` in hooks, or `ctx.extra["inline"]` (set to `True`) in event listeners.
- On validation failure the popover stays open with the submitted value and the error rendered under the control.
- Widget assets (select2, flatpickr, JSONEditor, TinyMCE) load on the list page only for fields that are inline-editable; views without inline edit keep their current page footprint.
- Custom fields work automatically if they follow the `BaseField` contract and branch on `action.is_form()` rather than `action == RequestAction.EDIT` (`INLINE_EDIT` is a form action).

## Relational data

Include the relationship attribute in `fields` and register both views; the UI renders select2 widgets automatically:

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]      # HasMany, auto-detected

class PostView(ModelView):
    fields = ["id", "title", "author"]    # HasOne, auto-detected
```

Dropdowns load lazily through the related view's `/_api/{key}/relation-lookup` endpoint, so large tables stay fast. Manual `HasOne`/`HasMany` declaration is required only when the target view is registered under a custom `key`:

```python
fields = ["id", "name", HasMany("books", key="post-article")]
```

## Object representation (defined on the model)

`__admin_repr__` returns the plain-text label used in relationship columns, breadcrumbs, and confirmation messages. `__admin_select2_repr__` returns the HTML shown in relation dropdown options. Both accept the request and may be sync or async.

```python
class Author(Base):
    ...

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    def __admin_select2_repr__(self, request: Request) -> str:
        # Always escape database values: render with Jinja2 autoescape or html.escape
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

Fallback order for dropdowns: `__admin_select2_repr__`, then escaped `__admin_repr__`, then a generated summary of non-relation fields.

## Permission hooks

All default to `True`; override only what you restrict. `is_accessible` hides the view entirely (sidebar included).

```python
class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool: ...
    def can_edit(self, request: Request) -> bool: ...
    def can_delete(self, request: Request) -> bool: ...
    def can_view_detail(self, request: Request) -> bool: ...
    def can_export(self, request: Request) -> bool: ...
    def can_import(self, request: Request) -> bool: ...
    def can_access_field(
        self, request: Request, field: BaseField, action: RequestAction | None = None
    ) -> bool: ...
```

## Lifecycle hooks

`before_create(request, data, obj)`, `after_create(request, obj)`, and the edit/delete equivalents run around the database write. Mutate `obj` in `before_*` hooks:

```python
class PostView(ModelView):
    async def before_create(self, request, data, obj) -> None:
        obj.title = obj.title.strip()
```

`after_create_committed`, `after_edit_committed`, `after_delete_committed` run only after the transaction commits (SQLAlchemy backend only). Use them for side effects that must not fire on rollback (emails, background jobs). The request session is already closed there: never write through `request.state.session`; open a new session or do external I/O. In `after_delete_committed`, `obj` is detached: only attributes loaded before the delete are readable.

For cross-view logic (audit logs, webhooks), use events instead. See [actions-events.md](actions-events.md).

## Sidebar organization

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(menu_label="View Live Site", icon="fa fa-external-link", url="/", target="_blank"),
        ],
    )
)
```

`admin.add_link(link)` is a thin wrapper around `add_view`.

## Form layout

`form_layout` rearranges the create/edit forms without changing `fields`. A tuple puts fields side by side in one row; a bare string keeps a field on its own line.

```python
class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

Grouping widgets (all from `starlette_admin`, shared with dashboards):

- `PanelWidget(title=, children=, collapsible=, collapsed=)`: titled card, optionally collapsible.
- `FieldsetWidget(legend=, children=, disabled=)`: native HTML fieldset; `disabled=True` disables every nested control.
- `TabsWidget(tabs=[(label, children), ...])`: tabbed sections.
- `ColumnWidget(children=)`: untitled vertical group.
- Explicit widths: `RowWidget(children=[Col(FieldRef("name"), Breakpoints(default=12, md=4)), ...])`. `FieldRef("email", show_label=False)` suppresses the label.
- Static content anywhere: `HtmlWidget(html=...)`, `TextWidget(content=...)`.

Rules:

- Layout respects `can_access_field` and `exclude_from_create/edit`. Hidden fields make row siblings expand; fully empty containers are omitted; static widgets always render.
- Fields in `fields` but missing from the layout are appended at the bottom in declaration order.
- Duplicate references or unknown names raise `ValueError` at view construction.

## Inline forms

Manage child records inside the parent's create/edit page. Two steps: subclass `InlineModelView` (import from your backend contrib package) and list it in the parent's `inlines`.

```python
from starlette_admin.contrib.sqla import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["author", "body"]
    extra = 1                 # empty rows shown in addition to existing rows

class ArticleView(ModelView):
    fields = ["title", "body"]
    inlines = [CommentInline]
```

`InlineModelView` attributes: `model` (required), `fk_attr` (str or tuple for composite FK), `extra` (default 0), `allow_delete` (default True), `collapsible` (default True), `collapsed` (default False), `inline_template`.

The SQLAlchemy backend infers `fk_attr` from the parent relationship, including composite `ForeignKeyConstraint` keys. Set it explicitly when the parent has multiple relationships to the same child, the relationship is not declared on the ORM model, or inference fails (a `ValueError` is raised in that case).

Validation is per row, with errors attached to the failing row. On the SQLAlchemy backend the whole request is one transaction: any failing row rolls back the parent and every inline row together.
