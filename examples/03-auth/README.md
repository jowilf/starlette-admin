# 03: Authentication & Authorization

This example shows how to secure the admin interface with username/password authentication
and role-based access control.

## Users

| Username | Password | Roles |
|----------|----------|-------|
| `admin`  | `password` | read, create, edit, delete, make_published action |
| `editor` | `password` | read, create, edit, make_published action |
| `viewer` | `password` | read only |

## What it demonstrates

- **`AuthProvider`**: implement `login`, `authenticate`, and `logout`
- **`SessionMiddleware`**: session-based auth state
- **Role-based permissions**: `can_view_detail`, `can_create`, `can_edit`, `can_delete`
- **Action-level authorization**: `is_action_allowed` per batch action

## Running

```shell
cd examples/03-auth
uv run app.py
```

Open <http://localhost:8000> and follow the link to the admin.
The SQLite database is created and seeded with 10 sample articles on first run.
