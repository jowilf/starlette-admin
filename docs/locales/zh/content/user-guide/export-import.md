---
title: 导出与导入
description: 在 starlette-admin 中启用 CSV、JSON 和 PDF 导出功能，并支持带校验的批量数据导入。
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# 导出与导入

每个列表页面都允许用户将数据导出到文件，以及从文件导入数据，因此你无需编写自定义路由。

## 概述

* **导出：** 用户点击工具栏按钮，然后设置范围、字段、格式和文件名。
* **导入：** 用户点击工具栏按钮打开三步向导：上传、预览和结果。
* **格式：** 开箱即用地支持 CSV、JSON、XLSX、ODS、YAML、PDF 以及自定义格式。
* **Upsert：** 导入可选择按主键匹配并更新现有记录。
* **集成：** 两项功能都可配合过滤、排序、行选择以及基于存储的字段使用。
* **无需额外端点：** 所有功能均随视图提供。

## 最小示例

```python hl_lines="23 24"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///store.sqlite")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column()

class ProductView(ModelView):
    fields = ["id", "name", "description", "price"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))

```

现在，`ProductView` 会在列表工具栏中显示一个**导出**按钮和一个**导入**按钮。每个对话框只提供你在 `exporters` 和 `importers` 中列出的格式。

---

## 启用导出

`exporters` 属性以普通扩展名字符串的形式列出要提供的格式：

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

默认值为 `["csv", "json"]`。下表列出了每种内置格式及其所需的软件包。`csv`、`tsv` 和 `json` 格式不需要额外依赖。其他所有表格格式都使用 `tablib`，而 `pdf` 使用 `reportlab`。未知的格式字符串，或者所需软件包尚未安装的格式，会在启动时抛出错误。

| 格式 | 安装要求 |
| --- | --- |
| `csv`、`tsv`、`json` | 核心已包含 |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`、`html`、`latex`、`jira`、`rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### 覆盖格式选项

每个格式字符串都会解析为一个带有合理默认值的预配置导出器实例。当某个格式需要不同的设置时，请传入导出器实例而不是字符串。同一个列表中可以混用字符串和实例：

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` 将关键字参数转发给 `csv.writer`，并接受一个 `escape_formulas` 参数。`TablibExporter(format, **kwargs)` 覆盖所有 tablib 格式，并将关键字参数转发给 `tablib.Dataset.export()`。

!!! warning
    公式转义默认关闭。如果导出的字段可能包含用户提供的字符串，请在 `CsvExporter`、`TsvExporter` 或 `TablibExporter` 上设置 `escape_formulas=True`，以防他人在电子表格应用中打开文件时发生公式注入。参见[公式注入](security.md#formula-injection)。

导出默认开启。只要 `exporters` 列表不为空，工具栏中就会显示**导出**按钮。要限制哪些用户可以导出，请覆盖 `can_export(request)` 方法：

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### 导出对话框

导出是一个内置的全局动作。选择**导出**会打开一个对话框，用户可在下载之前在其中配置导出。

* **范围：** 要导出的内容。选项包括“选中的行”（勾选了行时的默认值）、“全部匹配的行”（可通过全选横幅使用）以及“当前页”（未选中任何内容时的默认值）。
* **字段：** 每个可导出的字段对应一个复选框。取消勾选复选框即会去掉该列。标记为 `exclude_from_export=True` 的字段永远不会出现在这里。
* **格式：** `exporters` 中的每种格式对应一个条目。
* **文件名：** 默认为视图 key。服务器会自动追加文件扩展名。

每种范围都会遵循列表页面当前的搜索、过滤器和排序方式，因此用户看到的就是他们导出的内容。

### 行数上限

```python
from starlette_admin.export import ExportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    export_config=ExportConfig(max_rows=50_000),
)

