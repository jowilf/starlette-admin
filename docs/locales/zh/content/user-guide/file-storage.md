---
title: 文件存储
description: 在 starlette-admin 中使用 LocalStorage 或兼容 S3 的后端存储来管理文件和图片上传。
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# 文件存储

`FileField` 和 `ImageField` 通过存储后端保存上传的文件，该后端由字段的 `storage` 参数设置。

只需创建一次存储后端，即可在所有将文件保存在同一位置的字段中复用。


## 最小示例

```python hl_lines="8 12 31"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///admin.sqlite")

local = LocalStorage(base_dir="uploads", name="local")


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=local, upload_folder="covers"),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Bookstore", secret_key="change-me")
admin.add_view(BookView(Book))
admin.mount_to(app)
```

当用户通过管理后台上传封面时，管理后台会：

* 将文件保存到 `uploads/covers/`
* 在 `cover` 列中存储一个 JSON 元数据对象

数据库从不保存文件本身、文件系统路径或二进制数据。


## 数据库中存储的内容

管理后台将一次文件上传表示为模型字段中的一个序列化的 [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) 对象。

```json
{
  "filename": "product-photo.jpg",
  "content_type": "image/jpeg",
  "size": 204800,
  "storage": "s3",
  "key": "uploads/products/a1b2c3_product-photo.jpg",
  "url": "https://..."
}
```

* `filename`：经过清理的原始文件名，用于显示
* `content_type`：上传时检测到的 MIME 类型
* `size`：文件大小（字节）
* `storage`：注册的后端名称，用于解析文件位置以生成 URL 和执行删除
* `key`：相对于存储的路径或对象键
* `url`：缓存的公开 URL

`LocalStorage` 存储空的 `url` 值，因为 URL 取决于当前请求。`S3Storage` 则根据你的配置存储公开 URL 或预签名 URL。

无论使用哪种后端，`FileField` 都会在渲染时用 `storage.url()` 重新生成 URL，而不是信任存储的值。

`ImageField` 会额外添加 `width` 和 `height`。

管理后台在存储每个文件名之前都会先用 `secure_filename` 进行清理：它会去除路径部分，并将 `[A-Za-z0-9_.-]` 之外的字符替换为 `_`。参见[安全](security.md)。


## 存储后端

### 本地存储

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | 必填 | 存储文件的根目录。如果不存在会自动创建。 |
| `name` | `str | None` | `"local"` | 标识后端的注册名称。使用多个实例时必须唯一。 |

管理后台通过以下路由提供文件服务：

```
/_files/{storage}/{path}
```

你无需任何额外的静态文件配置。

`LocalStorage.url()` 基于当前请求上下文构建 URL，因此存储的 `url` 字段保持为空，并按需重新计算。

!!! note
    代码示例参见 [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage)。

### Amazon S3 存储

```python
from starlette_admin.storage import S3Storage

s3 = S3Storage(
    bucket="my-bucket",
    prefix="admin/",
    region="eu-west-1",
    public=False,
)
```

安装可选依赖：

```bash
pip install starlette-admin[s3]
```

这会安装 `aiobotocore`。

| 参数 | 类型 | 默认值 | 描述 |
| --- | --- | --- | --- |
| `bucket` | `str` | 必填 | S3 存储桶名称。 |
| `prefix` | `str` | `"uploads/"` | 应用于每个已存对象键的前缀。 |
| `region` | `str` | `"us-east-1"` | 用于签名和 URL 生成的 AWS 区域。 |
| `access_key` 和 `secret_key` | `str | None` | `None` | 可选凭证。未提供时回退到默认的 AWS 凭证链。 |
| `public` | `bool` | `True` | 为 `True` 时返回公开 URL；为 `False` 时生成预签名 URL。 |
| `expires` | `int` | `3600` | 预签名 URL 的过期时间（秒）。 |
| `endpoint_url` | `str | None` | `None` | 自定义的兼容 S3 的端点，例如 MinIO、R2 或 B2。 |
| `name` | `str | None` | `"s3"` | 标识后端的注册名称。 |

