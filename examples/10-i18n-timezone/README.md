# 10: Internationalization & Timezone (SQLAlchemy)

Demonstrates `I18nConfig` and `TimezoneConfig`, letting users switch the UI language and their display timezone at runtime.

## What it shows

### `I18nConfig`

- **`default_locale`**: sets the fallback language (`"en"`).
- **`language_switcher`**: populated with `SUPPORTED_LOCALES`, which exposes every locale that starlette-admin ships translations for. The switcher renders in the navbar and persists the choice in the session.

### `TimezoneConfig`

- **`default_timezone`**: the fallback display timezone (`"UTC"` here). Used when `use_user_locale_timezone` is `False`, or when browser detection fails.
- **`database_timezone`**: the timezone in which `DateTime` values are stored in the database (`"UTC"` here). Used to convert values correctly before display.
- **`use_user_locale_timezone`**: defaults to `True`. When enabled, the user's browser-detected local timezone is used on first visit instead of `default_timezone`.
- **`timezone_switcher`**: a curated list of IANA timezone identifiers (`UTC`, `Europe/Paris`, `Europe/Berlin`, …). The switcher appears in the navbar; the chosen timezone is persisted in a cookie (`timezone_cookie_name`, defaults to `"timezone"`) and overrides the browser-detected value on subsequent visits.

The `Post.published_at` column is a naive `DateTime` stored in UTC, which makes it a clear demonstration target: switch to `America/New_York` and the displayed time shifts by the correct offset.

## Models

| Model | Key fields |
|---|---|
| `Author` | `id`, `name` |
| `Post` | `id`, `title`, `body`, `published_at` (DateTime), `author_id` |

## Run

```bash
cd examples/10-i18n-timezone
uv run app.py
```

Then open <http://localhost:8000/admin/>. Use the language and timezone dropdowns in the navbar to try the i18n and timezone features.
