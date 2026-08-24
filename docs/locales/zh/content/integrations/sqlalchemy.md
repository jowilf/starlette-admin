---
title: SQLAlchemy 集成
description: 了解如何将 starlette-admin 与 SQLAlchemy 集成。在 FastAPI 中为你的关系数据库模型创建管理后台。
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

SQLAlchemy 后端是 `BaseModelView` 的参考实现。它仅针对 SQLAlchemy 2 的 `DeclarativeBase` 模型进行过测试。其他后端（如 Beanie、MongoEngine、Tortoise ORM 或你的自定义实现）则在其各自的数据存储之上实现同样的契约。

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]


class ProductView(ModelView):
    fields = ["id", "name", "price"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

## 安装

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2
    ```

如果不想使用 SQLite，可以将 `aiosqlite` 替换为 `asyncpg`（PostgreSQL）或 `aiomysql`/`asyncmy`（MySQL）。数据库驱动仅在异步引擎场景下相关。同步引擎使用纯 SQLAlchemy 所需的标准 DBAPI 驱动（如 `psycopg2` 或 `pymysql`），无需从 `starlette-admin` 安装额外的包。

## 异步引擎与同步引擎

`Admin` 既接受 `Engine`，也接受 `AsyncEngine`。传入你已配置好的任意一种实例即可：

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` 会在请求时对引擎检查一次，并打开匹配的会话类型：`AsyncEngine` 对应 `AsyncSession`，同步 `Engine` 对应普通的 `Session`。内部实现中，`ModelView` 通过 `isinstance(session, AsyncSession)` 进行分支判断。对于同步会话，它会通过 `anyio.to_thread.run_sync` 将阻塞调用路由到线程中执行，以避免阻塞事件循环。

## 传入 `sessionmaker` 而非引擎

`session_provider` 参数也接受 `sessionmaker` 或 `async_sessionmaker`。当需要直接配置会话时，请传入 session 工厂而非裸引擎。

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
会话中间件会调用 `session_maker()` 为每个请求生成一个新会话，而不是在内部自行构造。

## `sqla.Admin` 和 `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` 接受与 `starlette_admin.BaseAdmin` 相同的参数，外加一个必选的位置参数：`session_provider`。该提供者可以是 `Engine`、`AsyncEngine`、`sessionmaker` 或 `async_sessionmaker`。初始化期间，管理面板会配置一个绑定到所选提供者的会话中间件，并将其插入中间件栈的最前端。这一机制确保在每个请求上都会自动填充 `request.state.session`，然后才会执行你的视图代码。

`sqla.ModelView` 需要一个 SQLAlchemy 模型。初始化时，它会检查该模型，直接根据元数据自动检测字段、管理主键并配置过滤器注册表。

## 模型声明

使用标准 SQLAlchemy 声明式类定义模型：

```python
from datetime import datetime
from enum import Enum

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus]
    views: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

如果未在视图上设置 `fields`，`ModelView` 会按声明顺序使用模型上的所有属性。主键会被自动检测，并从新建和编辑表单中排除。其余每一列和每一个关联关系都会自动转换为合适的字段类型（如 `IntegerField`、`StringField`、`EnumField`、`HasOne` 或 `HasMany`）。

## 自动检测的默认值

列在 Python 侧配置的 `default=` 会在你首次打开新建表单时自动填充。你无需在字段本身上重复此定义：

```python
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    views: Mapped[int] = mapped_column(default=0)  # form shows 0
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )  # form shows now()
```

标量默认值（`default=0`）会严格按照其定义原样复制。可调用默认值（`default=datetime.utcnow` 或 `default=uuid.uuid4`）会在渲染表单时触发一次，从而显示真实值，而不是函数的 `repr` 形式。

!!! important
    主键列即使在定义了默认值的情况下也永远不会被预填充。它们被假定为由服务器端生成（通过 `autoincrement` 或序列），并被完全排除在新建和编辑表单之外。SQL 表达式默认值（如 `server_default=func.now()` 或数据库端的 `DEFAULT`）同样会被跳过，因为没有可在 Python 层面显示的值。这些值由数据库在插入时负责填充。

## 关联关系字段

模型上的 SQLAlchemy `relationship()` 会根据 `RelationshipProperty.direction` 属性自动转换为 `HasOne`（多对一或一对一）或 `HasMany`（一对多或多对多）。你无需显式声明字段类型：

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")
```

设置 `PostView.fields = ["id", "title", "author"]` 后，`author` 会渲染为 Select2 下拉框。该下拉框通过 AJAX 从关联视图的 `/_api/{key}/relation-lookup` 端点加载数据（其中 `{key}` 表示 `author`，即 `AuthorView` 的键）。应用绝不会一次性将整个作者表加载到页面中。当关联表包含数千行数据时，这种惰性加载行为对性能至关重要。类似地，设置 `AuthorView.fields = ["id", "name", "posts"]` 后，`posts` 会利用同一个查找端点渲染为多选控件。

## 复合主键

使用多个 `primary_key=True` 列构成复合主键的模型开箱即用，无需任何额外配置。这也涵盖了每个主键列同时充当外键的场景，例如多对多关联对象。

完整可运行的示例请参阅 [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks)。

## 过滤器注册表 {#filter-registry}

每种字段类型都会从 `SqlaFilterRegistry` 获得一组默认过滤器。解析方式是遍历字段所属类的继承层次，详见[过滤器](../user-guide/filters.md)文档。一个关键的 SQLAlchemy 特有细节是每个过滤器如何转换为查询片段。该模块中的每个 `apply()` 方法都返回一个独立的 SQLAlchemy 布尔子句（如 `column == value` 或 `column.between(a, b)`）。

