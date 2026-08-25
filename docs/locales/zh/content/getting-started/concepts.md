---
title: 核心概念
description: 了解 starlette-admin 的架构设计原则，包括声明式视图、基于 URL 的状态以及与后端无关的模型。
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

# 核心概念

在你编写 `PostView` 并挂载管理实例、完成快速开始教程之后，接下来了解该框架的架构设计原则。这些核心概念为文档的其余部分奠定基础。

## 一个资源对应一个类

管理界面所管理的每个资源都通过单一专用的类来暴露。当你继承 `ModelView` 并将其指向某个数据库模型时，系统会自动为所有标准 CRUD 操作（列表、详情、创建、编辑和删除）生成支持分页、排序和过滤的视图。

这就免去了编写自定义路由或 HTML 模板的需要。决定资源外观、校验方式和行为的一切都包含在这一个视图类中。

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## 同一视图，适配任意后端

视图通过一个可适配的后端层与你的数据交互。无论你的应用使用 SQLAlchemy、SQLModel、Beanie、MongoEngine 还是 Tortoise ORM，配置 API 都完全一致。

无论数据存放在何处，字段、过滤器、权限和生命周期钩子都以一致的方式工作。你在某一个后端上学到的知识可以直接迁移到其他后端。更换底层数据源只需要更新导入语句。

```python
# For SQLAlchemy backends
from starlette_admin.contrib.sqla import ModelView

# For Beanie backends: identical API surface, different import path
from starlette_admin.contrib.beanie import ModelView
```

## 基于 URL 的列表状态

排序、过滤、分页和搜索条件直接与 URL 查询字符串同步。由于服务器完全依据这些 URL 参数来渲染列表状态，因此每个视图状态天生就可以收藏和分享。

如果你将某个特定的管理页面链接发送给同事，他们看到的经过过滤的结果行和排序配置与你看到的完全相同。

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## 字段知晓如何渲染自身

字段是自渲染组件。每种字段类型在三个不同的上下文中各自管理自己的显示逻辑：列表表格中的单元格、详情视图中的行，以及表单内的输入元素。

构建视图时，你可以声明字段实例，或传入由后端自动映射为字段的属性名。选择与你的数据模型匹配的类型，渲染工作交由框架完成：

* `StringField` 用于文本字符串
* `IntegerField` 用于数值数据
* `ImageField` 用于文件上传

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## 声明式表单布局

默认情况下，`fields` 属性会将创建和编辑表单渲染为扁平的垂直列表。若要在不改动底层数据定义的前提下重新组织用户界面，请使用 `form_layout` 属性。

### 元组简写形式

对于基本的网格布局，可以将字段名分组为元组，使它们在同一行中并排渲染。这样就无需导入复杂的部件类。

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### 高级布局部件

当表单变得越来越复杂时，可以使用布局部件来组织其结构。元组简写形式在这些组件内部可以直接使用：

* **`PanelWidget` 或 `FieldsetWidget`：** 使用这些组件将相关字段分组到明确的标题之下，或使区块支持折叠。
* **`TabsWidget`：** 当资源拥有不同类别的数据（例如物流信息与 SEO 元数据）且无需同时展示时，使用此组件。

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

## 过滤器绑定到字段类型

过滤能力直接映射到数据类型，从而确保用户只会看到相关的查询选项。`StringField` 提供*包含*、*以……开头*、*等于*和*为空*等符合语境的文本选项；整数字段提供*大于*或*介于*等数值约束。

你可以使用 `filters` 参数针对单个字段限制或覆盖这些默认值，也可以为特殊的数据类型注册自定义过滤器。

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## 自行接入认证

框架不提供内置的用户模型，因此对你的用户结构完全不做事先假设。实现认证只需编写一个方法：`authenticate(request)`。

将该方法接入你现有的认证基础设施，例如本地数据库表、OAuth 提供商或上游单点登录（SSO）代理请求头。返回 `AdminUser` 对象即授予访问权限；返回 `None` 则拒绝访问。

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## 动作作用于选定的行

批量动作作用于从顶部工具栏选中的多行，行级动作则在单个记录上就地执行。使用 `@action` 或 `@row_action` 装饰视图方法后，该方法会自动出现在用户界面中，无需手动注册路由。

不必从动作方法返回消息字符串，你可以使用内置的 `flash()` 工具直接触发用户通知。

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## 原生数据导出与导入

每个列表页面都提供导出对话框，用户可以在其中选择范围（选中行或当前页）、字段、格式和文件名。当前生效的过滤器和搜索词会被保留，因此导出的文件与屏幕上显示的内容完全一致。

框架原生支持 CSV、JSON 和 PDF 格式。对于 Excel（`xlsx`）等其他格式，框架通过与 `tablib` 集成来支持任何兼容的文件类型。格式以普通扩展名字符串的形式声明。访问控制可通过 `can_export` 钩子进行细粒度管理。

导入向导能够以相同的这些格式安全地接收批量数据。向导会先在预览步骤中对上传内容进行校验，在提交任何数据库写入之前逐行标出错误，并支持可选的主键 upsert。你可以使用 `can_import` 钩子限制对该功能的访问。

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## 灵活的文件存储

通过 `FileField` 和 `ImageField` 进行的媒体管理依赖于底层的 `Storage` 抽象层。使用 `LocalStorage` 写入本地磁盘，或运行 `pip install starlette-admin[s3]` 安装可选的 S3 集成。

在你将字段指向所选的存储配置之后，字段会自动协调文件上传、后端校验和前端渲染。

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## 自定义视图与仪表盘部件

未明确绑定到数据库模型的页面（例如指标仪表盘或自定义报告）可以使用 `CustomView` 构建。内容通过 `widget` 参数填充。该参数既可以接受静态的 `BaseWidget` 实例，也可以接受动态的可调用对象——当内容取决于传入请求时执行该可调用对象。

你可以将布局原语和数据可视化部件组织成清晰的层次结构，从而组合出复杂的用户界面。

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## 事件与方法钩子

框架提供了两个不同的扩展点，用于在创建、更新和删除周期中执行代码：

1. **生命周期方法：** 对于仅限于特定实体的逻辑，可直接在视图类上重写 `before_create` 等本地方法。
2. **事件监听器：** 对于审计日志、缓存失效或 Webhook 等全局性事务，订阅 `admin.events` 系统。

两种模式在完全相同的执行点触发，因此你可以选择最契合自己应用架构的方式。

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Isolated to this view class only
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Global system listener spanning every view class
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**后续内容**

* **[视图](../user-guide/views.md)：** 所有 `ModelView` 配置选项。
* **[字段](../user-guide/fields.md)：** 完整的字段类型目录。
* **[表单布局](../advanced/form-layout.md)：** 使用行、面板和标签页排布创建与编辑表单。
* **[动作](../user-guide/actions.md)：** 深入了解批量动作与行级动作。
