---
title: 安全
description: 了解 starlette-admin 的内置安全特性，包括 CSRF 保护、文件上传安全性和访问控制。
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# 安全

`starlette-admin` 针对运行管理面板所伴随的风险内置了安全保障。只要实例化 `Admin` 类，针对跨站请求伪造（CSRF）的防护以及对导出和导入载荷大小的限制便会立即生效。

这些默认设置可以增强界面对常见攻击的防御能力，但并不能替代标准的部署安全措施。传输层安全（HTTPS/TLS）、网络访问控制、用户认证（参见[认证](auth.md)）、依赖项更新和安全审查仍需由你负责。本页涵盖自动启用的防护措施、需要你自行配置的选项，以及生产环境中必需的 `secret_key` 设置。

## 开箱即用的防护措施

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

即使不设置任何安全参数，管理实例也能抵御多种常见漏洞：

* **CSRF 保护：**对所有表单和 jQuery AJAX 调用生效，包括行级动作和确认对话框。
* **Flash 消息：**通过签名 cookie 传递，因此不需要 `SessionMiddleware`。
* **文件名净化：**应用于经过存储后端的每一次文件上传。
* **图片内容校验：**在已安装 Pillow 的情况下，以字节级别校验 `ImageField` 上传的内容。
* **导出限制：**每个请求最多导出 100,000 行，以防资源耗尽和拒绝服务。
* **导入限制：**每个请求最多 10 MB，以限制内存耗尽。

