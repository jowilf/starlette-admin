---
title: 认证
description: 使用 AuthProvider 在 starlette-admin 中实现认证，或集成 OAuth 来保护你的管理后台。
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# 认证

你只需实现一个方法，即可保护管理界面：

```python
async def authenticate(request) -> AdminUser | None
```

每个受保护的管理请求都会经过该方法。当它返回一个 `AdminUser` 时，请求即通过认证。当它返回 `None` 时，请求未通过认证，此时由你配置的登录或 OAuth 流程接管。

成功时，返回的 `AdminUser` 会被存入：

```python
request.state.admin_user
```

失败时，请求会被标记为匿名：

```python
request.state.is_anonymous = True
```

这样，公开路由和部分受保护的路由无需启动登录流程，即可区分已认证与未认证的请求。


## 选择认证提供程序

| 提供程序 | 适用场景 | 需要实现的内容 |
| --- | --- | --- |
| `AuthProvider` | 你希望使用内置登录页面，并自行校验凭据。 | `login()`、`logout()`、`authenticate()` |
| `OAuthProvider` | 你希望使用 OAuth2 或 OIDC 重定向流程，例如 Auth0、Okta 或 Google。 | `redirect_to_provider()`、`handle_callback()`、`authenticate()` |

二者均为 `BaseAuthProvider` 的子类，并遵循相同的约定。`authenticate()` 在每个请求上运行，其返回值会成为 `request.state.admin_user`；当它返回 `None` 时，框架会设置 `request.state.is_anonymous = True`。

## `AuthProvider`：内置登录页面

当你希望框架负责渲染并处理登录表单、而由你自行校验凭据时，请使用此提供程序。模板、POST 处理以及重定向均由框架管理。

下面是一个完整的示例：

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin

SECRET = "change-me-in-production"

# Demo user store: replace with a real lookup against your database
USERS = {"admin": {"name": "Administrator", "password": "password"}}


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return AdminUser(username=user["name"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


engine = create_engine("sqlite:///admin.sqlite")
app = Starlette(middleware=[Middleware(SessionMiddleware, secret_key=SECRET)])
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key=SECRET
)
admin.mount_to(app)
```

### 必需的方法

`AuthProvider` 实现三个方法。此处需要 `SessionMiddleware`，因为它会在请求之间持久化用户的登录状态。

#### `login()`

此方法处理表单提交。它接收 `username`、`password`、一个 `remember_me` 布尔值以及当前的 `request`。

* **成功时：**将一个标识符（如用户 ID 或用户名）写入 `request.session`。然后返回 `None` 让框架重定向到 `next` 或管理首页，或者返回一个 `Response` 以重定向到其他位置。
* **失败时：**抛出 `LoginFailed("message")` 以在表单上方显示错误，或抛出 `FormValidationError({"username": "..."})` 将特定字段标记为无效。

#### `authenticate()`

此方法在访问受保护管理路由的*每个*请求上运行。它接收 `request` 对象。

* 读取你在 `login()` 期间保存在 `request.session` 中的标识符。
* 在数据库中查找该用户。
* 当用户存在且有效时，返回一个 `AdminUser` 实例。
* 当用户不存在或未登录时，返回 `None`。

#### `logout()`

此方法处理登出。它接收 `request` 对象，你需要从 `request.session` 中清除用户数据以撤销其访问权。返回 `None` 表示默认重定向到管理首页，或者返回一个 `Response` 以重定向到其他位置。

## `OAuthProvider`：OAuth2/OIDC 重定向流程 {#oauthprovider-oauth2oidc-redirect-flow}


当你将认证委托给外部身份提供方（如 Auth0、Okta、Google 或 Microsoft Entra ID）时，请使用 `OAuthProvider`。

`AuthProvider` 在管理后台内部处理用户名和密码表单，而 `OAuthProvider` 则采用基于重定向的流程：

1. 将用户重定向到身份提供方。
2. 身份提供方对用户进行认证。
3. 身份提供方重定向回你的应用程序。
4. 你的应用程序用回调换取用户的身份信息。
5. `authenticate()` 从会话中恢复该用户。

### 回调 URL 设置（必需）

在实现 `OAuthProvider` 之前，请先在身份提供方的控制台中注册你应用程序的回调 URL。出于安全考虑，OAuth 提供方只会重定向到预先批准的 URL。

#### 回调 URL 示例

```text
https://your-domain.com/admin/oauth/callback
```

#### 本地开发

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    你的实际回调 URL 取决于你的配置。它由挂载 `Admin` 时使用的 `route_name` 加上提供方的 `callback_path` 构成。

    默认配置使用：

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    由此生成的回调 URL 为：

    ```text
    /admin/oauth/callback
    ```

    部署后则为：

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    如果更改挂载前缀或提供方的回调路径，该 URL 也会随之变化，你必须在 OAuth 提供方的配置中同步更新。

### 必需的方法

`OAuthProvider` 采用与 `AuthProvider` 相同的基于会话的模式，但它将登录拆分为一次重定向和一次回调。

#### `redirect_to_provider()`

此方法启动 OAuth 流程。它接收 `request` 和一个生成的 `callback_url`，并且必须返回一个 `Response`，将用户浏览器重定向到你的身份提供方。

#### `handle_callback()`

当浏览器携带授权码从身份提供方返回时，此方法开始运行。它接收 `request`。你需要用授权码换取访问令牌，获取用户资料，并将用户的身份存储到 `request.session` 中。

#### `authenticate()`

与 `AuthProvider` 一样，此方法读取 `handle_callback()` 存储在会话中的内容。当会话包含有效的用户数据时返回一个 `AdminUser`，否则返回 `None`。

#### `logout()`

清除会话数据。若要让用户同时从身份提供方登出（OIDC RP 发起的登出），请重写此方法并返回一个指向提供方结束会话端点的重定向 `Response`，而不是返回 `None`。

下面是一个完整的示例：

```python
import os

from authlib.integrations.starlette_client import OAuth
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette_admin.auth import AdminUser, OAuthProvider

AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-auth0-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-auth0-client-secret")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
)


