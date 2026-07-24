---
name: starlette-admin
description: Build and customize admin interfaces with starlette-admin, the admin framework for Starlette and FastAPI apps. Use when creating an admin panel or CRUD dashboard for SQLAlchemy, SQLModel, Beanie, or MongoEngine models, or when working with ModelView, fields, field validators, filters, batch/row actions, inline editing, authentication, file uploads, export/import, inline forms, custom dashboards, or widgets in starlette-admin.
---

# starlette-admin

starlette-admin generates a full admin interface (paginated list, detail, create, edit, delete, search, filters, export, import) from data models. You configure everything through view classes; no custom routes or templates are needed for standard CRUD.

## Mental model

- **`Admin`** is a self-contained sub-application mounted onto a Starlette or FastAPI app. All admin-wide settings (title, base_url, auth, theme, i18n) are constructor kwargs.
- **One class per resource.** A `ModelView` subclass is the single source of truth for how one model looks, validates, and behaves. `CustomView` builds standalone pages, `Link` adds sidebar hyperlinks, `DropDown` groups views into folders.
- **The same view API works on every backend.** Only the import path changes between SQLAlchemy, SQLModel, Beanie, and MongoEngine. Fields, filters, permissions, and hooks are identical.
- **Fields render themselves** in three contexts: list cell, detail row, form input. Strings in `fields` are auto-converted from column metadata; pass explicit field instances for control.
- **List state lives in the URL** (`page`, `order_by`, `q`, `filter`), so every filtered view is bookmarkable.

## Backend import matrix

| Backend | Imports | Admin constructor |
| --- | --- | --- |
| SQLAlchemy 2 | `from starlette_admin.contrib.sqla import Admin, ModelView` | `Admin(engine_or_sessionmaker, ...)` |
| SQLModel | `from starlette_admin.contrib.sqlmodel import Admin, ModelView` | Same as sqla (re-export, adds Pydantic validation) |
| Beanie | `from starlette_admin.contrib.beanie import Admin, ModelView` | `Admin(...)`, init Beanie in app lifespan first |
| MongoEngine | `from starlette_admin.contrib.mongoengine import Admin, ModelView` | `Admin(...)`, call `me.connect()` in lifespan first |

Never import `ModelView` from `starlette_admin` directly for a real backend. Field classes, widgets, and decorators do come from the top-level `starlette_admin` package; backend-specific filter classes come from `starlette_admin.contrib.<backend>.filters`.

## Minimal working app (SQLAlchemy + FastAPI)

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)  # Starlette(lifespan=lifespan) works identically

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

The admin is served at `/admin`. Icons accept any Font Awesome class. Async engines (`create_async_engine`) work with the same code.

## Critical rules

These are the mistakes that break real apps. Follow them without exception.

1. **Register views before mounting.** `mount_to(app)` locks the admin. Calling `add_view` afterward, mounting twice, or touching `admin.app` before mounting raises `RuntimeError`.
2. **Always set `secret_key` explicitly** (from an environment variable in production). It signs the CSRF and flash cookies. Without it, each worker process generates its own key and CSRF validation fails randomly across workers.
3. **Never call `session.commit()` on the SQLAlchemy backend.** Use `request.state.session` (populated by middleware on every request), call `session.flush()` if needed, and let the middleware commit exactly once per request. It rolls back on exceptions and on responses with status >= 400.
4. **`AuthProvider` requires `SessionMiddleware`** on the host app, because `login()` and `authenticate()` persist state in `request.session`. See [references/auth.md](references/auth.md).
5. **Import filter classes from your backend's module** (`starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters`), never from `starlette_admin.filters` when passing `filters=` to a field.
6. **`EnumField` requires exactly one of** `enum=`, `choices=`, or `choices_loader=`.
7. **`__admin_repr__` and `__admin_select2_repr__` are defined on the model, not the view.** Without them, related records display as bare primary keys. `__admin_select2_repr__` returns HTML: render it with Jinja2 `autoescape=True` or escape values manually to prevent XSS.
8. **`PasswordField` only masks form input.** Values render as plain text on list and detail pages and are logged at DEBUG level. Set `exclude_from_list=True` and `exclude_from_detail=True` on it.
9. **Storage-backed `FileField`/`ImageField` need a JSON-capable column.** The database stores `FileInfo` metadata only. Orphaned files are never cleaned up automatically; use sqlalchemy-file if uploads must be transactional. `ListField(FileField(...))` is unsupported, use `multiple=True`.
10. **In actions, signal outcomes with `flash(request, msg, "success")` and `raise ActionFailed("msg")`,** not return values. Do not call `flash()` in an `ActionFailed` branch, the request does not redirect.
11. **Batch action handlers receive an `ActionSelection`, never a `pks` list.** Call `await selection.rows()`, `.pks()`, or `.count()`; the selection may represent "select all matching" rather than materialized rows, so treating it as a list breaks under that mode.
12. **Always call `super()` for unhandled names** when overriding `is_action_allowed`, `is_row_action_allowed`, or `is_row_action_allowed_for_obj`. Skipping it silently disables the permission checks behind the built-in view/edit/delete actions.
13. **`after_*_committed` hooks fire only on the SQLAlchemy backend** and run after the session is committed and closed. Never write through `request.state.session` inside them.
14. **Multiple `Admin` instances on one app need distinct `base_url` and `route_name`,** otherwise generated links resolve to the wrong admin.
15. **Import creates per row unless upsert is on.** The wizard's "Update existing records by primary key" option calls `edit()` on PK matches; without it, re-importing an export with primary keys duplicates rows or fails. The preview step validates everything before writing; unchecking the PK column lets backends auto-generate keys.
16. **`form_layout` must reference each field at most once and only names present in `fields`;** violations raise `ValueError` at view construction. Fields omitted from the layout are appended at the bottom, never lost.
17. **Inline saves submit only the edited field.** With `inline_editable_fields`, the view's `validate()` hook and the edit lifecycle hooks receive `data` containing just that field. Guard cross-field rules with `"name" in data` checks; direct indexing raises `KeyError`.

