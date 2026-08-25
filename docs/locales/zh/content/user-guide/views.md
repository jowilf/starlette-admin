---
title: 视图
description: 了解如何在 starlette-admin 中配置列表视图和详情视图，包括搜索、排序和分页。
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# 视图

`starlette-admin` 由三类视图构建其侧边栏：`ModelView` 公开数据库模型，`CustomView` 渲染独立页面，`Link` 添加超链接。

## ModelView

在管理界面中公开数据库模型的方式是编写 `ModelView` 子类。该视图上的类属性和方法重写决定了资源的呈现方式、行为方式以及数据处理方式。

本节的所有示例都基于以下 SQLAlchemy 设置：

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### 基本用法

要公开 `Post` 模型，请继承 `ModelView` 并配置其属性。

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

视图类在被注册到 `Admin` 实例之前不会有任何作用：

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

如需查看以相同方式基于 `Post` 模型构建的可运行管理示例，请参阅 [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart)。

注册一个视图会生成支持分页、排序和搜索的界面，用于列出、查看、创建、编辑和删除记录，全程无需编写路由或模板。

!!! note
    请从所用后端的 contrib 包导入 `ModelView`，例如 `starlette_admin.contrib.sqla`、`.beanie`、`.mongoengine`、`.sqlmodel` 或 `.tortoise`。**下文描述的所有属性在各后端之间完全一致**，因此之后可以将 SQLAlchemy 模型替换为 MongoEngine 文档，而无需更改视图逻辑。

### 核心配置

#### 命名与路由

默认情况下，管理界面会根据模型类名推导 URL 路由和 UI 标签。对于 `Post` 模型，推导结果如下：

* **键：** `post`（URL：`/admin/post/list`）
* **菜单标签：** `Posts`（侧边栏条目）
* **显示名称：** `Post`（诸如 **New Post** 之类的 UI 按钮）

当推导出的值不符合需求时，可以在注册时或构造函数中进行覆盖。

| 属性 | 描述 | 覆盖示例 | 生成的 UI 或 URL |
| --- | --- | --- | --- |
| **`key`** | 内部 slug 和基础 URL 路由。 | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | 侧边栏中使用的复数名词。 | `menu_label="Blog Posts"` | **侧边栏：** Blog Posts |
| **`display_name`** | 动作和表单中使用的单数名词。 | `display_name="Article"` | **按钮：** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### 字段选择与自定义 {#field-selection-and-customization}

`fields` 列表设定哪些模型属性会出现在列表视图、详情页面和表单中。省略该列表则会公开所有模型属性。

可以混合使用字符串名称和显式的 `BaseField` 实例来控制部件、校验和标签：

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    管理界面会自动检测主键。仅在检测失败时才需定义 `pk_attr`，例如自定义后端没有单一字段的主键时。

#### 上下文字段可见性

有些字段通常应出现在列表页或详情页上，但不应出现在创建表单中，例如时间戳和由系统维护的状态。使用 `exclude_fields_from_*` 属性可以在特定界面上隐藏字段：

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

可用的排除属性分别以 `_create`、`_edit`、`_list`、`_detail`、`_export` 和 `_import` 结尾。

!!! important
    若要让用户在创建记录时能够设置主键（该功能默认关闭），请设置 `show_pk_in_forms = True`。

#### 表单布局

默认情况下，`fields` 会将创建表单和编辑表单渲染为平铺的垂直列表。若要在不改动数据定义的情况下重新组织界面，请使用 `form_layout` 属性。

**元组简写**

对于基本的网格布局，无需导入部件类。将多个字段名称组成一个元组，即可让它们在同一行中并排渲染。

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**高级布局部件**

随着表单变得复杂，可以使用布局部件来组织结构。元组简写在布局部件内部同样适用：

* **`PanelWidget` 或 `FieldsetWidget`：** 将相关字段分组置于一个标题之下，或将某个区块设为可折叠。
* **`TabsWidget`：** 分隔无需同时显示的不同类别数据，例如配送信息和 SEO 元数据。

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

有关带显式宽度的多列行、选项卡、静态内容以及访问控制行为，请参阅[表单布局](../advanced/form-layout.md)。