当你提供 `endpoint_url` 时，管理后台按如下方式构建 URL：

```
{endpoint_url}/{bucket}/{key}
```

而不是使用 AWS 虚拟托管（virtual-hosted）格式。


!!! important
    文件字段必须映射到支持 JSON 的数据库列。数据库只保存元数据，文件本身由存储后端保存。


## 多文件（`multiple=True`）

在 `FileField` 或 `ImageField` 上设置 `multiple=True`，即可在一个字段中接受多个上传。

```python
from starlette_admin import FileField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/attachments", name="attachments")


class TicketView(ModelView):
    fields = [
        "id",
        "subject",
        FileField(
            "attachments",
            storage=local,
            upload_folder="tickets/",
            multiple=True,
        ),
    ]
```

数据库存储一个由 `FileInfo` 对象组成的 JSON 列表，管理后台会对每个文件独立地进行校验和存储处理。


!!! warning
    保存表单会用提交的文件替换整个文件列表。无法单独添加或删除某一个文件。要对单个文件进行生命周期管理，请使用带有自身 `FileField` 的内联模型。

!!! important
    不支持 `ListField(FileField(...))`。简单的集合请使用 `multiple=True`，结构化的文件数据请使用内联模型。

## 校验

校验按以下顺序执行：

1. `accept`
2. `max_size`
3. 自定义 `validators`

自定义校验器是一个可调用对象，接收请求、字段、一个 `UploadFile` 以及完整的表单提交值。它必须返回 `None` 或抛出 `ValueError`。

下面的示例使用 `filetype` 库校验实际的文件内容：

```python
import filetype
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.fields import BaseField

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_document_type(
    request: Request, field: BaseField, upload: UploadFile, form_values: dict
) -> None:
    upload.file.seek(0)
    try:
        header = upload.file.read(2048)
        kind = filetype.guess(header)
        detected = kind.mime if kind else "application/octet-stream"
    finally:
        upload.file.seek(0)

    if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
        )
```

!!! important "重置文件指针"
    检查前后务必用 `seek(0)` 重置文件指针，以便存储层能够读取完整文件。

!!! note
    校验器逐文件运行，因此在 `multiple=True` 时每个文件都会独立校验。`ImageField` 会在任何自定义校验器之前应用自身的图片校验。


!!! tip "最佳实践"
    使用 `accept` 和 `max_size` 进行轻量级校验。

    需要检查文件内容或实施应用特定规则时，请使用自定义校验器。

    安全敏感的校验不要依赖文件扩展名或 `Content-Type` 头。应改为使用 `filetype` 或 `python-magic` 之类的库检查内容。


## 文件清理的限制

`starlette-admin` 会将文件上传到存储后端并将 `FileInfo` 元数据写入数据库，但在失败或删除之后不会清理文件。由此带来两种行为：

* **事务失败：** 如果上传完成后数据库事务回滚，文件仍会留在存储后端中。存储写入没有回滚机制。
* **删除与更新：** 删除一行或替换文件会从数据库中移除 `FileInfo` 引用，但旧文件仍留在 `LocalStorage` 或 `S3Storage` 中。

这种设计保持了存储层的简单性，并防止应用层错误触发破坏性操作。代价是孤立文件会不断累积。为避免存储无限增长，请自行核对并清理这些文件。常见模式是用一个周期性后台任务，将存储后端中的键与数据库中仍然有效的 `FileInfo` 引用做差异比对。

### 事务型替代方案

如果你的应用需要文件存储操作与数据库写入保持事务一致性，请使用将文件存储与 SQLAlchemy 工作单元（unit of work）绑定的库。

请使用 [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file) 代替字段的 `storage=` 参数。它将文件的存储纳入 ORM 的 flush 与回滚周期，因此事务失败或行删除会撤销相应的文件写入。可运行的示例见 [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file)。

---

## 接下来

* **[字段](fields.md)：** `FileField` 和 `ImageField` 参考。
* **[导出与导入](export-import.md)：** 文件如何包含在导出压缩包中。
* **[安全](security.md)：** 自动清理与校验行为。
