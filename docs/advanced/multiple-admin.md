---
title: Multiple Admin Instances
description: Mount multiple isolated admin dashboards on a single FastAPI application for different user roles or domains.
---

# Multiple Admin Instances

Every `Admin` instance you construct is a self-contained Starlette sub-application. Mount as many as you need, each with its own `base_url`, `route_name`, authentication provider, and views.

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Order, Post, User

engine = create_engine("sqlite:///app.sqlite")
app = Starlette()

STAFF = {"staff": "staffpass"}
SUPERADMINS = {"root": "rootpass"}


class StaffAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if STAFF.get(username) == password:
            request.session["user"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("user")
        return AdminUser(username=username) if username in STAFF else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


class SuperAdminAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if SUPERADMINS.get(username) == password:
            request.session["user"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("user")
        return AdminUser(username=username) if username in SUPERADMINS else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


staff_admin = Admin(
    engine,
    title="Staff Admin",
    base_url="/staff",
    route_name="staff_admin",
    auth_provider=StaffAuth(),
    secret_key="staff-secret-change-me",
    middlewares=[Middleware(SessionMiddleware, secret_key="staff-secret-change-me")],
)
staff_admin.add_view(ModelView(Order))
staff_admin.add_view(ModelView(Post))
staff_admin.mount_to(app)

root_admin = Admin(
    engine,
    title="Super Admin",
    base_url="/root",
    route_name="root_admin",
    auth_provider=SuperAdminAuth(),
    secret_key="root-secret-change-me",
    middlewares=[Middleware(SessionMiddleware, secret_key="root-secret-change-me")],
)
root_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(User))
root_admin.mount_to(app)

```

In this example, `/staff` shows a sign-in page backed by `StaffAuth` and `/root` shows a separate one backed by `SuperAdminAuth`. Signing in to one doesn't grant access to the other: each `SessionMiddleware` signs its cookie with its own `secret_key`, so each `Admin` instance only reads the session data its own authentication provider wrote.

## `base_url` and `route_name`

`base_url` and `route_name` are constructor parameters on the `Admin` and `BaseAdmin` classes in `starlette_admin/base.py`. They default to `/admin` and `"admin"`:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** sets the path prefix the admin mounts at. It goes straight into the internal `app.mount(self.base_url, app=admin_app, name=self.route_name)` call, so it has to be unique per instance. Otherwise one mount shadows the other.
* **`route_name`** is the name Starlette registers the mount under. Every URL the admin generates, for lists, details, edits, exports, and static assets, comes from `request.url_for(route_name + ":list", ...)`, and every page template reads `request.app.state.ROUTE_NAME` to get the right prefix for link building.

`mount_to` builds a fresh Starlette sub-application for each admin instance, so middleware, routes, and template globals stay isolated. `Admin` isn't a process-wide singleton: construct as many independent instances as your application needs.

!!! warning
    Give every `Admin` a distinct `route_name`. Starlette's router resolves `url_for("admin:list", ...)` by matching the mount **name**, so two admins sharing a `route_name` leave the parent application with two mounts under the same name, and `url_for` resolves to whichever one Starlette matches first. Every internal link in the second admin, including edit links, static assets, and export endpoints, then silently points at the first admin's `base_url`.

## Sharing views vs. defining separate views

`add_view` takes a view instance and mutates it during setup. For a `BaseModelView`, that setup binds internal callbacks to the admin it's registered with, including how `HasOne` and `HasMany` fields resolve related-record links.

Register the same view **instance** on two admins and the second `add_view` call overwrites those callbacks, so relation links on the first admin's pages resolve against the second admin's views and URLs.

To avoid this, give each admin a fresh instance of the `ModelView` **class**. The class holds no admin-specific state, only the instances do:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

When the two admins need different behavior, such as different visibility rules or `can_delete` permissions, write a subclass for each instead of patching a shared instance at runtime:

```python
class StaffOrderView(ModelView):
    fields_default_sort = ["-created_at"]

    def can_delete(self, request: Request) -> bool:
        return False


class RootOrderView(ModelView):
    fields_default_sort = ["-created_at"]


staff_admin.add_view(StaffOrderView(Order))
root_admin.add_view(RootOrderView(Order))

```

---

## What's next

* **[Authentication](../user-guide/auth.md):** The complete `AuthProvider` and `OAuthProvider` contract.
* **[Extension Points](extension-points.md):** Every other pluggable surface available on the `Admin` class.
* **[Quickstart](../getting-started/quickstart.md):** The foundational single-admin setup this guide builds upon.