### 数据表格功能

#### 搜索与排序 {#search-and-sort}

通过 `searchable_fields` 和 `sortable_fields` 控制用户查找和排序数据的方式。

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`**：启用过滤器构建器和全局搜索框。全局搜索会对这些字段执行全文查询。
* **`sortable_fields`**：限制用户可以按哪些列标题进行排序。通过 URL 参数传入的对其他字段的排序请求将被忽略。
* **`fields_default_sort`**：设置表格的初始状态。传入纯字符串表示按升序排序；传入包含 `True` 的元组表示按降序排序；传入包含 `False` 的元组表示显式按升序排序。串联多个条目可实现多列排序。

#### 分页与 UI 控件 {#pagination-and-ui-controls}

使用以下属性微调列表页面的布局：

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` 和 `page_size_options`**：默认的分页数量上限和下拉菜单选项。
* **`show_goto_page`**：为大型数据集添加“跳转到指定页”输入框。
* **`search_auto_submit`**：随用户输入实时过滤。
* **`show_detail_search`**：在详情页添加搜索框，用于过滤内嵌的关联关系表格。
* **`row_click_navigate`**：当用户点击表格行的任意位置时打开详情页。该功能默认开启。将其设为 `False` 可使行保持不可点击状态，用户需改用行级动作进行导航。对于 `can_view_detail` 校验未通过的用户，表格行永远不可点击。

#### 内联编辑

可以让用户直接从列表视图修改特定字段，而无需打开完整的编辑表单。

使用 `inline_editable_fields` 属性声明哪些列支持该功能。点击已启用的单元格后，将打开一个弹出框以便快速更新。

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "安全与访问"
    内联编辑默认关闭。开启该功能后，视图现有的 `can_edit` 权限仍然对其构成限制。

有关配置细节、校验行为以及所支持字段类型的完整清单，请参阅[内联编辑](inline-edit.md)指南。

### 关联关系数据

管理界面会代为处理数据的关联关系。对于 `Post` 与 `Author` 之间的多对一关系，只需将关联关系属性添加到 `fields` 列表中。只要两个模型都注册了视图，UI 就会渲染相应的部件。

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### 手动声明关联关系

只有当目标视图以自定义 `key` 注册时，才需要自行声明 `HasOne` 或 `HasMany` 字段。

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### 对象表示

当管理界面需要将记录显示为单个值时，会回退使用主键。此时，一条关联到 `Author #3` 的 `Post` 在关联关系列中会显示为“3”，这几乎无法向用户传达任何信息。两个可选方法可以将这一默认值替换为有意义的内容，它们定义在**模型**上而非视图上。这两个方法都接受当前 `Request` 参数，且既可为同步也可为异步。

#### `__admin_repr__`

返回一个纯字符串，用在记录以文本形式出现的所有位置：列表页和详情页上的关联关系列、面包屑导航，以及动作确认消息。

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

定义该方法后，文章的作者将显示为“Gabriel Garcia Marquez”而非“3”。

#### `__admin_select2_repr__`

返回一个 HTML 片段，用于渲染关联关系表单字段所使用的 `select2` 下拉框中的选项，从而可以用图片、徽章或辅助文本丰富选项内容。如果没有该方法，管理界面将回退到 `__admin_repr__` 经转义后的输出。如果两个方法都不存在，则回退到根据记录的非关联字段生成的摘要。

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    返回值必须是有效的 HTML。