另有一项防护可用，但默认关闭：在 CSV 和电子表格导出（XLSX、XLS、ODS）中启用转义，以防止电子表格公式注入。参见[公式注入](#formula-injection)。

以下章节将说明这些防护措施，以及如何调整由你掌控的阈值。

## 密钥

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

`secret_key` 是签署两个 cookie 的加密根基：CSRF 令牌和 Flash 消息 cookie。两者均使用 [itsdangerous](https://itsdangerous.palletsprojects.com/)，因此客户端可以读取这些 cookie，但没有密钥便无法伪造或篡改其中的载荷。

!!! warning "在生产环境中务必显式设置密钥"
    如果省略 `secret_key`，`Admin` 实例会在启动时生成随机密钥并发出 `UserWarning`。这在本地演示中没有问题，但在多进程（worker）部署中会导致故障。当你运行多个 worker（例如 `uvicorn --workers 4`、Gunicorn 或多个容器）时，每个进程都会生成自己的密钥。此时，由提供表单的 worker 签署的 CSRF 令牌，在另一个 worker 处理提交时将无法通过验证，导致一部分请求看似随机地出现无效 CSRF 令牌错误。在扩展到单个进程之外之前，请显式设置 `secret_key`。

## CSRF 保护

`CSRFMiddleware` 采用签名的双提交 cookie 模式来防范跨站请求伪造。它会在安全的 HTTP 方法（`GET`、`HEAD`、`OPTIONS` 和 `TRACE`）上颁发 `starlette_admin_csrftoken` cookie。对于变更型请求，它会对照 `X-CSRFToken` 请求头或 `csrftoken` 隐藏表单字段来验证该 cookie。

每个内置管理模板（`create`、`edit` 和 `login`）都会为你渲染该隐藏字段：

```jinja
{{ csrf_input(request) }}

```

捆绑的 JavaScript 还会将该请求头附加到每个 jQuery AJAX 调用上，因此行级动作和其他异步交互无需额外代码即可受到保护。仅当你在默认模板之外构建自定义表单时，才需要自行调用 `csrf_input(request)`。参见[自定义视图](custom-views.md)。

## 文件上传

经过[存储](file-storage.md)后端的每一次上传都会使用 `secure_filename` 进行净化。包含目录遍历的路径部分会被剔除，`[A-Za-z0-9_.-]` 之外的字符会变为下划线（`_`）。此机制无法关闭。

使用 `accept` 和 `max_size` 按字段设置内容类型和大小限制：

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

如果不设置这两项，`FileField` 会接受任意类型和大小的文件。`ImageField` 是例外：它默认为 `accept="image/*"`，并且在已安装 Pillow 的情况下会预先附加一个校验器，用 `PIL.Image` 打开上传的文件以确认字节确实能解码为图像，而不是信任浏览器提供的元数据。

!!! important "在网络服务器层面强制实施请求大小限制"
    不要仅仅依赖 `max_size`。这项应用层检查只有在服务器接收到完整请求载荷之后才会运行。为防止拒绝服务（DoS）攻击，请在网络服务器配置中限制请求体大小，例如 NGINX 中的 `client_max_body_size` 或负载均衡器上的等效设置。

!!! warning "文件扩展名和 Content-Type 请求头可能被伪造"
    `accept` 属性依赖文件名扩展名和浏览器提供的 `Content-Type` 请求头，而攻击者可以对两者同时进行伪造。看起来像 `invoice.pdf` 的文件可能携带可执行载荷。

    对于非图片文件，请将 `accept` 与检查文件魔数（magic bytes）的自定义校验器配合使用。[`filetype`](https://github.com/h2non/filetype.py) 和 [`python-magic`](https://github.com/ahupp/python-magic) 等库可以验证文件的真实格式：

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

    使用 `FileField(..., validators=[validate_document_type])` 应用该校验器。完整实现请参见 [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage)。

## 导出限制

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| 属性 | 默认值 | 描述 |
| --- | --- | --- |
| `max_rows` | `100_000` | 每次导出请求允许的最大行数。超出限制时会闪现一条错误消息，并将用户返回列表视图。设为 `None` 可移除该限制。 |
| `restrict_url_download` | `True` | 适用于仅引用 URL 的文件。将导出 ZIP 限定为来源与管理后台 `base_url` 匹配的文件。 |
| `max_download_size` | `20 MB` | 打包进导出 ZIP 的纯 URL 下载内容的最大大小。超过该大小的文件会被跳过并记录一条警告。 |
| `safe_download_url` | `None` | 签名为 `(url, request) -> str` 的自定义回调。 |

关于 ZIP 包的构建方式，请参见[导出与导入](export-import.md)。

### 公式注入 {#formula-injection}

电子表格软件会将以 `=`、`+`、`-` 或 `@` 开头的单元格值视为公式。如果不受信任的用户将 `=HYPERLINK(...)` 之类的载荷保存到导出字段中，那么当管理员打开该文件时，电子表格应用程序就会执行它。这种现象称为 CSV 注入，也称公式注入。

由于导出的值会按照其在数据库中的存储方式原样写出，公式转义**默认关闭**。CSV 导出器和 Tablib 电子表格导出器（`xlsx`、`xls` 和 `ods`）都接受 `escape_formulas` 参数。启用后，任何以触发字符开头的字符串都会获得一个前导单引号（`'`），从而迫使应用程序将该值渲染为纯文本。

!!! warning "对用户提供的数据开启公式转义"
    只要有任何非管理员账户能够向导出字段写入数据，就应设置 `escape_formulas=True`。否则，攻击者控制的值可能在有人于本地打开文件时执行系统命令或窃取数据。

要启用转义，请用显式指定的导出器实例替换格式字符串：

```python
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.export import CsvExporter, TablibExporter


class ProductView(ModelView):
    exporters = [
        CsvExporter(escape_formulas=True),
        TablibExporter("xlsx", escape_formulas=True),
        "json",
    ]
```

## 导入限制

```python
from starlette_admin.importers import ImportConfig

admin = Admin(
    engine,
    title="My Admin",
    import_config=ImportConfig(
        max_upload_size=5 * 1024 * 1024,
        max_rows=50_000,
    ),
)
```

| 属性 | 默认值 | 描述 |
| --- | --- | --- |
| `max_upload_size` | `10 MB` | 在请求到达时立即检查，早于任何解析步骤。 |
| `max_rows` | `100_000` | 每次导入请求允许的最大行数。管理后台会在预检阶段统计载荷行数，并在创建任何数据库记录之前以 HTTP 400 响应拒绝更大的文件。设为 `None` 可移除该限制。 |

导入功能会直接拒绝 ZIP 归档，从而消除了该端点上 ZIP 炸弹攻击的风险。`FileField` 和 `ImageField` 也被排除在批量导入之外（因为默认 `exclude_from_import=True`），用户只能通过新建或编辑表单逐一附加文件。

## 本页未涵盖的内容

内置防护解决的是管理代码库内部的风险，并不能保证整体架构的安全。以下运维措施不在 `starlette-admin` 的范围之内，仍需由你负责：

* **传输安全：**通过 HTTPS 提供管理面板服务。CSRF 和 Flash cookie 经过了签名，但并未加密，因此任何截获明文 HTTP 流量的人都可以读取它们。
* **认证与授权：**在附加 `AuthProvider` 之前，`Admin` 实例是公开的。没有它，每个端点和路由都处于开放状态。参见[认证](auth.md)。
* **网络暴露面：**如果管理面板无需公开访问，请将其置于防火墙、VPN 或 IP 允许列表之后。
* **依赖项维护：**关注安全公告，保持 `starlette-admin`、Starlette、你的 ORM 驱动程序及其余依赖项处于最新版本。
* **认证后的操作：**CSRF 和上传校验并不会限制已登录用户可以执行的操作。细粒度的访问控制完全来自你在 `is_accessible`、`can_create`、`can_edit` 和 `can_delete` 中编写的权限检查。参见[认证](auth.md)。

请将本页视为配置管理包的指南，而不是保护整个生产部署的核对清单。

---

## 下一步

* **[导出与导入](export-import.md)：**导出对话框、导入预览的生命周期以及 ZIP 包结构。
* **[文件存储](file-storage.md)：**为 `FileField` 和 `ImageField` 配置存储后端的常见模式。
* **[认证](auth.md)：**添加认证提供方后，`secret_key` 如何管控登录会话与 CSRF 校验。
