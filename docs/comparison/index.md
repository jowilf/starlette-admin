# Comparing starlette-admin, Django Admin, and Flask-Admin

Django Admin, Flask-Admin, and starlette-admin all solve the same core problem: they generate a production-ready administrative interface directly from your data models. This eliminates the need to write CRUD screens by hand. They differ primarily in their target web stacks, supported ORMs, and the balance of built-in features versus developer customization.

This page provides a comprehensive comparison. If you are already familiar with Django Admin or Flask-Admin and want a direct API translation, refer to the relevant migration guide:

* [Coming from Django Admin](django-admin.md)
* [Coming from Flask-Admin](flask-admin.md)

## Positioning at a Glance

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Web framework** | Django only | Flask only | Starlette, FastAPI, and any ASGI app capable of mounting sub-applications |
| **Execution model** | Sync (WSGI-first) | Sync (WSGI) | Async-first (ASGI) |
| **Data layer** | Django ORM only | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM, or a [custom backend](../integrations/custom-backend.md) |
| **UI toolkit** | Django templates, classic admin theme | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), dark mode, [custom themes](../advanced/custom-themes.md) |
| **Included with framework** | Yes, part of Django | No, separate package | No, separate package |
| **Authentication** | Built in via `django.contrib.auth` | Bring your own (`is_accessible`) | Pluggable [`AuthProvider` / `OAuthProvider](../user-guide/auth.md)`, bring your own user store |

## When Each Framework Fits

### Django Admin

This is the ideal choice for native Django applications. It is mature and deeply integrated with `django.contrib.auth`. It provides users, groups, per-model permissions, and change history with zero configuration. However, it cannot be used outside of the Django ecosystem.

### Flask-Admin

This library brought the auto-generation concept to Flask and popularized the `ModelView` configuration style. It remains synchronous and strictly tied to Flask. This limitation is significant if you are building on a modern asynchronous stack.

### starlette-admin

This package targets the modern asynchronous Python stack. If your application uses FastAPI or Starlette, it mounts directly onto your app and runs natively on the async event loop. It supports both SQL and NoSQL data layers. It borrows the intuitive `ModelView` configuration from Flask-Admin while covering the feature depth expected by Django Admin users. This includes inlines, batch actions, per-request permissions, and internationalization.

## Feature Matrix

**Legend:**

* **Yes:** Built in
* **Partial:** Possible via third-party packages or custom code
* **No:** Not available

| Feature | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Auto-generated CRUD views | **Yes** | **Yes** | **Yes** |
| Full-text search | **Yes** `search_fields` | **Yes** `column_searchable_list` | **Yes** [`searchable_fields`](../user-guide/filters.md) |
| Column filters | **Yes** `list_filter` | **Yes** `column_filters` | **Yes** [Visual filter builder](../user-guide/filters.md) with `AND`/`OR` groups |
| Sorting and default ordering | **Yes** | **Yes** | **Yes** [`sortable_fields`, `fields_default_sort](../user-guide/views.md#search-sort)` |
| Inline editing in list view | **Yes** `list_editable` | **Yes** `column_editable_list` | **Yes** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Related-model inline forms | **Yes** `TabularInline` / `StackedInline` | **Yes** `inline_models` | **Yes** [`InlineModelView`](../user-guide/inline-forms.md) |
| Batch actions | **Yes** `actions` | **Yes** `@action` | **Yes** [`@action`](../user-guide/actions.md) with confirmation dialogs and custom forms |
| Per-row actions | **Partial** custom templates | **Partial** custom formatters | **Yes** [`@row_action`, `@link_row_action](../user-guide/actions.md%23row-actions)` |
| Data export | **Partial** `django-import-export` | **Yes** CSV and others | **Yes** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Data import | **Partial** `django-import-export` | **No** | **Yes** [CSV, JSON, Excel](../user-guide/export-import.md) with dry-run validation |
| File and image uploads | **Yes** `FileField` / `ImageField` | **Partial** requires extra setup | **Yes** [Local and S3 storage](../user-guide/file-storage.md) |
| Dashboard widgets | **Partial** third-party themes | **Partial** custom index view | **Yes** [Built-in widget system](../user-guide/custom-views.md) |
| Custom standalone pages | **Yes** custom `AdminSite` URLs | **Yes** `BaseView` + `@expose` | **Yes** [`CustomView`](../user-guide/custom-views.md) |
| Form layout control | **Yes** `fieldsets` | **Yes** `form_rules` | **Yes** [`form_layout`](../advanced/form-layout.md) with tabs and grids |
| Authentication | **Yes** `django.contrib.auth` | **No** bring your own | **Yes** [`AuthProvider`](../user-guide/auth.md) or `OAuthProvider` |
| Per-model permissions | **Yes** permission framework | **Yes** override `can_*` flags | **Yes** [per-request methods](../user-guide/views.md%23security-authorization) |
| Per-field permissions | **Partial** `get_readonly_fields` | **No** | **Yes** [`can_access_field`](../user-guide/views.md%23security-authorization) |
| Lifecycle hooks | **Yes** `save_model`, signals | **Yes** `on_model_change` | **Yes** [Lifecycle hooks](../user-guide/views.md%23lifecycle-hooks) and [events](../advanced/events.md) |
| CSRF protection | **Yes** Django middleware | **Yes** via Flask-WTF | **Yes** [Built into `Admin](../user-guide/security.md)` |
| Change history / audit log | **Yes** `LogEntry` | **No** | **Partial** build using [events](../advanced/events.md) |
| Internationalization | **Yes** | **Yes** via Flask-Babel | **Yes** [`I18nConfig`](../user-guide/i18n.md) |
| Multiple admin instances | **Yes** multiple `AdminSite`s | **Yes** | **Yes** [Multiple `Admin` mounts](../advanced/multiple-admin.md) |
| Async ORM support | **Partial** | **No** | **Yes** async SQLAlchemy, Beanie, Tortoise ORM |

## Trade-Offs

A fair technical evaluation must acknowledge areas where other tools excel.

* **Complete user system:** Django Admin includes a comprehensive user system out of the box. Users, groups, permissions, and password management are handled by `django.contrib.auth` automatically. starlette-admin requires you to implement `authenticate()` against your own data store. This demands more initial setup but provides greater architectural flexibility later.
* **Automated change history:** Django Admin automatically records change history via `LogEntry`. In starlette-admin, you must build your own audit trail by subscribing to lifecycle [events](../advanced/events.md). This only requires a few lines of code, but it is not automatic.
* **Third-party ecosystem:** Django Admin benefits from a massive ecosystem of third-party packages for themes, widgets, and data workflows. While starlette-admin includes many of these features natively, highly specialized niche extensions might not yet exist.
* **File management:** Flask-Admin provides `FileAdmin`, a dedicated server file-system browser. starlette-admin handles files attached directly to model fields via [local disk or S3](../user-guide/file-storage.md), but it does not include a generalized server file manager.

## Next Steps

* Migrating from Django? Read [Coming from Django Admin](django-admin.md).
* Migrating from Flask-Admin? Read [Coming from Flask-Admin](flask-admin.md).
* Starting fresh? The [Quickstart](../getting-started/quickstart.md) will help you build a working admin interface in minutes.