class Auth0Provider(OAuthProvider):
    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        client = oauth.create_client("auth0")
        return await client.authorize_redirect(request, callback_url)

    async def handle_callback(self, request: Request) -> None:
        client = oauth.create_client("auth0")
        token = await client.authorize_access_token(request)
        request.session["user"] = dict(token["userinfo"])

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = request.session.get("user")
        if user:
            return AdminUser(username=user["name"], photo_url=user.get("picture"))
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()
        client = oauth.create_client("auth0")
        metadata = await client.load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        if end_session_endpoint:
            logout_url = str(
                URL(end_session_endpoint).include_query_params(
                    post_logout_redirect_uri="https://www.google.com/",
                    client_id=AUTH0_CLIENT_ID,
                )
            )
            return RedirectResponse(logout_url, status_code=HTTP_303_SEE_OTHER)
        return None


SECRET_KEY = "change-me"
engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
# required because Auth0Provider's handle_callback/authenticate methods use request.session
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

admin = Admin(
    engine, title="My Admin", auth_provider=Auth0Provider(), secret_key=SECRET_KEY
)
admin.mount_to(app)
```

## 注册提供程序

实现认证提供程序后，将其附加到 `Admin` 实例上。

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

仅这一行就完成了全部集成。`Admin` 会将提供程序的 `AuthMiddleware` 挂载到每个管理路由之前，并在管理前缀内添加提供程序的路由（登录、登出以及 `OAuthProvider` 的回调）。

## 权限检查

认证回答“这是谁？”权限回答“他们能做什么？”权限属于视图。基于角色的访问控制分为三步：

1. 继承 `AdminUser`（一个普通的数据类），添加一个 `roles` 列表。
2. 在提供程序的 `authenticate()` 方法中返回该子类实例，并根据你的用户存储填充数据。
3. 在视图的权限钩子中读取 `request.state.admin_user.roles`。

```python
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette_admin import action, row_action
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField
from starlette_admin.types import RequestAction

# Demo user store: replace with a real lookup against your database
USERS = {
    "admin": {
        "name": "Administrator",
        "password": "password",
        "roles": ["read", "create", "edit", "delete", "read_body", "publish"],
    },
    "editor": {
        "name": "Editor",
        "password": "password",
        "roles": ["read", "create", "edit", "read_body", "publish"],
    },
    "viewer": {"name": "Viewer", "password": "password", "roles": ["read"]},
}


