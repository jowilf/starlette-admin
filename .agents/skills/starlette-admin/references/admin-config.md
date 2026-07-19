# Admin configuration, backends, security, and deployment

## Admin constructor reference

All settings are keyword arguments; SQLAlchemy/SQLModel additionally take `session_provider` as the first positional argument (`Engine`, `AsyncEngine`, `sessionmaker`, or `async_sessionmaker`).

| Parameter | Default | Purpose |
| --- | --- | --- |
| `title` | `"Admin"` | Navbar text and page title |
| `logo_url`, `login_logo_url`, `favicon_url` | `None` | Branding; each accepts a URL string or `(request) -> str or None` callable (multi-tenant branding) |
| `base_url` | `"/admin"` | Mount prefix |
| `route_name` | `"admin"` | Starlette mount name; internal links use `url_for(route_name + ":list", ...)` |
| `templates_dir` | `"templates"` | Override directory checked before built-in templates |
| `static_dir` | `None` | Extra static files served alongside built-ins |
| `theme` | `ThemeSettings()` | Bootstrap/Tabler theme, see below |
| `index_view` | `DefaultIndexView` | Home page, see [dashboards.md](dashboards.md) |
| `auth_provider` | `None` (public!) | See [auth.md](auth.md) |
| `secret_key` | random + warning | Signs CSRF and flash cookies; always set explicitly |
| `middlewares` | `None` | Extra Starlette middleware on top of the built-in CSRF/flash/auth stack |
| `export_config`, `import_config` | defaults | Caps, see [files-export-import.md](files-export-import.md) |
| `i18n_config` | `None` (English) | UI translations, see below |
| `timezone_config` | `TimezoneConfig()` (ON) | Datetime display conversion, see below |
| `debug` | `False` | Verbose colored DEBUG logging for the `starlette_admin` package (middleware, view resolution, permission decisions); dev only |

Lifecycle: create `Admin`, `add_view(...)` for every view, then `mount_to(app)` exactly once. The admin locks after mounting.

## SQLAlchemy backend specifics

- `DBSessionMiddleware` opens one session per request on `request.state.session`: `AsyncSession` for async engines, `Session` for sync (sync calls are routed through a thread to avoid blocking the event loop).
- One commit per request: never call `session.commit()`; `flush()` is enough. The middleware commits on 2xx/3xx responses and rolls back on exceptions and on responses with status >= 400 (such as form validation failures).
- Pass a `sessionmaker`/`async_sessionmaker` as `session_provider` when the session needs configuration (for example `autoflush=False`).
- Unset `fields` exposes every model attribute in declaration order. Python-side column defaults (`default=0`, `default=datetime.utcnow`) pre-fill create forms; `server_default` and primary keys do not.
- Relationships convert automatically: many-to-one/one-to-one to `HasOne`, one-to-many/many-to-many to `HasMany`, loaded lazily via a relation-lookup endpoint.
- Composite primary keys work out of the box (`examples/12-sqla-composite-pks`).

### SQLModel

`starlette_admin.contrib.sqlmodel` re-exports the sqla backend and adds Pydantic validation: `validate()` runs `model.model_validate(data)`, so `Field(min_length=...)` and `@field_validator` rules surface as per-field form errors. File and relationship fields are excluded from that validation. Example: `examples/14-sqlmodel`.

### Plain SQLAlchemy + Pydantic validation

`starlette_admin.contrib.sqla.ext.pydantic.ModelView` takes `pydantic_model=` to validate form data against a separate schema: `admin.add_view(ModelView(User, pydantic_model=UserIn))`. Example: `examples/11-sqla-pydantic-fastapi`.

## MongoDB backends

- **Beanie** (`contrib.beanie`): async Pydantic documents. Call `await init_beanie(database=..., document_models=[...])` in the app lifespan before mounting traffic. Pydantic validation errors map to form errors; MongoDB full-text search is supported. `Admin()` takes no connection argument.
- **MongoEngine** (`contrib.mongoengine`): sync Django-style documents. Call `me.connect(...)` in the lifespan. GridFS-backed `FileField`/`ImageField` work with no `storage=` configuration; `mount_to` registers the GridFS file route.

Examples: `examples/15-beanie`, `examples/16-mongoengine`. A custom backend implements the `BaseModelView` contract (see `docs/integrations/custom-backend.md` and `examples/advanced/03-custom-backend`).

## Security defaults

Automatic: CSRF double-submit cookie on every form and jQuery AJAX call, signed flash cookie (no SessionMiddleware needed for flash), filename sanitization on uploads, Pillow image verification on `ImageField`, 100k-row export cap, spreadsheet formula escaping, 10 MB import cap.

Your responsibility: HTTPS, an `auth_provider` (the admin is public without one), network exposure, dependency updates, and the `can_*`/`is_accessible` permission checks. Custom forms in your own templates must render `{{ csrf_input(request) }}`.

## Internationalization and timezones

```python
from starlette_admin import I18nConfig, TimezoneConfig
from starlette_admin.i18n import SUPPORTED_LOCALES

admin = Admin(
    engine,
    i18n_config=I18nConfig(default_locale="en", language_switcher=SUPPORTED_LOCALES),
    timezone_config=TimezoneConfig(
        default_timezone="UTC",
        database_timezone="UTC",
        timezone_switcher=["UTC", "Europe/Paris", "America/New_York"],
    ),
    secret_key="...",
)
```

- i18n needs `starlette-admin[i18n]` (Babel). Locale resolution order: language cookie, `Accept-Language` header, `default_locale`. Supported locales include de, en, fr, pt, ru, tr, zh-Hans, zh-Hant.
- Timezone conversion is ON by default even without config: naive datetimes are assumed to be `database_timezone` (UTC) and displayed in the viewer's timezone (cookie-detected, switcher-set). Form submissions convert back to `database_timezone` before hitting the model. Set `timezone_switcher=None` plus `default_timezone` to force one timezone for everyone.

Example: `examples/10-i18n-timezone`.

## Themes

```python
from starlette_admin import ThemeSettings

admin = Admin(engine, theme=ThemeSettings(base="slate", primary="blue", radius=2, mode="dark"))
```

`mode`: light/dark. `base`: slate, gray, zinc, neutral, stone, pink. `primary`: blue, azure, indigo, purple, pink, red, orange, yellow, lime, green, teal, cyan, inverted. `radius`: 0 to 2 in 0.5 steps. For deeper changes use `templates_dir` (files shadow built-ins at the same relative path) and `static_dir`. Example: `examples/08-themes`.

## Multiple admin instances

Each `Admin` is independent and can have its own auth provider and views. Distinct `base_url` AND `route_name` are mandatory, otherwise links from one admin resolve into the other:

```python
staff_admin = Admin(engine, base_url="/staff", route_name="staff-admin", ...)
root_admin = Admin(engine, base_url="/root", route_name="root-admin", ...)
staff_admin.mount_to(app)
root_admin.mount_to(app)
```

## Deployment

- Set `secret_key` from an environment variable; the auto-generated key differs per worker and breaks CSRF under multiple workers.
- Behind a TLS-terminating proxy, forward `X-Forwarded-Proto` (and `Host`, `X-Forwarded-For`) and run uvicorn with `--proxy-headers --forwarded-allow-ips=<proxy-ip>`, otherwise every generated link downgrades to `http://` and browsers block it.
- Limit request body size at the web server (nginx `client_max_body_size`); the admin's `max_size`/`max_upload_size` checks run only after the request reaches the app.
