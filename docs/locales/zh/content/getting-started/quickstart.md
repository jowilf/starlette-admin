---
title: 快速开始
description: 通过我们全面的快速入门指南，几分钟内即可为 FastAPI 和 Starlette 构建功能完备的 CRUD 管理界面。
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# 快速开始

几分钟内即可为一个博客构建功能完备的 CRUD 管理界面——表单、列表、搜索、导入和导出全部由你的数据模型自动生成。

## 安装

使用你偏好的包管理器安装所需的包：

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    `fastapi[standard]` 包包含 FastAPI CLI，运行 `fastapi dev` 即可启动开发服务器。

## 完整示例

创建一个名为 `main.py` 的文件，并添加以下代码：

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## 运行应用

启动开发服务器：

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

打开浏览器并访问 [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin)。

在侧边栏中选择 **Posts**，然后选择 **Create**。现在你即可访问分页列表、详情、创建、编辑和删除页面。系统会根据你的模型定义自动生成所有这些界面。

## 工作原理

以下各节将解释该应用的核心组件。

### 模型

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

这段代码使用了标准的 SQLAlchemy 2.0 写法。starlette-admin 包会读取映射到这些属性的列元数据，以确定需要生成的具体 HTML 输入控件。例如，它会为 `str` 生成文本输入框，为 `bool` 生成复选框，为 `datetime` 生成日期时间选择器。

### 视图

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` 是该资源的核心对象。`fields` 属性控制在列表和表单中显示哪些列，而 `searchable_fields` 用于启用搜索栏。关于 `Post` 在管理仪表盘中的外观和行为的所有配置都包含在这一个类中。

!!! note
    本示例从 `starlette_admin.contrib.sqla` 导入 `ModelView`，因为它依赖 SQLAlchemy。如果你使用其他后端（例如 Beanie、MongoEngine 或 Tortoise ORM），则必须从对应的 contrib 包导入 `ModelView`。配置 API 在所有受支持的后端中保持一致。

### Admin 实例

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

`Admin` 类将数据库引擎与用户界面连接起来。

* `add_view` 将你的视图注册到侧边栏。可选的 `icon` 参数接受任何有效的 [Font Awesome](https://fontawesome.com/icons) 类名。
* `mount_to` 将管理应用挂载到你的 FastAPI 或 Starlette 应用的 `/admin` 路径下。

!!! warning
    `secret_key` 参数用于对承载会话数据的 cookie 进行签名，其中包括 Flash 消息和 CSRF 保护。在生产环境中，你必须将示例值替换为一个较长的、随机的且经过安全生成的字符串。切勿在线上部署中使用占位符值。

## 添加第二个模型

你可以注册任意数量的模型。例如，要添加 `Tag` 模型及其对应的视图，请定义相应的类并再次调用 `add_view`：

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

刷新浏览器窗口，你会看到 **Posts** 和 **Tags** 同时出现在侧边栏中。每个资源现在都拥有功能完备的列表、创建、编辑和删除页面。

---

## 后续步骤

* **[核心概念](concepts.md)：** 了解本文所介绍概念的术语，以便更好地浏览用户指南。
* **[Admin](../user-guide/admin.md)：** 探索所有 `Admin(...)` 选项，包括品牌标识、主题、认证、安全和国际化。
* **[视图](../user-guide/views.md)：** 浏览可用于自定义数据展示的全部 `ModelView` 配置选项。
