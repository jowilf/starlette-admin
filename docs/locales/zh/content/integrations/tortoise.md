---
title: Tortoise ORM 集成
description: 使用 starlette-admin 在 FastAPI 中轻松为你的 Tortoise ORM 模型创建管理界面。
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Tortoise ORM 集成

Tortoise ORM 是一个受 Django 启发、原生支持 asyncio 的对象关系映射器。`starlette_admin.contrib.tortoise` 模块提供了专门的 `Admin`、`ModelView` 和 `InlineModelView` 类，它们经过预配置，可直接与你的 Tortoise 模型集成。

**主要特性：**

* **自动字段转换：** 将 Tortoise 模型字段直接映射为 UI 组件，完全支持枚举、JSON、日期以及自动时间戳。
* **关联关系映射：** 将外键和一对一关联转换为 `HasOne` 字段，将多对多关联转换为 `HasMany` 字段。反向关联会自动以只读方式呈现。
* **高级过滤：** 在过滤器构建器中利用 Tortoise 的 `Q` 表达式，并支持跨字符串字段进行不区分大小写的全文搜索。
* **错误转换：** 将 Tortoise 校验错误直接映射为 UI 中针对特定字段的表单错误。

## 安装

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## 最小示例

Tortoise 在应用程序的 `lifespan` 上下文管理器中连接数据库。由于管理视图通常在导入时实例化（早于 `Tortoise.init()` 执行），因此必须尽早解析关联关系。

在定义模型之后立即调用 `Tortoise.init_models()`，以确保在构建管理视图时关联关系可用。

```python
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from tortoise import Tortoise, fields
from tortoise.models import Model
from starlette_admin.contrib.tortoise import Admin, ModelView


class Genre(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)


# Resolve relations at import time before the admin views are built.
Tortoise.init_models(["app"], "models")


@asynccontextmanager
async def lifespan(app: Starlette):
    await Tortoise.init(db_url="sqlite://library.sqlite3", modules={"models": ["app"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
```

`ModelView` 直接接受 Tortoise 的 `Model` 类，并自动根据模型的 schema 推导出字段列表、表单和过滤器。

## 核心类

### `tortoise.Admin`

`tortoise.Admin` 类继承自 `BaseAdmin`，初始化时无需任何数据库特定的配置。连接设置完全在应用程序的 lifespan 中完成。请始终从 `starlette_admin.contrib.tortoise` 导入 `Admin`，以确保与未来针对特定后端的增强功能保持兼容。

### `tortoise.ModelView`

`tortoise.ModelView` 类提供了数据库与用户界面之间的集成层。它会自动处理以下操作：

* **字段填充：** 如果未显式指定字段，则根据模型定义生成字段。默认会省略作为对一（to-one）关联底层存储的原始键列（如名为 `author` 的关联对应的 `author_id`）以及反向关联。
* **关联关系解析：** 预取视图展示的每一个关联关系，确保列表页和详情页永远不会触发延迟加载。
* **自动时间戳：** 使用 `DatetimeField(auto_now=...)` 或 `DatetimeField(auto_now_add=...)` 的列会以只读方式呈现，且永远不会被标记为必填。
* **错误处理：** 将 Tortoise 校验错误（`"<field>: <detail>"`）转换为针对特定字段的表单错误，直接指引用户定位错误的输入项。

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

内联视图允许用户在父表单中编辑关联行。当子模型恰好只有一个指向父模型的关联关系时，外键会被自动检测。如果存在多个关联关系，则必须使用关联关系名称或其原始键列显式设置 `fk_attr`。

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## 处理关联关系

该集成会根据字段类型将数据库关联关系映射为管理字段。必须为每个关联的模型注册一个 `ModelView`，关联关系字段才能成功解析其指向的外部视图。

| 关联关系类型 | Tortoise 配置 | 管理行为 |
| --- | --- | --- |
| **正向（对一）** | `ForeignKeyField`、`OneToOneField` | 转换为 `HasOne`。 |
| **正向（对多）** | `ManyToManyField` | 转换为 `HasMany`。 |
| **反向** | `related_name` 属性 | 以只读方式呈现。必须显式添加到 `fields` 中才会显示。 |

**关联关系的过滤与排序：**
对一（to-one）关联提供针对原始键列的“Is null”和“Is not null”过滤器。要在过滤器构建器中公开某个关联关系，请将其名称添加到 `searchable_fields`。要支持按原始键列排序，请将其名称添加到 `sortable_fields`。

## 搜索与过滤

### 过滤器注册表 {#filter-registry}

每种字段类型都会从 `TortoiseFilterRegistry` 获得一组默认过滤器，这些过滤器基于 Tortoise 的 `Q` 表达式实现：

* **字符串匹配：** 包含、以……开头/结尾以及相等过滤器均使用不区分大小写的查询方式（`__icontains`、`__istartswith`、`__iendswith`、`__iexact`）。
* **枚举：** 对于 `CharEnumField` 和 `IntEnumField` 列，原始过滤值会在查询前被转换回枚举成员。
* **时间列：** `TimeField` 列仅提供空值检查。这一限制的原因在于，时间类型的参数无法以可移植的方式绑定到所有数据库后端。

### 全文搜索

列表页的搜索框会对所有可搜索的字符串类字段构建不区分大小写的 `contains` 匹配（由 `OR` 组合的 `Q` 表达式）。你可以通过在视图上重写 `get_search_query()` 方法来自定义此行为。

## 完整示例

本节提供了一个完整可运行的 Tortoise ORM 与 `starlette-admin` 集成示例。

### 1. 安装依赖

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

`fastapi[standard]` 包包含了 FastAPI CLI，运行 `fastapi dev` 即可启动开发服务器。

### 2. 创建应用

将以下代码保存到名为 `main.py` 的文件中。

```python title="main.py"
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI
from starlette_admin import SlugField
from starlette_admin.contrib.tortoise import Admin, ModelView
from tortoise import Tortoise, fields
from tortoise.models import Model

DB_URL = "sqlite://blog.sqlite3"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)

    def __admin_repr__(self, request) -> str:
        return self.name


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    status = fields.CharEnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.Author", related_name="posts")

    def __admin_repr__(self, request) -> str:
        return self.title


# Resolve relations at import time before the admin views are built.
Tortoise.init_models(["main"], "models")


class AuthorView(ModelView):
    fields = ["id", "name"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        "content",
        "status",
        "created_at",
        "author",
    ]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["main"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

由于 `created_at` 使用了 `auto_now_add`，管理界面会自动将其渲染为只读，无需配置 `exclude_fields_from_create` 或 `exclude_fields_from_edit`。

### 3. 运行服务器

启动 FastAPI 开发服务器：

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

在浏览器中打开 [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)，即可查看并操作管理面板。

> **进阶示例：** 仓库中的 [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) 包含一个功能齐全的示例，涵盖关联关系、内联视图、枚举以及由 SQLite 支撑的 JSON 字段。

## 后续阅读

* **[视图](../user-guide/views.md)：** 了解与后端无关的 `BaseModelView` 配置选项。
* **[过滤器](../user-guide/filters.md)：** 了解过滤器构建器以及 ORM 特定过滤器如何接入。
* **[SQLAlchemy](sqlalchemy.md)：** starlette-admin 内置的另一个关系型后端的文档。