# Step 1: AdminUser is a plain dataclass, so subclassing it to add `roles` is
# the intended pattern rather than a workaround.
@dataclass
class MyAdminUser(AdminUser):
    roles: list[str] = field(default_factory=list)


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    # Step 2: authenticate() looks up the roles for the signed-in user and
    # returns them on a MyAdminUser instead of a plain AdminUser.
    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return MyAdminUser(username=user["name"], roles=user["roles"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# Step 3: Every hook below reads request.state.admin_user.roles, which is
# populated only because authenticate() returned a MyAdminUser.
class ArticleView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        return "read" in request.state.admin_user.roles  # Hides the view entirely

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.admin_user.roles

    def can_access_field(
        self, request: Request, field: BaseField, action: RequestAction | None = None
    ) -> bool:
        if field.name == "body":
            return "read_body" in request.state.admin_user.roles
        return super().can_access_field(request, field, action)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "publish":
            return "publish" in request.state.admin_user.roles
        return await super().is_action_allowed(request, name)
```

像注册其他提供程序一样注册 `MyAuthProvider`，即 `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`。此后，上述每个钩子都可以访问 `request.state.admin_user.roles`。

`is_accessible()` 可用于每个 `BaseView`，它会隐藏整个视图，包括其在侧边栏中的条目。`can_create`、`can_edit`、`can_delete`、`can_export`、`can_import` 和 `can_view_detail` 控制 `ModelView` 上的各项操作。`can_access_field` 用于隐藏特定字段，`is_action_allowed` 和 `is_row_action_allowed` 用于限制批量操作和行操作。当某个行操作取决于记录本身而非用户时（例如在已发布的文章上隐藏 `publish`），应改为重写 `is_row_action_allowed_for_obj(request, name, obj)`。该方法接收行对应的底层对象，并回退到 `is_row_action_allowed`。

完整的 API 参考请参见[视图](views.md)和[操作](actions.md)。包含 `can_export`、`can_import` 和一个行操作的完整可运行版本位于 [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth)。

## `@login_not_required`

有些路由即使在整体已加锁的管理面板中也保持公开，例如自助注册表单或健康检查端点。为该端点添加装饰器后，`AuthMiddleware` 便会放行请求，而不检查是否存在有效的 `authenticate()` 结果：

```python
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_admin import CustomView, route
from starlette_admin.auth import login_not_required


class AccountsView(CustomView):
    menu_label = "Accounts"
    path = "/accounts"

    @route("/register", methods=["GET", "POST"], name="register")
    @login_not_required
    async def register(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                request=request, name="register.html", context={}
            )
        form = await request.form()
        # Create the user account before granting access to the panel
        await create_user(email=form["email"], password=form["password"])
        return RedirectResponse(request.url_for("admin:login"), status_code=302)
```

`@route` 和 `@login_not_required` 都只是为函数附加一个属性并原样返回该函数，因此二者的堆叠顺序无关紧要。

## `allow_routes`

`allow_routes` 提供同样的放行机制，但作用于路由名称级别而非函数级别。当你不拥有端点的定义，或希望将放行列表集中在一处时，可以使用它：

```python
provider = MyAuthProvider(allow_routes=["register"])
```

该字符串是路由的名称：可以是方法名，也可以是你传递给 `@route` 中 `name=` 参数的值，例如上面的 `name="register"`。除你列出的自定义路由之外，`AuthMiddleware` 始终允许 `"login"` 和 `"static"`。

## `AdminUser`

`authenticate()` 返回的内容都会填充到 `request.state.admin_user` 中。顶栏会从中读取两个字段：

| 属性 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"`（可翻译） | 顶栏用户菜单中显示的名称。 |
| `photo_url` | `str | None` | `None` | 头像图片 URL。未设置时回退为占位图标。 |

`AdminUser` 是一个普通的 `@dataclass`，因此可以继承它来携带角色、租户 ID 或权限钩子所需的任何其他数据——这正是预期的做法。上文中的 `MyAdminUser` 示例展示了这一实践。

---

**后续内容**

* [安全](security.md)：CSRF、密钥，以及框架自动保护的内容。
* [视图](views.md)：`can_create`、`can_edit`、`can_delete` 以及完整的权限钩子列表。
* [操作](actions.md)：用于批量操作和行操作的 `is_action_allowed` 和 `is_row_action_allowed`。
