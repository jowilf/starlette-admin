---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# 使用 starlette-admin 在 5 分钟内为 FastAPI 添加管理后台

_2026-07-13_

你的 API 已经上线。现在，团队里有人需要编辑它背后的数据：修正某条记录里的错别字、下架一篇文章，或者查一下用户到底提交了什么。常见的几种标准做法往往代价高昂：

| 方案                       | 缺点                                                                                                       |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **自建 CRUD 前端**         | 构建和维护需要耗费数周的开发时间。                                                                          |
| **直接访问数据库**          | 会带来巨大的安全和数据完整性风险。                                                                          |
| **Django Admin / Flask Admin** | 要么迫使你重写整个框架，要么依赖同步 WSGI，从而阻塞你的异步 ASGI 应用。                                     |
| **starlette-admin**        | **零前端代码，即刻挂载到你的应用上。**                                                                      |

`starlette-admin` 适用于任何基于 Starlette 的应用，而 FastAPI 恰好正是这样的应用。

本指南将带你从一个空文件开始，在 5 分钟内搭建出一套可用的后台管理系统。你将构建分页列表、搜索功能、可排序的列、由现有 Pydantic 模型校验的创建与编辑表单、删除确认以及 CSV 导出——所有这些都直接由一个 SQLAlchemy 模型生成。

完整的可运行代码位于 [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>)。

## 第 1 分钟：安装

你需要三个软件包：管理后台框架、ORM，以及 FastAPI 本身。

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic 随 FastAPI 一同附带，这一点在后面会变得重要：管理后台可以复用你的 API 用于校验的同一套模型。

## 第 2 和第 3 分钟：完整的应用

创建 `main.py`。这就是整个应用：

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)
```

注意这里省去了什么：没有模板，没有管理页面的路由处理器，没有序列化器，也没有字段配置。`starlette-admin` 会读取 SQLAlchemy 的列元数据并自动推导出整个界面：两个 `String` 列对应带长度限制的文本输入框，`Text` 内容对应多行文本域，`published_at` 对应日期时间选择器。

三处高亮显示的代码行是你仅有的集成点。`Admin` 负责绑定数据库引擎，`add_view` 把模型注册到侧边栏，`mount_to` 则将一切挂载到你现有的 FastAPI 应用之下的 `/admin` 路径。你的 API 路由保持原样；管理后台只是作为一个被挂载的子应用运行。

## 第 4 分钟：运行

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

打开 [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)，并在侧边栏中点击 **Post**。开箱即用，你会得到：

- 所有文章的分页、可排序的列表视图。
- 创建与编辑表单，并按列类型配备了正确的输入部件。
- 每条记录的详情视图页面。
- 附带确认对话框的批量删除功能。
- 针对当前列表的 CSV 和 Excel 导出。

你的 API 依旧正常对外提供服务。访问 [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) 即可确认一切完好无损。

## 第 5 分钟：让它如同手工打造

默认视图已经提供了完整的 CRUD 界面，但一套真正的后台管理系统值得精心定制：属于你的字段顺序、表单布局和搜索行为。对 `ModelView` 进行子类化，正是 `starlette-admin` 释放全部潜力的地方。用一个配置好的视图替换 `add_view` 调用：

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))
```

这一个类带来了四项强大的升级：

- **`SlugField(populate_from="title")`**：随着操作员输入标题自动生成 slug，你这边无需编写任何自定义 JavaScript。
- **`ComputedField`**：渲染数据库中并不存在的值。字数统计由一个普通的 Python 可调用对象在渲染时计算得出。
- **`form_layout`**：将表单排布成合乎逻辑的行：标题与 slug 并排，内容占满整行宽度，发布日期位于其下。
- **`search_auto_submit`**：操作员输入时，列表即会在 `searchable_fields` 中定义的所有列上动态过滤。

## 拒绝无效数据：直接使用你已有的模型

