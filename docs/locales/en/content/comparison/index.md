---
title: Comparing starlette-admin, Django Admin, and Flask-Admin
description: A side-by-side comparison of starlette-admin, Django Admin, and Flask-Admin covering web stacks, supported ORMs, feature depth, and trade-offs.
---

# Comparing starlette-admin, Django Admin, and Flask-Admin

Django Admin, Flask-Admin, and starlette-admin solve the same problem: they generate a production-ready admin interface from your data models, so you don't write CRUD screens by hand. They differ in the web stacks they target, the ORMs they support, and how much they build in versus leave to you.

This page compares the three. If you already know Django Admin or Flask-Admin and want a direct API translation, go to the matching migration guide:

* [Coming from Django Admin](django-admin.md)
* [Coming from Flask-Admin](flask-admin.md)

## Positioning at a glance

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Web framework** | Django only | Flask only | Starlette, FastAPI, and any ASGI app that can mount sub-applications |
| **Execution model** | Sync (WSGI-first) | Sync (WSGI) | Async-first (ASGI) |
| **Data layer** | Django ORM only | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM, or a [custom backend](../integrations/custom-backend.md) |
| **UI toolkit** | Django templates, classic admin theme | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), dark mode, [custom themes](../advanced/custom-themes.md) |
| **Included with framework** | Yes, part of Django | No, separate package | No, separate package |
| **Authentication** | Built in through `django.contrib.auth` | Bring your own (`is_accessible`) | Pluggable [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md), bring your own user store |

## When each framework fits

### Django Admin

Django Admin fits native Django applications. It's mature and integrates with `django.contrib.auth`, so you get users, groups, per-model permissions, and change history with no configuration. It runs only inside Django.

### Flask-Admin

Flask-Admin brought auto-generation to Flask and popularized the `ModelView` configuration style. It's synchronous and tied to Flask, so it doesn't run on an async stack.

### starlette-admin

starlette-admin targets the async Python stack. If your application uses FastAPI or Starlette, you mount the admin on your app and it runs on the same event loop. It works with SQL and NoSQL data layers, keeps the `ModelView` configuration style from Flask-Admin, and covers the feature depth Django Admin users expect: inlines, batch actions, per-request permissions, and internationalization.

## Feature matrix

**Legend:**

* **Yes:** Built in
* **Partial:** Possible through third-party packages or custom code
* **No:** Not available

| Feature | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Auto-generated CRUD views | **Yes** | **Yes** | **Yes** |
| Full-text search | **Yes** `search_fields` | **Yes** `column_searchable_list` | **Yes** [`searchable_fields`](../user-guide/filters.md) |
| Column filters | **Yes** `list_filter` | **Yes** `column_filters` | **Yes** [Visual filter builder](../user-guide/filters.md) with `AND`/`OR` groups |
| Sorting and default ordering | **Yes** | **Yes** | **Yes** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#search-and-sort) |
| Inline editing in list view | **Yes** `list_editable` | **Yes** `column_editable_list` | **Yes** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Related-model inline forms | **Yes** `TabularInline` / `StackedInline` | **Yes** `inline_models` | **Yes** [`InlineModelView`](../user-guide/inline-forms.md) |
| Batch actions | **Yes** `actions` | **Yes** `@action` | **Yes** [`@action`](../user-guide/actions.md) with confirmation dialogs and custom forms |
| Per-row actions | **Partial** custom templates | **Partial** custom formatters | **Yes** [`@row_action`, `@link_row_action`](../user-guide/actions.md#row-actions) |
| Data export | **Partial** `django-import-export` | **Yes** CSV and others | **Yes** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Data import | **Partial** `django-import-export` | **No** | **Yes** [CSV, JSON, Excel](../user-guide/export-import.md) with preview validation and upsert |
| File and image uploads | **Yes** `FileField` / `ImageField` | **Partial** needs extra setup | **Yes** [Local and S3 storage](../user-guide/file-storage.md) |
| Dashboard widgets | **Partial** third-party themes | **Partial** custom index view | **Yes** [Built-in widget system](../user-guide/custom-views.md) |
| Custom standalone pages | **Yes** custom `AdminSite` URLs | **Yes** `BaseView` + `@expose` | **Yes** [`CustomView`](../user-guide/custom-views.md) |
| Form layout control | **Yes** `fieldsets` | **Yes** `form_rules` | **Yes** [`form_layout`](../advanced/form-layout.md) with tabs and grids |
| Authentication | **Yes** `django.contrib.auth` | **No** bring your own | **Yes** [`AuthProvider`](../user-guide/auth.md) or `OAuthProvider` |
| Per-model permissions | **Yes** permission framework | **Yes** override `can_*` flags | **Yes** [per-request methods](../user-guide/views.md#security-and-authorization) |
| Per-field permissions | **Partial** `get_readonly_fields` | **No** | **Yes** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| Lifecycle hooks | **Yes** `save_model`, signals | **Yes** `on_model_change` | **Yes** [Lifecycle hooks](../user-guide/views.md#lifecycle-hooks) and [events](../advanced/events.md) |
| CSRF protection | **Yes** Django middleware | **Yes** through Flask-WTF | **Yes** [Built into `Admin`](../user-guide/security.md) |
| Change history / audit log | **Yes** `LogEntry` | **No** | **Partial** build your own with [events](../advanced/events.md) |
| Internationalization | **Yes** | **Yes** through Flask-Babel | **Yes** [`I18nConfig`](../user-guide/i18n.md) |
| Multiple admin instances | **Yes** multiple `AdminSite`s | **Yes** | **Yes** [Multiple `Admin` mounts](../advanced/multiple-admin.md) |
| Async ORM support | **Partial** | **No** | **Yes** async SQLAlchemy, Beanie, Tortoise ORM |

## Trade-offs

* **Complete user system:** Django Admin ships a full user system. `django.contrib.auth` handles users, groups, permissions, and password management for you. In starlette-admin, you implement `authenticate()` against your own data store, which is more setup at the start and more architectural freedom later.
* **Automated change history:** Django Admin records change history in `LogEntry`. In starlette-admin, you build the audit trail yourself by subscribing to lifecycle [events](../advanced/events.md). It takes a few lines of code, but it isn't automatic.
* **Third-party ecosystem:** Django Admin has a large ecosystem of third-party packages for themes, widgets, and data workflows. starlette-admin covers many of those features natively, but a niche extension you depend on might not exist yet.
* **File management:** Flask-Admin ships `FileAdmin`, a browser for the server file system. starlette-admin handles files attached to model fields through [local disk or S3](../user-guide/file-storage.md), and it has no general-purpose server file browser.

## Next steps

* Moving from Django? Read [Coming from Django Admin](django-admin.md).
* Moving from Flask-Admin? Read [Coming from Flask-Admin](flask-admin.md).
* Starting fresh? The [Quickstart](../getting-started/quickstart.md) gets you a working admin interface in minutes.
