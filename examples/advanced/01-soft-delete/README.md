# Advanced 01: Soft Delete (SQLAlchemy)

Demonstrates soft delete: "deleting" a record marks it with a `deleted_at` timestamp rather than removing it from the database. A separate Trash view lets you restore or permanently purge those records.

## What it shows

### `PostView`: active posts

- **`get_list_query` / `get_count_query` / `get_detail_query`** filtered to `deleted_at IS NULL`, so soft-deleted rows never appear in the list, count, or detail page.
- **`delete()` override**: instead of issuing a SQL `DELETE`, it sets `deleted_at = datetime.utcnow()` on each selected row and commits. The built-in delete action and row-level delete button both call this method, so no extra wiring is needed.

### `TrashView`: deleted posts

- Same `Post` model, different `key` (`"trash"`), so starlette-admin treats it as a separate resource with its own URL.
- **`get_list_query` / `get_count_query` / `get_detail_query`** filtered to `deleted_at IS NOT NULL`.
- **`can_create` / `can_edit`** return `False`: trash rows cannot be created or edited directly.
- **`restore` action**: clears `deleted_at` on the selected rows so they reappear in `PostView`.
- **`delete` action** (built-in, kept in `actions`): performs a real `DELETE` from the database (permanent purge).

## Models

| Model | Key fields |
|---|---|
| `Post` | `id`, `title`, `body`, `created_at`, `deleted_at` |

`deleted_at` is `NULL` for live posts and set to the deletion timestamp for soft-deleted ones. Two posts start in the trash on first run.

## Run

```bash
cd examples/advanced/01-soft-delete
uv run app.py
```

Then open <http://localhost:8000/admin/>.

- **Posts**: select one or more rows and click **Delete**. The rows disappear from this list.
- **Trash**: the deleted posts appear here. Select them and use **Restore** to bring them back, or **Delete** to purge them permanently.
