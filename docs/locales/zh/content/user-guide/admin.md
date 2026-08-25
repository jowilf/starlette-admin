---
title: Admin 配置
description: 配置 starlette-admin 实例，自定义主题、路由以及整体安全设置。
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# Admin

所有管理级别的设置都以关键字参数的形式传递给 `Admin` 类：导航栏标题、挂载位置、CSRF 与认证配置，以及所渲染的主题。

## 基本用法

首先，从与你的对象关系映射器（ORM）相匹配的 `contrib` 包中导入 `Admin` 类：

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

下面是一个使用 SQLAlchemy 的最简配置：

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()

admin = Admin(
    session_provider=engine,
    title="My Admin",
    base_url="/admin",
    secret_key="a-long-random-string",
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

* `title` 设置导航栏文本和 HTML `<title>` 标签。
* `base_url` 定义管理挂载所在的路径前缀（基础路径）。
* `secret_key` 用于对 CSRF 和 flash cookie 进行签名。
* `add_view` 用于注册视图，而 `mount_to` 会先构建管理的路由和中间件，再将它们挂载到你的应用程序上。

每个 `Admin` 类都接受下文所述的全部配置选项，部分类还会添加特定于后端的行为：

* `contrib.sqla.Admin(session_provider, ...)` 的第一个位置参数可以是 `Engine`、`AsyncEngine`、`sessionmaker` 或 `async_sessionmaker`，并且会自动为你插入 `DBSessionMiddleware`。`contrib.sqlmodel.Admin` 是同一个类的重新导出。参见 [SQLAlchemy](../integrations/sqlalchemy.md) 和 [SQLModel](../integrations/sqlmodel.md)。
* `contrib.beanie.Admin`、`contrib.mongoengine.Admin` 和 `contrib.tortoise.Admin` 不接受额外的构造函数参数，因为 Beanie、MongoEngine 和 Tortoise ORM 在管理之外自行管理连接。`mongoengine.Admin` 还会在 `mount_to` 中注册一条 GridFS 文件服务路由。参见 [Beanie](../integrations/beanie.md)、[MongoEngine](../integrations/mongoengine.md) 和 [Tortoise ORM](../integrations/tortoise.md)。

## 完整参考

`Admin` 构造函数接受下列全部参数作为关键字参数。

### 标识与品牌

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | 导航栏文本和 `<title>` 标签。 |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | 导航栏中显示的徽标，取代 `title`。可传入普通的 URL，或传入一个按请求解析该 URL 的可调用对象，例如用于按租户定制品牌。 |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | 登录页中显示的徽标，取代 `logo_url`。未设置时回退到 `logo_url`。 |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | favicon `<link>` 标签的 href。 |

`logo_url`、`login_logo_url` 和 `favicon_url` 均可接受字符串或 `(request) -> str | None` 可调用对象。当品牌展示依赖于请求时，请使用可调用对象，例如在多租户应用程序中，或在服务多个主机名的情况下：

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### 挂载

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | 管理挂载所在的 URL 前缀。 |
| `route_name` | `str` | `"admin"` | Starlette 挂载名称。所有内部链接（`list`、`edit`、导出和静态资源）都通过调用 `request.url_for(route_name + ":list", ...)` 生成。 |

要在同一应用程序中运行多个 `Admin` 实例，请为每个实例指定不同的 `base_url` 和 `route_name`。否则，一个管理实例生成的链接可能会解析到另一个实例上。参见[多个 Admin 实例](../advanced/multiple-admin.md)。


### 模板、静态文件与主题

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | 在回退到内置模板之前，用于查找模板覆盖文件的目录。 |
| `static_dir` | `str | None` | `None` | 额外静态文件所在的目录，这些文件将与内置 CSS 和 JS 一同提供。 |
| `theme` | `BaseTheme` | `DefaultTheme()` | 一个主题子类，定义布局模板、图标集和静态资源。 |

[自定义主题](../advanced/custom-themes.md)和[模板](../advanced/templates.md)对这些选项作了完整说明。

### 首页

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None`（基于已注册视图构建的 `DefaultIndexView`） | 在 `base_url` 处渲染的页面。 |

默认首页包含一个欢迎横幅，以及每个已注册模型视图对应的一个面板，各面板分别显示其记录数。要替换首页，请传入你自己的 `CustomView`，通常是一个 `DefaultIndexView` 子类，或任何带有 `widget` 的 `CustomView`。参见[自定义视图与部件](custom-views.md)。

### 认证、安全与数据保护

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None`（管理界面可公开访问） | 对每条路由进行访问控制。参见[认证](auth.md)。 |
| `secret_key` | `str | None` | `None`（启动时生成随机密钥，并发出 `UserWarning`） | 对 CSRF 和 flash cookie 进行签名。 |
| `middlewares` | `Sequence[Middleware] | None` | `None` | 额外的 Starlette 中间件，与管理自身添加的 CSRF、flash 和认证中间件一同运行。 |
| `import_config` | `ImportConfig | None` | `None`（`ImportConfig()` 默认值） | 导入端点的上传大小限制和 ZIP 炸弹防护限制。 |
| `export_config` | `ExportConfig | None` | `None`（`ExportConfig()` 默认值） | 导出端点的行数上限和 URL 文件下载限制。 |

[安全](security.md)指南深入介绍了这五个参数。

### 区域设置与时区

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None`（仅英文，无 `LocaleMiddleware`） | 启用经过翻译的界面字符串。 |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()`（开启） | 将显示的日期时间转换为查看者所在时区的时间。 |

完整的操作指引请参阅[国际化与时区](i18n.md)。

### 调试 {#debugging}

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | 设为 `True` 时，会在启动前调用 `starlette_admin.logging.configure_logging()`，从而为 `starlette_admin` 包启用带颜色的 DEBUG 级别控制台日志。 |

```python
admin = Admin(
    session_provider=engine, title="My Admin", secret_key="a-long-random-string", debug=True
)
```

调试日志对开发很有帮助。每个请求都会记录执行了哪些中间件、哪个视图解析了该 URL，以及权限检查通过或失败的原因。

!!! warning
    在生产环境中请保持 `debug=False`。DEBUG 级别的日志十分冗长，会给每个请求带来显著的开销。

如果想要更轻量的方案，可以自行调用 `starlette_admin.logging.configure_logging(level=logging.INFO)`，而不是传入 `debug=True`。这样既能获得日志处理器，又不会产生完整的 DEBUG 详细输出。

## 注册视图与挂载

创建 `Admin` 实例后，注册你的视图，并将管理挂载到你的应用程序上。

```python
admin.add_view(ModelView(Post))  # Register a view (BaseModelView, CustomView, and so on)
admin.mount_to(app)  # Mount the admin onto your Starlette or FastAPI app
```

### 注册视图

使用 `add_view` 向管理仪表盘中添加组件。该方法既可以接受视图实例，也可以接受视图类；你可以注册模型视图、自定义页面、下拉菜单以及外部链接。

### 挂载到应用程序

注册完所有视图后，请恰好调用一次 `mount_to(app)`，将管理附加到你的 Starlette 或 FastAPI 应用程序上。此步骤会最终确定路由和安全配置。

!!! important "操作顺序很重要"
    挂载会锁定管理配置，以确保每个视图都能被正确路由。

    * 在挂载之前访问 `admin.app` 会抛出 `RuntimeError`。
    * 首次挂载之后，再注册新的视图或再次调用 `mount_to` 同样会抛出 `RuntimeError`。

```python
admin.app  # Raises RuntimeError: not mounted yet

admin.mount_to(app)
admin.app  # Returns the mounted sub-application

admin.add_view(ModelView(Comment))  # Raises RuntimeError: already mounted
```

---

**后续内容**

* **[安全](security.md)：** `secret_key`、CSRF，以及导出和导入限制。
* **[认证](auth.md)：** 接入 `auth_provider`。
* **[多个 Admin 实例](../advanced/multiple-admin.md)：** 在同一应用程序中运行多个 `Admin`。
