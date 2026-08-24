---
title: SQLModel 集成
description: 使用 starlette-admin 为你的 FastAPI SQLModel 应用构建功能完善的管理后台。
source_hash: 96c8764bbc647c696f3ec02784bf0b7a9b05d3f1b051c40e8783b36bb49e612e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/integrations/sqlmodel/)
<!-- translation-notice:end -->

# SQLModel 集成

[SQLModel](https://sqlmodel.tiangolo.com/) 将 SQLAlchemy 表与 Pydantic 校验组合在同一个模型类中。由于 SQLModel 模型在底层就是 SQLAlchemy 模型，`starlette_admin.contrib.sqlmodel` 模块只是现有 [SQLAlchemy 后端](sqlalchemy.md)之上的一层轻量封装。

该集成并未另起炉灶实现一套独立系统，而是直接从核心 SQLAlchemy 后端继承全部能力，包括字段自动检测、主键管理、关联关系处理、过滤以及会话中间件。它引入了一个健壮的校验层：在任何数据库写入发生之前，将提交的表单数据交由模型自身的 Pydantic 校验器（例如 `Field(min_length=...)` 或自定义的 `@field_validator` 方法）进行校验。由此产生的 `ValidationError` 异常会自动转换为 UI 中逐字段的表单错误。

!!! note
    [SQLAlchemy 页面](sqlalchemy.md)中记录的所有内容均原样适用，包括同步与异步引擎、`sessionmaker` 提供者、每个请求仅提交一次的会话生命周期、关联关系字段以及过滤器注册表。

## 安装

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## 最小示例

```python
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)
    price: float


class ProductView(ModelView):
    fields = ["id", "name", "price"]


SQLModel.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

`ModelView` 直接接受 SQLModel 表类，并自动从模型的 schema 推导出字段列表、表单和过滤器。

## 核心类

### `sqlmodel.Admin`

`sqlmodel.Admin` 类是对 `sqla.Admin` 类的重新导出。它使用相同的构造函数，其必选参数 `session_provider` 可接受 `Engine`、`AsyncEngine`、`sessionmaker` 或 `async_sessionmaker`。它同样插入了相同的会话中间件，在每个请求上填充 `request.state.session`。

### `sqlmodel.ModelView`

`sqlmodel.ModelView` 类继承了 `sqla.ModelView` 的全部功能，并添加了一层校验。其 `validate()` 方法会在写入记录之前调用 `self.model.model_validate(data)`，确保表单提交由模型的 Pydantic 校验器进行检查，而不是严格依赖 SQLAlchemy 列约束。文件字段和关联关系字段被有意排除在此校验调用之外，因为它们不在模型 Pydantic 校验范围之内。

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

内联视图允许用户在父表单中编辑关联行。该类从 SQLAlchemy 的 `InlineModelView` 继承外键检测与会话处理逻辑，并对每个内联行应用相同的 Pydantic 校验。

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Pydantic 校验

模型上声明的约束会自动应用于新建和编辑表单：

```python
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr
    created_at: datetime | None = Field(default=None)

    articles: list["Article"] = Relationship(back_populates="author")
```

如果输入的 `full_name` 少于两个字符，或电子邮件地址无效，校验将会失败。这些失败会在任何 `INSERT` 或 `UPDATE` 操作到达数据库之前，以逐字段表单错误的形式返回。

!!! note
    `EmailStr` 类型需要 `email-validator` 包，可通过 `pip install "pydantic[email]"` 安装。

## 完整可运行示例

本节提供一个与 `starlette-admin` 完整集成且可直接运行的 SQLModel 示例。

### 1. 安装依赖

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

`fastapi[standard]` 包包含 FastAPI CLI，运行 `fastapi dev` 即可启动开发服务器。

### 2. 创建应用

将以下代码保存到名为 `main.py` 的文件中。

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import Column, Text, create_engine
from sqlmodel import Field, Relationship, SQLModel
from starlette_admin import SlugField
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)

    posts: list["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3)
    slug: str = Field(unique=True)
    content: str = Field(sa_column=Column(Text))
    status: PostStatus = Field(default=PostStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Author | None = Relationship(back_populates="posts")


class AuthorView(ModelView):
    fields = ["id", "name", "posts"]


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
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

提交少于三个字符的 `title` 或少于两个字符的 `name` 时，表单会重新渲染，并将错误附加到相应字段上。

### 3. 启动服务器

启动 FastAPI 开发服务器：

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

在浏览器中访问 [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)，即可查看并操作管理后台。

> **进阶示例：**仓库中的 [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) 包含一个功能完备的 CMS 示例，涵盖关联关系、内联视图、动作、过滤器、事件和导出功能。

## 延伸阅读

* **[SQLAlchemy](sqlalchemy.md)：**本集成所依赖的后端，涵盖引擎、会话、事务和过滤器注册表。
* **[视图](../user-guide/views.md)：**探索与后端无关的 `BaseModelView` 配置选项。
* **[过滤器](../user-guide/filters.md)：**了解过滤器构建器以及特定于 ORM 的过滤器如何接入。