## ModelView configuration cheat sheet

```python
class PostView(ModelView):
    # What is shown; strings are auto-converted, or pass field instances
    fields = ["id", StringField("title", required=True), "content", "author"]

    # Surface-specific hiding: _create, _edit, _list, _detail, _export, _import
    exclude_fields_from_create = ["created_at"]

    # List page behavior
    searchable_fields = ["title", "content"]   # enables search box + filter builder
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]   # True = descending
    page_size = 25
    page_size_options = [25, 50, 100, -1]          # -1 renders as "All"

    # Feature lists
    actions = ["make_published", "delete"]          # batch actions ("delete" is built in)
    row_actions = ["view", "edit", "delete"]        # built-in row actions
    inline_editable_fields = ["title", "published"] # single-field edit popovers on the list page
    inlines = [CommentInline]                       # nested child forms
    exporters = ["csv", "xlsx"]                     # default: ["csv", "json"]
    importers = ["csv"]                             # default: ["csv", "json"]
    form_layout = [("title", "author"), "content"]  # tuple = shared row

    # Permission hooks (all default to True): is_accessible, can_create, can_edit,
    # can_delete, can_view_detail, can_export, can_import, can_access_field

    # Lifecycle hooks: before/after_create, before/after_edit, before/after_delete,
    # after_create_committed, after_edit_committed, after_delete_committed
```

Registration accepts naming overrides: `admin.add_view(PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article", icon="fa fa-newspaper"))`. When a related view uses a custom `key`, declare the relation manually: `HasOne("author", key="custom-key")` / `HasMany("books", key="...")`.

## Field type quick map

| Data | Field |
| --- | --- |
| Short text / long text / rich text | `StringField`, `TextAreaField`, `TinyMCEEditorField` (tinymce extra) |
| Formatted strings | `EmailField`, `URLField`, `UUIDField`, `IPAddressField`, `PhoneField`, `ColorField`, `PasswordField`, `SlugField(populate_from=...)` |
| Numbers | `IntegerField(min, max, step)`, `DecimalField`, `FloatField` (plain text input, no min/max) |
| Boolean | `BooleanField` |
| Date/time | `DateField`, `DateTimeField(output_format=...)`, `TimeField`, `ArrowField` (arrow extra) |
| Choices | `EnumField(enum= / choices= / choices_loader=, multiple=)`, `TimeZoneField`, `CountryField`, `CurrencyField` (i18n extra) |
| Collections | `TagsField` (free strings), `ListField(inner_field)`, `CollectionField(fields=[...])` (nested object) |
| JSON | `JSONField(validation_schema=...)` |
| Derived read-only | `ComputedField(getter=...)` or subclass and override `parse_obj()` |
| Files | `FileField`, `ImageField` (both take `storage=`, `upload_folder=`, `accept=`, `max_size=`, `multiple=`, `validators=`) |
| Relations | `HasOne`, `HasMany` (auto-detected from ORM relationships) |

Common attributes on every field: `label`, `help_text`, `required`, `disabled`, `read_only`, `default` (static, zero-arg callable, or `(request) -> value`), `getter` (`(request, obj) -> value`, overrides the default `getattr` lookup in `parse_obj`), `formatter` (`dict[RequestAction, (request, value) -> value]`, replaces `serialize_value`/`serialize_none_value` per action; its return value is used as-is), `parser` (`dict[RequestAction, (request, raw) -> value]`, replaces the field's default form/import parsing per action), `validators`, `searchable`, `orderable`, `filters`, `exclude_from_*` flags, and `extra` (free metadata dict the framework never touches).

Server-side validation: pass `validators=[...]` on any field. A validator is a sync or async callable `(request, field, value, form_values)` that raises `ValueError` to reject the value; `form_values` is the full parsed submission keyed by field name, so a validator can read other fields' values. Built-in factories live in `starlette_admin.validators`: `length`, `number_range`, `regexp`, `email`, `url`, `uuid`, `ip_address`, `any_of`, `none_of`, `file_size`, `file_type`, `valid_image`. Empty values are only checked against `required`; rules that reject across multiple fields go in the view's `validate()` override. Details in [references/fields.md](references/fields.md).

## Task router

Read the reference that matches the task before writing code:

| Task | Reference |
| --- | --- |
| ModelView options, relations, object repr, inline forms, inline edit, form layout | [references/views.md](references/views.md) |
| Login, OAuth/OIDC, roles, per-field and per-action permissions | [references/auth.md](references/auth.md) |
| Batch/row actions, lifecycle hooks, global events, flash messages | [references/actions-events.md](references/actions-events.md) |
| List filters, filter URL format, custom `BaseFilter` | [references/filters.md](references/filters.md) |
| File uploads, storage backends, export and import | [references/files-export-import.md](references/files-export-import.md) |
| Dashboards, `CustomView`, widgets, custom routes and templates | [references/dashboards.md](references/dashboards.md) |
| Admin constructor, backends and sessions, security, i18n, themes, deployment | [references/admin-config.md](references/admin-config.md) |
| Field validators, custom field types, converter registry | [references/fields.md](references/fields.md) |

Upgrading an app from starlette-admin 0.17.x to 1.0.0 is covered by the separate `starlette-admin-migration` skill.

When working inside the starlette-admin repository itself, the full documentation lives in `docs/` and runnable apps in `examples/` (numbered 01-16 plus `examples/advanced/`). Each example runs with `cd examples/<name> && uv run app.py`.
