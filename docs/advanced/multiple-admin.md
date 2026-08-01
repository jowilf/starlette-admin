---
title: Multiple Admin Instances
description: Mount multiple isolated admin dashboards on a single FastAPI application for different user roles or domains.
---

# Multiple Admin Instances

Every `Admin` instance you construct acts as a self-contained Starlette sub-application. You can mount as many instances as you need, and each can maintain its own `base_url`, `route_name`, authentication provider, and views.

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

In this example, visiting `/staff` displays a login page secured by `StaffAuth`, while visiting `/root` displays a separate login page secured by `SuperAdminAuth`. Logging into one interface does not grant access to the other. Because each `SessionMiddleware` signs its cookie with a unique `secret_key`, each `Admin` instance only reads the session data written by its corresponding authentication provider.

## `base_url` and `route_name`

Both `base_url` and `route_name` are constructor parameters for the `Admin` and `BaseAdmin` classes (located in `starlette_admin/base.py`). They default to `/admin` and `"admin"`, respectively:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** determines the path prefix where the admin interface is mounted. Because this value is passed directly to the internal `app.mount(self.base_url, app=admin_app, name=self.route_name)` call, it must be unique for each admin instance. Otherwise, one mount will shadow the other.
* **`route_name`** defines the name Starlette uses to register the mount. Every generated URL within the admin interface (including lists, details, edits, exports, and static assets) is built by calling `request.url_for(route_name + ":list", ...)`. Additionally, every page template reads `request.app.state.ROUTE_NAME` to determine the correct route name prefix for link building.

Calling `mount_to` builds a fresh Starlette sub-application for each admin instance. As a result, middleware, routes, and template globals remain fully isolated. The `Admin` class is not a process-wide singleton, meaning you can construct as many independent instances as your application requires.

!!! warning
    Give every `Admin` a distinct `route_name`. Starlette's router resolves `url_for("admin:list", ...)` by matching the mount **name**. If two admins share the same `route_name`, the parent application will have two mounts registered under identical names. Consequently, `url_for` will resolve to whichever mount Starlette matches first. This can cause every internal link in the second admin (such as edit links, static assets, or export endpoints) to silently point to the first admin's `base_url` instead of its own.

## Sharing Views vs. Defining Separate Views

The `add_view` method accepts a view instance and mutates it during setup. For a `BaseModelView`, the setup process binds internal callbacks specifically to the admin instance it is registered with. For example, it configures how `HasOne` and `HasMany` fields resolve related-record links.

If you register the exact same view **instance** on two different admins, the second `add_view` call will overwrite these callbacks. As a result, relation links on the first admin's pages will incorrectly resolve against the second admin's views and URLs.

To prevent this, always register a fresh instance of the `ModelView` **class** for each admin. The class itself carries no admin-specific state, only the instantiated objects do:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

If you need distinct behavior for each admin interface (such as different visibility rules or `can_delete` permissions), create dedicated subclasses rather than relying on runtime overrides:

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

## What's Next

* **[Authentication](../user-guide/auth.md):** The complete `AuthProvider` and `OAuthProvider` contract.
* **[Extension Points](extension-points.md):** Every other pluggable surface available on the `Admin` class.
* **[Quickstart](../getting-started/quickstart.md):** The foundational single-admin setup this guide builds upon.