```

`ExportConfig.max_rows` 默认为 100,000。该上限适用于所选范围实际会产生的行数，并且管理后台会在获取任何行之前检查数量。当数量超过上限时，管理后台会闪烁错误提示并重定向回列表页面，而不生成文件。这样可以避免在大表上进行宽泛的无过滤导出时挂起请求。设置 `max_rows=None` 可移除该限制。

---

## 启用导入

`importers` 属性的工作方式与 `exporters` 完全相同，接受格式字符串：

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

内置的导入格式有 `csv`、`tsv`、`json`、`yaml`、`xlsx`、`xls`、`ods`、`dbf` 和 `html`，其依赖项与对应的导出格式相同。要覆盖某个格式的默认设置，请传入导入器实例，例如来自 `starlette_admin.importers` 的 `CsvImporter(delimiter=";")`。

导入默认开启，使用 `["csv", "json"]`。只要 `importers` 列表不为空，工具栏中就会显示**导入**按钮。要限制哪些用户可以导入，请覆盖 `can_import(request)` 方法：

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### 导入向导

选择**导入**会打开一个三步向导。在最终确认之前不会向数据库写入任何内容，并且在各步骤之间服务器上不会保存任何文件：浏览器持有该文件并在每一步重新提交它。

1. **上传：** 选择一种格式，选择一个文件，并可选择勾选**按主键更新现有记录**。勾选后，主键与现有记录匹配的行会更新该记录而不是创建新记录。否则，每一行都会被新建。
2. **预览：** 提交上传后会执行一次完整的校验流程，但不写入任何内容。向导会显示摘要、列映射、示例行和详细的错误表格。
3. **结果：** 向导提交导入并报告最终创建、更新和跳过的记录数量。在预览中校验失败的行会被跳过。

!!! tip
    若要让后端生成主键，请在预览映射中清除主键列。这样导入的行将不带主键值，因此重新导入你导出的文件时会创建全新记录，而不会因过期的 ID 而失败。

### 上传与行数上限

```python
from starlette_admin.importers import ImportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    import_config=ImportConfig(max_rows=50_000),
)
```

导入端点沿用了导出的行数上限机制。`ImportConfig.max_rows` 默认为 100,000，并在创建任何记录之前强制执行。管理后台会在预处理阶段统计上传文件的行数，对超过上限的文件返回 HTTP 400 错误予以拒绝。设置 `max_rows=None` 可移除该限制。`ImportConfig.max_upload_size` 默认还会将上传大小限制在 10 MB 以内。

### 表头匹配

向导首先将文件的每个表头与字段的 `label` 匹配，然后再与其 `name` 匹配。包含列 `Name` 的文件和包含列 `name` 的文件都会映射到名为 `name` 的字段。无法匹配的列会被忽略，而没有匹配列的字段将收到 `None`。

## 文件字段

包含基于存储的 `FileField` 或 `ImageField` 的视图会导出为 ZIP 压缩包，因此文件内容会随行数据一同传输：

```python
from sqlalchemy import Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///catalog.sqlite")
covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")

class Base(DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[dict | None] = mapped_column(JSON, nullable=True)

class ProductView(ModelView):
    fields = [
        "id",
        "name",
        ImageField("photo", storage=covers_storage, upload_folder="products"),
    ]

Base.metadata.create_all(engine)
admin = Admin(engine, title="Catalog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

将 `ProductView` 导出到 CSV 会生成具有以下结构的 `export.zip`：

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

`export.csv` 中的 `photo` 列保存文件相对于 ZIP 的路径 `assets/<storage-name>/<key>`，这样 CSV 在电子表格应用中仍可读。管理后台会从相应的存储后端获取每个被引用的文件，并将其打包到 `assets/` 目录下。

导入不接受 ZIP 压缩包。`FileField` 和 `ImageField` 始终被排除在导入之外，因为它们默认 `exclude_from_import=True`，所以向导在上传时会忽略 `photo` 列。请重新导入纯数据文件，然后通过创建或编辑表单附加文件。


## 编写自定义导出器

要编写自定义导出器，请继承 `BaseExporter` 并实现 `generate` 方法。基类会处理 ZIP 打包、文件下载和响应头：

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField

class MarkdownExporter(BaseExporter):
    content_type = "text/markdown"
    extension = "md"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        lines = [
            " | ".join(f.label or f.name for f in fields),
            " | ".join("---" for _ in fields),
        ]
        for row in rows:
            lines.append(" | ".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

`rows` 数据经过预先清理：管理后台会先将每个 `FileField` 和 `ImageField` 的值替换为其相对于 ZIP 的路径字符串，因此你的 `generate` 方法永远不会接触文件字典。将 `MarkdownExporter()` 注册到你的 `exporters` 列表中，即可将其显示在格式下拉框中。

## 编写自定义导入器

要编写自定义导入器，请继承 `BaseImporter` 并将 `parse` 实现为一个异步生成器，为每一行产出一个字典：

```python
import json
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext

class NdjsonImporter(BaseImporter):
    extension = "ndjson"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        for line in ctx.content.decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
```

---

## 接下来

* **[文件存储](file-storage.md)：** 配置导出 ZIP 压缩包中引用的存储后端。
* **[安全](security.md)：** 导出行数上限和导入上传大小限制。
* **[动作](actions.md)：** 在导出与导入之外，添加批量动作和行级动作。