!!! note
    关联关系上的 `Is null` 过滤器求值为 `~column.has()`（用于多对一关联关系）或 `~column.any()`（用于一对多和多对多关联关系），而不是 `column.is_(None)`。因为关联关系属性并不是包含 `NULL` 值的标准列，其是否为空完全取决于是否存在关联行。

!!! note
    与 Beanie 和 MongoEngine 不同，SQLAlchemy 后端并未提供 `ArrayInFilter` 或 `ArrayNotInFilter`（即面向列表值列的“is one of”过滤器）。如果需要对基于 `TagsField` 的 JSON 或 ARRAY 列执行“is one of”过滤，你必须自行编写 `apply()` 逻辑。更多详情请查阅[自定义过滤器](../advanced/custom-filters.md)文档。

## 会话与事务

会话中间件为每个请求恰好打开一个会话，并将其安全地存储在 `request.state.session` 上。使用异步引擎（或 `async_sessionmaker`）时，该对象是一个 `AsyncSession`；否则是一个标准的 `Session`。请求所触及的每个组件都共享这一个会话。列表查询、表单中的关联关系查找，以及在钩子、动作或端点中运行的任何自定义逻辑，都在完全相同的事务中进行。无论底层引擎类型如何，你都可以统一获取它：

```python
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    @action(name="publish", text="Publish selected")
    async def publish(self, request: Request, pks: list[Any]) -> str:
        session: AsyncSession = request.state.session
        for post in await self.find_by_pks(request, pks):
            post.status = "PUBLISHED"
            session.add(post)
        await session.flush()
        return f"{len(pks)} post(s) published."
```

使用同步引擎时，`request.state.session` 是一个标准的 `Session`，调用 `session.flush()` 时不需要 `await`。前面代码片段的其余部分保持不变。你无需导入单独的 `get_session()` 依赖项。由于会话中间件会在调用路由处理器之前建立连接，因此在你的钩子或动作执行之前，会话就已附加到请求上。

**每个请求只提交一次。** 你绝不应手动调用 `session.commit()`。调用 `flush()`（或在执行只读查询时不做任何操作）就足够了。只要响应表明成功，会话中间件就会在路由处理器返回之后恰好提交一次会话。如果发生错误，中间件会自动回滚整个事务：

* 如果处理器抛出异常，会话会回滚，应用会重新抛出该异常。
* 如果处理器返回带有 `status_code >= 400` 的响应（例如表单校验失败），会话会回滚，服务器将原样返回该响应。这种回滚至关重要，因为此时事务中可能包含一次失败的 flush；若将其提交，可能会无意间持久化一条写入不完整的记录。
* 如果提交操作本身抛出异常（例如在 flush 时捕获到数据库约束冲突），会话会回滚并重新抛出该异常。

在处理器返回 2xx 或 3xx 响应的所有其他情况下，中间件会提交会话并释放连接。这一生命周期解释了为什么上文演示的 `publish` 动作无需显式的提交或关闭语句。会话中间件会在你的代码执行之前打开会话，并在响应离开视图之前完成提交或回滚操作。

## Pydantic 校验 {#pydantic-validation}

你可能使用纯 SQLAlchemy 模型，但仍希望在保存前依据某个 Pydantic schema 校验表单数据。在这种情况下，`starlette_admin.contrib.sqla.ext.pydantic.ModelView` 接受一个 `pydantic_model` 参数，以针对该 schema 执行校验，而不是依赖底层的 SQLAlchemy 列类型：

```python
from sqlalchemy import ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

engine = create_engine(
    "sqlite:///users.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip().split()) < 2:
            raise ValueError("Must include both first and last name (e.g. John Doe)")
        return v


admin = Admin(engine, title="Users Admin", secret_key="change-me")
admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
```

提交 `full_name="Madonna"`（单个单词）会导致 `validate_full_name` 方法校验失败。随后，新建或编辑表单会重新渲染，并将错误明确附加到 `full_name` 字段上。底层 SQLAlchemy 的 `String(100)` 列并没有这样的规则，该约束完全存在于 `UserIn` 这个 Pydantic 模型中。完整示例请参阅 [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)，其中还包含挂载到同一管理面板的另一个视图（`PostIn`）。

## 完整可运行示例


下面是一个完整的 SQLAlchemy 与 starlette-admin 集成示例。可运行版本请参阅 [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart)。

### 1. 安装依赖

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

`fastapi[standard]` 包包含 FastAPI CLI，运行 `fastapi dev` 即可启动开发服务器。

### 2. 创建应用

将以下代码保存为 `main.py`。出于演示目的，此脚本使用本地 SQLite 数据库（`blog.db`）；不过 starlette-admin 对 PostgreSQL、MySQL 和 SQLite 同时支持同步与异步引擎。

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette_admin import SlugField
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")


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
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

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

现在，你可以在浏览器中访问 [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)，查看并操作管理后台。

---

## 延伸阅读

* **[视图](../user-guide/views.md)**：探索与后端无关的 `BaseModelView` 配置选项。
* [过滤器](../user-guide/filters.md)：关于过滤器构建器及其 URL 格式的详细信息，均由过滤器注册表提供支持。
* [视图](../user-guide/views.md)：`ModelView` 全部配置选项的综合列表（与后端无关）。
* [SQLModel](sqlmodel.md)：围绕此后端的轻量封装，为表单添加 Pydantic 校验。
* [Beanie](beanie.md)：使用相同的 `ModelView` API 操作 MongoDB 数据库的指南。
* [Tortoise ORM](tortoise.md)：starlette-admin 内置的另一个关系型后端。