!!! warning
    请对数据库值进行转义，以防跨站脚本（XSS）攻击。如上所示，使用 Jinja2 和 `autoescape=True` 渲染该片段，或使用 `html.escape` 自行转义每个值。更多信息请参阅 [OWASP 文档](https://owasp.org/www-community/attacks/xss/)。

### 安全与授权 {#security-and-authorization}

通过重写 `ModelView` 上的权限方法来限制访问。每个方法均返回一个布尔值，且基类实现一律返回 `True`。

该模式可直接接入 `AuthProvider`。在下方的示例中，每项检查都会从会话的 `admin_user` 中读取 `roles` 列表：

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

有关配置 `AuthProvider` 以及填充 `admin_user` 对象的更多信息，请参阅[认证](auth.md)。

!!! note
    只需重写想要限制的方法。未重写的方法将继续允许访问。

### 生命周期钩子 {#lifecycle-hooks}

使用生命周期钩子，可以在数据库事务前后立即运行副作用或修改数据。

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

可用的钩子包括 `before_create`、`after_create`、`after_create_committed`、`before_edit`、`after_edit`、`after_edit_committed`、`before_delete`、`after_delete` 和 `after_delete_committed`。

#### 提交后钩子

`after_create_committed`、`after_edit_committed` 和 `after_delete_committed` 仅在数据库事务提交之后运行。写入操作回滚时不希望执行的副作用应放在这些钩子中处理，例如发送电子邮件或将后台任务加入队列：

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    这些钩子运行时，请求的会话已提交并关闭。不要在钩子内部通过 `request.state.session` 写入数据库。请使用外部 I/O，或打开一个新的数据库会话。

!!! important
    在 `after_delete_committed` 中，`obj` 已从所有会话分离。删除前已加载的属性仍可读取，但读取从未加载过的属性会失败，因为对应的行已被删除。

!!! note "后端支持"
    只有将提交推迟到请求末尾的后端才会触发这些钩子。目前只有 SQLAlchemy 后端采用这种方式。

!!! tip
    对于跨越多个视图的逻辑（例如审计日志），请改用[事件](../advanced/events.md)。

### UI 自定义

#### 侧边栏组织 {#sidebar-organization}

使用 `DropDown` 将相关视图分组到一个可折叠的文件夹中。文件夹可以混合包含 `ModelView`、`CustomView` 和 `Link` 条目。

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### 导出器与导入器

`exporters` 和 `importers` 属性设定可用于数据传输的格式。内置选项及自定义导出器和导入器的编写方法，请参阅[导出与导入](export-import.md)指南。

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### 动作、内联表单与模板

`ModelView` 还有三组适用于复杂场景的功能，每组都有专门的指南：

* **动作与行级动作：** `actions` 和 `row_actions` 属性可在 CRUD 之外添加自定义批量操作和逐行操作。请参阅[动作](actions.md)。
* **内联表单：** `inlines` 属性可将关联模型的创建和编辑表单嵌套在父视图中。请参阅[内联表单](inline-forms.md)。
* **模板与资源：** 通过 `list_template`、`detail_template`、`create_template` 或 `edit_template` 用自己的 Jinja 模板替换默认页面。请参阅[模板](../advanced/templates.md)。

## CustomView

并非所有管理页面都与数据库模型对应。`CustomView` 可创建独立的侧边栏页面，其内容由部件、自定义模板或自定义路由构成。

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

完整的部件目录、仪表盘构建说明和自定义路由，请参阅[自定义视图](custom-views.md)。

## Link {#link}

`Link` 会在侧边栏中添加一个超链接，指引用户前往线上站点、外部文档或其他内部工具。

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** 和 **`icon`**：侧边栏条目的文本和图标。
* **`url`** 和 **`target`**：目标地址和锚点的 target 属性。

`admin.add_link(link)` 是对 `admin.add_view(link)` 的轻量封装。选择在代码库中更具可读性的那个即可。还可以将 `Link` 嵌套在 `DropDown` 中，如[侧边栏组织](#sidebar-organization)所述。

---

## 后续内容

* **[字段](fields.md)**：完整的字段类型目录。
* **[表单布局](../advanced/form-layout.md)**：使用行、面板、字段集和选项卡安排创建表单和编辑表单。
* **[自定义视图](custom-views.md)**：使用部件、模板和自定义路由构建仪表盘和独立页面。
* **[动作与行级动作](actions.md)**：在 CRUD 之外添加批量操作和逐行操作。
* **[内联编辑](inline-edit.md)**：让用户从列表页直接编辑某一行的单个字段。
* **[内联表单](inline-forms.md)**：将关联模型的创建和编辑表单嵌套在父视图中。
* **[模板](../advanced/templates.md)**：换用自己的 Jinja 模板并注入自定义资源。
