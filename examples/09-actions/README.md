# 09: Custom Actions (SQLAlchemy)

Demonstrates every action hook that starlette-admin exposes: batch actions (with and without confirmation, with form input, with custom response), row actions, and link row actions.

## What it shows

### Batch actions (`@action`)

| Action | What it demonstrates |
|---|---|
| **Mark as published** | Confirmation dialog, success message |
| **Increase views** | Confirmation + inline form, reads `request.form()` |
| **Always Failed** | Raises `ActionFailed(...)` to show the error banner |
| **No confirmation** | Action runs immediately, no dialog |
| **Redirect** | `custom_response=True`, returns `RedirectResponse` |
| **Redirect with form** | `custom_response=True` + form, redirects with query param |
| **Sync all articles** | `allow_empty_selection=True`, global action runnable with no rows selected |
| **Purge drafts** | `allow_empty_selection=True`, deletes every draft article regardless of selection |
| **Publish all matching** | Reads `selection.filters`/`selection.q` directly, acting on whatever the list page's current filter/search matches instead of the checked rows |

### Row actions (`@row_action`, `@link_row_action`)

| Action | What it demonstrates |
|---|---|
| **Mark as published** | Per-row confirmation dialog; hidden via `is_row_action_allowed_for_obj` once the article is already published |
| **Go to example.com** | `@link_row_action` opens an external URL, no round-trip |

Row actions are rendered as an icon list (`RowActionsDisplayType.ICON_LIST`).

## Model

| Model | Key fields |
|---|---|
| `Article` | `id`, `title`, `body`, `views`, `status` |

`Status` is a `str` enum with values `Draft` (`d`), `Published` (`p`), `Withdrawn` (`w`). Ten sample articles are seeded automatically on first run.

## Run

```bash
cd examples/09-actions
uv run app.py
```

Then open <http://localhost:8000/admin/>.
