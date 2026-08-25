---
title: MongoEngine 集成
description: 了解如何将 MongoEngine 模型连接到 starlette-admin，通过管理面板管理你的 MongoDB 数据。
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# MongoEngine 集成

MongoEngine 通过一套 Django 风格的字段 API 将 MongoDB 文档建模为同步 Python 类。`starlette_admin.contrib.mongoengine` 模块提供了专门的 `Admin` 和 `ModelView` 类，可直接根据你的 `mongoengine.Document` 定义构建管理视图。

**主要特性：**

* 自动转换字段类型、关联关系和内嵌文档。
* 开箱即用地支持基于 GridFS 的 `FileField` 和 `ImageField` 上传。

## 安装

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## 最小示例

在任何请求到达管理界面之前，必须先建立 MongoDB 连接。将连接逻辑封装在主应用程序的 `lifespan` 上下文管理器中，是确保满足这一前提条件的最佳方式。

```python
from contextlib import asynccontextmanager

import mongoengine as me
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)

    meta = {"collection": "categories"}


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db="podcast_admin", host="mongodb://localhost:27017")
    yield
    me.disconnect()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Podcast Admin", secret_key="change-me-in-production")
admin.add_view(ModelView(Category, icon="fa fa-tags"))
admin.mount_to(app)
```

`ModelView` 直接接受 `mongoengine.Document` 类。它会自动根据文档的字段推导出字段列表、表单和过滤器。

## 核心类：Admin 和 ModelView

### `mongoengine.Admin` 类

`mongoengine.Admin` 类在基础 `Admin` 的基础上增加了一个专用路由：`/api/file/{db}/{col}/{pk}`。该路由可将 GridFS 文件直接流式传输回浏览器。

由于 MongoEngine 模型上的每个 `FileField` 和 `ImageField` 上传文件都存储在 GridFS 中，因此需要该路由来提供这些文件。请始终使用 `mongoengine.Admin` 而不是基础 `Admin`。

### `mongoengine.ModelView` 类

与基类不同，`mongoengine.ModelView` 构造函数接受一个 `document` 位置参数，而不是声明式模型类：

```python
def __init__(
    self,
    document: type[me.Document],
    icon: str | None = None,
    display_name: str | None = None,
    menu_label: str | None = None,
    key: str | None = None,
    converter: BaseMongoEngineModelConverter | None = None,
):

```

如果在 `ModelView` 子类上不设置 `fields` 属性，则默认会按声明顺序包含文档上的每个字段。

`key`、`menu_label` 和 `display_name` 等属性遵循严格的回退顺序：

1. 构造函数参数。
2. 在子类上设置的类级属性。
3. 从文档类名派生的值（`key` 变为 slug 化后的名称，`menu_label` 变为复数形式的美化名称，`display_name` 变为单数形式的美化名称）。

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## 过滤器注册表 {#filter-registry}

每种字段类型都包含一组由 `MongoEngineFilterRegistry` 提供的固定过滤器。可以使用 `filters=[...]` 参数按字段覆盖这些默认值。

| 字段类型 | 可用过滤器 |
| --- | --- |
| `StringField` | 包含、不包含、以……开头、以……结尾、等于、不等于、为空、不为空 |
| `TextAreaField` | 包含、不包含、以……开头、以……结尾、为空、不为空 |
| `EnumField` | 等于、不等于、属于、不属于、为空、不为空 |
| `NumberField` | 等于、不等于、大于、小于、介于、为空、不为空 |
| `FloatField` | 等于、不等于、大于、小于、介于、为空、不为空 |
| `DateField` | 等于、介于、在过去、在未来、为空、不为空 |
| `DateTimeField` | 等于、介于、在过去、在未来、为空、不为空 |
| `BooleanField` | 为真、为假、为空、不为空 |
| `TagsField` | 属于、不属于、为空、不为空 |
| `RelationField` | 为空、不为空 |
| `ObjectIdField` | 等于、不等于、属于、不属于、为空、不为空 |

!!! note
    `ObjectIdField` 表示文档的 `id`。

在底层，每个过滤器的 `apply()` 方法会针对其特定条件返回一个 MongoEngine `Q` 片段。嵌套的 `FilterGroup` 树随后会使用位运算符（`&` 或 `|`）组合这些片段，然后再执行查询。更多详情请参阅[过滤器](../user-guide/filters.md)文档。

## 内嵌文档

MongoEngine 的 `EmbeddedDocumentField` 会转换为 `CollectionField`。在此过程中，内嵌文档上的每个字段都会被递归地转换为其各自的子字段：

```python
import mongoengine as me
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Address(me.EmbeddedDocument):
    street = me.StringField()
    city = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    address = me.EmbeddedDocumentField(Address)
    comments = me.EmbeddedDocumentListField(Comment)


class PostView(ModelView):
    fields = ["id", "name", "address", "comments"]


admin = Admin()
admin.add_view(PostView(Post))
```

在此示例中：

* `address` 字段在创建和编辑时呈现为嵌套子表单，在详情页上呈现为嵌套区块。
* `comments` 字段（`EmbeddedDocumentListField`）会转换为由 `CollectionField` 组成的 `ListField`。它呈现为一组可重复添加的子表单，列表中的每一项显示一个。

## 完整示例

本节提供了一个完整可运行的 MongoEngine 与 `starlette-admin` 集成示例。

### 1. 安装依赖

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

`fastapi[standard]` 包包含了 FastAPI CLI，运行 `fastapi dev` 即可启动开发服务器。

### 2. 创建应用

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

import mongoengine as me
from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin import SlugField
from starlette_admin.contrib.mongoengine import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(me.Document):
    name = me.StringField(required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    meta = {"collection": "authors"}


class Post(me.Document):
    title = me.StringField(required=True)
    slug = me.StringField(required=True, unique=True)
    content = me.StringField(required=True)
    status = me.EnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = me.DateTimeField(default=lambda: datetime.now(timezone.utc))
    author = me.ReferenceField(Author, required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.title

    meta = {"collection": "posts"}


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
    me.connect(db="blog", host=MONGO_URI)
    yield
    me.disconnect()


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

> **进阶示例：** 仓库中的 [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) 包含一个功能齐全的应用程序，涵盖内联视图、事件、自定义行级与批量动作，以及 GridFS 图片和文件上传。

---

## 后续阅读

* **[视图](../user-guide/views.md)**：了解与后端无关的 `BaseModelView` 配置选项。
* **[字段](../user-guide/fields.md)：** 详细介绍每种字段类型及其属性，包括 `CollectionField`。
* **[过滤器](../user-guide/filters.md)：** 探索过滤器构建器 UI，并学习如何编写自定义过滤器。
* **[Beanie](beanie.md)：** 了解适用于 MongoDB 的异步且基于 Pydantic 的替代方案。
