---
title: Beanie 集成
description: 在 FastAPI 中集成 Beanie ODM 与 starlette-admin，为你的 MongoDB 集合创建可扩展的管理界面。
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Beanie 集成

Beanie 将 MongoDB 文档建模为异步 Pydantic 模型。`starlette_admin.contrib.beanie` 模块提供了专门的 `Admin` 和 `ModelView` 类，经过配置后可直接与这些文档交互。

**主要特性：**

- 原生支持 MongoDB 查询操作符与过滤。
- 自动将 Pydantic 校验错误转换为 UI 中针对特定字段的表单错误。
- 内置 MongoDB 全文搜索集成。

## 安装

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## 最小示例

在任何请求到达管理界面之前，必须先初始化 Beanie。将连接逻辑封装在主应用程序的 `lifespan` 上下文管理器中，是确保满足这一前提条件的最佳方式。

```python
from contextlib import asynccontextmanager

import uvicorn
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView


class Genre(Document):
    name: str
    description: str | None = None

    class Settings:
        name = "genres"


mongo_client = AsyncMongoClient("mongodb://localhost:27017")


@asynccontextmanager
async def lifespan(app: Starlette):
    await init_beanie(
        database=mongo_client.get_database("library"), document_models=[Genre]
    )
    yield


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)
```

`ModelView` 直接接受 Beanie 的 `Document` 类。它会自动根据文档的字段推导出字段列表、表单和过滤器。

## 核心类

### `beanie.Admin` 类

`beanie.Admin` 类继承自 `BaseAdmin`，初始化时无需任何数据库特定的配置。连接设置完全在应用程序的 lifespan 中完成。请始终从 `starlette_admin.contrib.beanie` 导入 `Admin`，以确保与未来针对特定后端的增强功能保持兼容。

### `beanie.ModelView` 类

`beanie.ModelView` 类提供了数据库与 UI 之间的集成层。它会自动处理以下操作：

- **字段填充：** 如果未显式指定字段，则根据文档定义自动生成字段。
- **内部字段过滤：** 默认从列表和表单中排除 Beanie 内部的 `revision_id` 字段。
- **关联关系解析：** 使用 `fetch_links=True` 和 `nesting_depth=1` 执行数据库读取，确保 `Link` 引用被解析为其关联对象，而不是返回原始的数据库引用。
- **错误处理：** 将 Pydantic 校验错误转换为针对特定字段的表单错误，直接指引用户定位错误的输入项。

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## `BeanieObjectIdField`

Beanie 使用 `PydanticObjectId` 作为主键。管理面板会使用专用的 `BeanieObjectIdField` 自动表示这些主键以及任何原始的 ObjectId 引用。

尽管它的渲染和校验方式与标准的 `StringField` 完全相同，但它在过滤器注册表中拥有自己独立的条目。这种分离确保 ObjectId 特定的过滤器只应用于 ObjectId 字段，而不是应用程序中的每个标准文本字段。这些专用过滤器会在查询数据库之前安全地将字符串解析为有效的 `PydanticObjectId` 对象。

## 过滤器注册表 {#filter-registry}

每种字段类型都会从 `BeanieFilterRegistry` 获得一组默认过滤器。

- **字符串匹配：** 相等过滤器使用不区分大小写的正则表达式，以与“包含”、“以……开头”等其他文本搜索保持一致。
- **数组操作：** 该注册表内置了基于数组的过滤支持，让针对列表值字段（如 `TagsField`）的“属于其中之一”（Is one of）操作开箱即用。
- **主键：** 构建查询片段时，`id` 字段会自动重映射为 MongoDB 原生的 `_id`。

## 全文搜索

当用户在列表页使用搜索框时，管理面板会检查 MongoDB 集合中是否存在文本索引，并相应地调整查询策略：

- **存在文本索引：** 查询将使用 MongoDB 原生的 `$text` 操作符。这提供了真正的全文搜索能力，包括分词、词干提取和相关度排序。
- **无文本索引：** 系统会回退为对所有标记为 `searchable` 的字段执行不区分大小写的正则表达式搜索。这种方式无需任何配置，但无法按相关度对结果排序，也无法利用标准索引。

管理面板会检测已存在的文本索引，但不会创建它们。要启用原生文本搜索，必须在 Beanie 文档上定义该索引。例如，可以通过在模型中添加 `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]` 来实现。

!!! note
如果启用了文本索引，可以在 `ModelView` 子类上设置 `full_text_override_order_by = True`，以便按照 MongoDB 的相关度得分而非默认列排序来排列搜索结果。

## 完整示例

本节提供了一个完整可运行的 Beanie 与 `starlette-admin` 集成示例。

### 1. 安装依赖

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

`fastapi[standard]` 包包含了 FastAPI CLI，运行 `fastapi dev` 即可启动开发服务器。

### 2. 创建应用

将以下代码保存到名为 `main.py` 的文件中。

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Link, init_beanie
from fastapi import FastAPI
from pydantic import Field
from pymongo import AsyncMongoClient
from starlette_admin import SlugField
from starlette_admin.contrib.beanie import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"
mongo_client = AsyncMongoClient(MONGO_URI)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Document):
    name: str

    async def __admin_repr__(self, request) -> str:
        return self.name

    class Settings:
        name = "authors"


class Post(Document):
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Link[Author]

    async def __admin_repr__(self, request) -> str:
        return self.title

    class Settings:
        name = "posts"


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
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_beanie(
        database=mongo_client.get_database("blog"), document_models=[Author, Post]
    )
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

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

> **进阶示例：** 仓库中的 [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) 包含一个功能齐全的示例，涵盖内联视图、事件和自定义批量动作。

## 后续阅读

- **[视图](../user-guide/views.md)**：了解与后端无关的 `BaseModelView` 配置选项。
- **[过滤器](../user-guide/filters.md)：** 过滤器构建器，以及 ORM 特定过滤器如何接入。
- **[MongoEngine](mongoengine.md)：** starlette-admin 内置的另一个 MongoDB 后端。
- **[SQLAlchemy](sqlalchemy.md)：** starlette-admin 内置的关系型后端。
