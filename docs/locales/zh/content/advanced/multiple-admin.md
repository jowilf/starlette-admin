---
title: 多个 Admin 实例
description: 在单个 FastAPI 应用上挂载多个相互隔离的管理后台，以服务不同的用户角色或业务领域。
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# 多个 Admin 实例

你构造的每个 `Admin` 实例都是一个自包含的 Starlette 子应用。可以按需挂载任意数量的实例，每个实例都拥有自己的 `base_url`、`route_name`、认证提供方和视图。

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

在此示例中，`/staff` 显示一个由 `StaffAuth` 支持的登录页面，`/root` 则显示另一个由 `SuperAdminAuth` 支持的独立登录页面。登录其中之一并不会获得对另一个的访问权限：每个 `SessionMiddleware` 都使用自己的 `secret_key` 对 Cookie 签名，因此每个 `Admin` 实例只会读取由自身认证提供方写入的会话数据。

## `base_url` 与 `route_name`

`base_url` 和 `route_name` 是 `starlette_admin/base.py` 中 `Admin` 和 `BaseAdmin` 类的构造参数。它们分别默认为 `/admin` 和 `"admin"`：

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** 设置管理后台挂载所在的路径前缀。它会直接传入内部的 `app.mount(self.base_url, app=admin_app, name=self.route_name)` 调用，因此在各实例之间必须唯一，否则一个挂载会遮蔽另一个。
* **`route_name`** 是 Starlette 注册该挂载时使用的名称。管理后台生成的所有 URL——包括列表、详情、编辑、导出和静态资源——都来自 `request.url_for(route_name + ":list", ...)`，并且每个页面模板都会读取 `request.app.state.ROUTE_NAME` 来获取构建链接所需的正确前缀。

`mount_to` 会为每个 Admin 实例构建一个全新的 Starlette 子应用，因此中间件、路由和模板全局变量彼此隔离。`Admin` 并不是进程级单例：可以根据应用的需要构造任意多个独立实例。

!!! warning
    为每个 `Admin` 设置不同的 `route_name`。Starlette 的路由通过匹配挂载**名称**来解析 `url_for("admin:list", ...)`，因此两个共用同一 `route_name` 的管理后台会让父应用中存在两个同名挂载，`url_for` 会解析到 Starlette 先匹配到的那个。于是第二个管理后台中的所有内部链接——包括编辑链接、静态资源和导出端点——都会悄然指向第一个管理后台的 `base_url`。

## 共享视图与定义独立视图

`add_view` 接收一个视图实例，并在设置过程中对其进行修改。对于 `BaseModelView`，该设置过程会把内部回调绑定到它注册所在的 Admin，包括 `HasOne` 和 `HasMany` 字段如何解析关联记录的链接。

如果在两个管理后台上注册同一个视图**实例**，第二次 `add_view` 调用会覆盖这些回调，导致第一个管理后台页面上的关联链接按照第二个管理后台的视图和 URL 解析。

为避免这种情况，应给每个管理后台提供一个全新的 `ModelView` **类**实例。类本身不持有任何与管理后台相关的状态，只有实例才会持有：

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(
    ModelView(Order)
)  # separate instance of the same class; this is safe
```

当两个管理后台需要不同的行为时，例如不同的可见性规则或 `can_delete` 权限，应为每个后台编写各自的子类，而不是在运行时修补共享实例：

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

## 后续步骤

* **[认证](../user-guide/auth.md)**：完整的 `AuthProvider` 和 `OAuthProvider` 契约。
* **[扩展点](extension-points.md)**：`Admin` 类上其余全部可插拔扩展点。
* **[快速入门](../getting-started/quickstart.md)**：本指南所基于的单管理后台基础配置。
