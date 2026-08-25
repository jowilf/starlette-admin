---
title: 安装
description: 了解如何安装 starlette-admin 及其可选依赖，为你的 FastAPI 或 Starlette 应用构建管理界面。
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# 安装

使用你偏好的包管理器安装 **starlette-admin**。

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin 要求 **Python 3.11 或更高版本**。

核心包本身与后端无关。要为你的应用构建管理界面，请在基础包之外，为你的数据层（如 SQLAlchemy、Beanie、MongoEngine 或 Tortoise ORM）安装相应的集成。

## 包含的依赖

基础安装已包含运行管理界面所需的一切，默认不安装任何可选依赖。

| 依赖 | 用途 |
| --- | --- |
| [Starlette](https://www.starlette.io/) | 承载管理应用。 |
| [Jinja2](https://jinja.palletsprojects.com/) | 为列表、详情和表单页面提供模板引擎。 |
| [python-multipart](https://github.com/Kludex/python-multipart) | 解析表单提交和文件上传。 |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | 为 CSRF 令牌和 Flash 消息对 cookie 进行签名。 |

基于 FastAPI 构建的应用无需额外的集成，因为 FastAPI 构建于 Starlette 之上。只需将管理界面挂载到你现有的 FastAPI 应用即可。

## 可选依赖

starlette-admin 提供以下可选依赖：

- `pdf`：添加 PDF 导出支持（[reportlab](https://www.reportlab.com/)）。
- `i18n`：添加国际化支持（[Babel](https://babel.pocoo.org/)）。
- `tinymce`：添加富文本编辑器支持。会安装 [nh3](https://nh3.readthedocs.io/)，用于清理 `TinyMCEEditorField` 提交的 HTML。
- `s3`：添加 S3 兼容对象存储支持。会安装 [aiobotocore](https://aiobotocore.readthedocs.io/)，用于向 AWS S3 以及 MinIO 等兼容对象存储服务进行异步上传。

将一个或多个可选依赖与 starlette-admin 一起安装：

=== "pip"

    ```bash
    # Install the `pdf` extra.
    pip install "starlette-admin[pdf]"

    # Install multiple extras.
    pip install "starlette-admin[i18n,pdf,s3]"
    ```

=== "uv"

    ```bash
    # Install the `pdf` extra.
    uv add "starlette-admin[pdf]"

    # Install multiple extras.
    uv add "starlette-admin[i18n,pdf,s3]"
    ```

## 从源码安装

要使用尚未发布的最新更改，请直接从 GitHub 仓库安装该包。

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## 后续步骤

- **[快速开始](quickstart.md)**：使用真实数据构建你的第一个管理界面。
- **[核心概念](concepts.md)**：了解 starlette-admin 背后的核心架构与设计原则。