操作员难免犯错，这意味着管理后台需要在服务端执行你的规则。优势在于，这些规则你已经写好了。每个 FastAPI 项目都用 Pydantic 模型来校验请求体，因此在你的代码库中，一定存在一个类似下面这样的模型：

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v
```

与其把校验逻辑写两遍，不如把你现有的模型直接交给管理后台。`ext.pydantic` 扩展提供了一个 `ModelView`，它会在每次表单提交抵达数据库之前，先通过一个 Pydantic 模型对其进行处理。把你的 `ModelView` 导入指向该扩展，保持 `Admin` 原样不动，再传入这个模型即可：

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView): ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)
```

`PostView` 的主体保持完全一致；通过新的导入，发生变化的仅仅是它的基类。

这套集成天衣无缝。创建和编辑时，每一条约束都会生效：长度边界、slug 正则表达式，以及自定义的 `field_validator`。每个 Pydantic 错误都会直接映射回对应的表单字段并就地内联渲染，与手工打造的表单完美一致。请务必让 `id` 在模型中保持可选，这样起初没有 ID 的创建表单才能照常通过校验。

由此确立了单一事实来源。当你的 API 模型新增一条规则时，管理后台在下一次请求时便会执行它，无需对管理端代码做任何修改。

## 还剩一分钟？给文章加上作者

真实数据离不开关系，而管理后台会以同样的零配置方式处理它们。添加一个 `User` 模型，并将它与 `Post` 关联起来：

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")
```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")
```

按照同样的基于模型的方式注册用户模型。`EmailStr` 和 `HttpUrl` 会自动提供格式校验，而 `email-validator` 已随 `fastapi[standard]` 一并提供：

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
```

由于这一次没有任何需要配置的内容，可以直接使用扩展的 `ModelView`，无需再进行子类化。

最后，往 `PostIn` 中加入两行代码，把作者设为必填项：

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User
```

`user: User` 没有默认值，也就是说，缺少作者的文章会像其他任何校验错误一样遭到拒绝。这里的类型之所以是 SQLAlchemy 的 `User` 类本身，是因为管理后台会在校验开始之前先把选中的 ID 解析为一个 ORM 实例。这正是必须设置 `arbitrary_types_allowed` 的原因（`ConfigDict` 从 `pydantic` 导入）。

接下来，把 `"user"` 加入 `PostView.fields` 和 `form_layout`，让作者显示在文章表单里。这个字段不是普通的下拉框，而是一个带有服务端自动补全的选择框，会随着操作员的输入实时搜索你的用户；同时，用户详情页面还会链接回每一篇相关文章。

!!! note
`create_all` 不会修改已有的表，因此重启之前你需要删除 `blog.db`，才能用上新添的 `user_id` 列。

## 部署之前

!!! warning
`secret_key` 参数用于为 CSRF 保护和Flash 消息所使用的会话 Cookie 签名。部署之前，请把其中的占位符替换为你配置中的长随机值，并确保从环境变量加载它，而不是硬编码在源代码里。

!!! note
lifespan 中的 `Base.metadata.create_all(engine)` 只是为快速上手提供的便利。在生产项目中，你的表应由迁移工具（如 Alembic）管理。去掉那个调用，让 `Admin` 直接指向你现有的引擎即可。`starlette-admin` 从不修改你的表结构；它只会读取和写入数据行。

## 这套机制可以扩展到演示之外

上面的一切只用到两个模型，但这些一模一样的 `ModelView` 机制足以支撑一个庞大的后台管理系统。你可以轻松实现文件与图片上传、[支持基于角色的访问控制的认证](../../user-guide/auth.md)、[自定义过滤器](../../user-guide/filters.md)、[行级和批量动作](../../user-guide/actions.md)以及全面的 [i18n](../../user-guide/i18n.md)。每当内置行为力有不逮时，每一个查询和生命周期步骤都提供了可供覆盖的钩子。[软删除与回收站视图](soft-deletes-trash-view.md)这类模式正是借助这种灵活性构建出来的。

---

## 下一步

- **[核心概念](../../getting-started/concepts.md)：**你刚刚构建之物背后的术语体系，帮助你顺畅地阅读其余文档。
- **[视图](../../user-guide/views.md)：**深入剖析每一个 `ModelView` 选项以及权限钩子。
- **[FastAPI 的软删除与回收站视图](soft-deletes-trash-view.md)：**第一个高级配方，直接构建在本文介绍的覆盖钩子之上。
