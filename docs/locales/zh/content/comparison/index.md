---
title: starlette-admin、Django Admin 与 Flask-Admin 对比
description: 对 starlette-admin、Django Admin 与 Flask-Admin 的并列对比，涵盖 Web 技术栈、支持的 ORM、功能深度与取舍。
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

# starlette-admin、Django Admin 与 Flask-Admin 对比

Django Admin、Flask-Admin 与 starlette-admin 解决的是同一个问题：它们根据数据模型生成可直接投入生产的管理界面，让你不必手写 CRUD 页面。三者的差异在于面向的 Web 技术栈、支持的 ORM，以及内置了多少功能、又把多少留给你自己实现。

本页面对三者进行比较。如果你已经熟悉 Django Admin 或 Flask-Admin，希望获得一份直接的 API 对照，请前往对应的迁移指南：

* [从 Django Admin 迁移](django-admin.md)
* [从 Flask-Admin 迁移](flask-admin.md)

## 定位概览

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Web 框架** | 仅 Django | 仅 Flask | Starlette、FastAPI，以及任何可挂载子应用的 ASGI 应用 |
| **执行模型** | 同步（以 WSGI 为主） | 同步（WSGI） | 异步优先（ASGI） |
| **数据层** | 仅 Django ORM | SQLAlchemy、MongoEngine、peewee、pymongo | SQLAlchemy、SQLModel、MongoEngine、Beanie、Tortoise ORM，或[自定义后端](../integrations/custom-backend.md) |
| **UI 工具集** | Django 模板、经典管理主题 | Bootstrap 2/3/4 | [Tabler](https://tabler.io)（Bootstrap 5）、深色模式、[自定义主题](../advanced/custom-themes.md) |
| **是否随框架附带** | 是，Django 的一部分 | 否，独立软件包 | 否，独立软件包 |
| **认证** | 通过 `django.contrib.auth` 内置 | 自行提供（`is_accessible`） | 可插拔的 [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md)，用户存储可自行接入 |

## 各框架的适用场景

### Django Admin

Django Admin 适合原生 Django 应用。它成熟稳定，并与 `django.contrib.auth` 集成，因此无需任何配置即可获得用户、分组、模型级权限和变更历史。它只能在 Django 内运行。

### Flask-Admin

Flask-Admin 把自动生成带到了 Flask，并推广了 `ModelView` 配置风格。它是同步的，且与 Flask 绑定，因此不能运行在异步技术栈上。

### starlette-admin

starlette-admin 面向异步 Python 技术栈。如果你的应用使用 FastAPI 或 Starlette，只需把 admin 挂载到应用上，它就会在同一个事件循环中运行。它兼容 SQL 与 NoSQL 数据层，保留了源自 Flask-Admin 的 `ModelView` 配置风格，并具备 Django Admin 用户所期待的功能深度：内联表单、批量动作、按请求权限和国际化。

## 功能矩阵

**图例：**

* **是：** 内置
* **部分：** 可通过第三方软件包或自定义代码实现
* **否：** 不提供

| 功能 | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| 自动生成的 CRUD 视图 | **是** | **是** | **是** |
| 全文搜索 | **是** `search_fields` | **是** `column_searchable_list` | **是** [`searchable_fields`](../user-guide/filters.md) |
| 列过滤器 | **是** `list_filter` | **是** `column_filters` | **是** [可视化过滤器构建器](../user-guide/filters.md)，支持 `AND`/`OR` 分组 |
| 排序与默认排序 | **是** | **是** | **是** [`sortable_fields`、`fields_default_sort`](../user-guide/views.md#search-and-sort) |
| 列表视图中的内联编辑 | **是** `list_editable` | **是** `column_editable_list` | **是** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| 关联模型内联表单 | **是** `TabularInline` / `StackedInline` | **是** `inline_models` | **是** [`InlineModelView`](../user-guide/inline-forms.md) |
| 批量动作 | **是** `actions` | **是** `@action` | **是** [`@action`](../user-guide/actions.md)，带确认对话框与自定义表单 |
| 行级动作 | **部分** 自定义模板 | **部分** 自定义格式化器 | **是** [`@row_action`、`@link_row_action`](../user-guide/actions.md#row-actions) |
| 数据导出 | **部分** `django-import-export` | **是** CSV 及其他格式 | **是** [CSV、JSON、Excel、PDF](../user-guide/export-import.md) |
| 数据导入 | **部分** `django-import-export` | **否** | **是** [CSV、JSON、Excel](../user-guide/export-import.md)，带预览校验和 upsert |
| 文件与图片上传 | **是** `FileField` / `ImageField` | **部分** 需额外配置 | **是** [本地与 S3 存储](../user-guide/file-storage.md) |
| 仪表盘部件 | **部分** 第三方主题 | **部分** 自定义索引视图 | **是** [内置部件系统](../user-guide/custom-views.md) |
| 自定义独立页面 | **是** 自定义 `AdminSite` URL | **是** `BaseView` + `@expose` | **是** [`CustomView`](../user-guide/custom-views.md) |
| 表单布局控制 | **是** `fieldsets` | **是** `form_rules` | **是** [`form_layout`](../advanced/form-layout.md)，支持选项卡和网格 |
| 认证 | **是** `django.contrib.auth` | **否** 自行提供 | **是** [`AuthProvider`](../user-guide/auth.md) 或 `OAuthProvider` |
| 模型级权限 | **是** 权限框架 | **是** 覆盖 `can_*` 标志 | **是** [按请求方法](../user-guide/views.md#security-and-authorization) |
| 字段级权限 | **部分** `get_readonly_fields` | **否** | **是** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| 生命周期钩子 | **是** `save_model`、信号 | **是** `on_model_change` | **是** [生命周期钩子](../user-guide/views.md#lifecycle-hooks)与[事件](../advanced/events.md) |
| CSRF 保护 | **是** Django 中间件 | **是** 通过 Flask-WTF | **是** [内置于 `Admin`](../user-guide/security.md) |
| 变更历史 / 审计日志 | **是** `LogEntry` | **否** | **部分** 可借助[事件](../advanced/events.md)自行实现 |
| 国际化 | **是** | **是** 通过 Flask-Babel | **是** [`I18nConfig`](../user-guide/i18n.md) |
| 多个 admin 实例 | **是** 多个 `AdminSite` | **是** | **是** [多个 `Admin` 挂载](../advanced/multiple-admin.md) |
| 异步 ORM 支持 | **部分** | **否** | **是** 异步 SQLAlchemy、Beanie、Tortoise ORM |

## 取舍

* **完整的用户系统：** Django Admin 自带一套完整的用户系统。`django.contrib.auth` 为你处理用户、分组、权限和密码管理。而在 starlette-admin 中，你需要针对自己的数据存储实现 `authenticate()`，这前期需要更多设置，但后期带来更大的架构自由度。
* **自动化的变更历史：** Django Admin 会将变更历史记录到 `LogEntry`。而在 starlette-admin 中，你需要通过订阅生命周期[事件](../advanced/events.md)来自己构建审计轨迹。只需几行代码，但这并不是自动完成的。
* **第三方生态：** Django Admin 围绕主题、部件和数据工作流拥有庞大的第三方软件包生态。starlette-admin 原生覆盖了其中许多功能，但你依赖的某个小众扩展可能还不存在。
* **文件管理：** Flask-Admin 附带 `FileAdmin`，这是一个服务器文件系统浏览器。starlette-admin 通过[本地磁盘或 S3](../user-guide/file-storage.md) 处理附加到模型字段的文件，但不提供通用的服务器文件浏览器。

## 后续步骤

* 正在从 Django 迁移？请阅读[从 Django Admin 迁移](django-admin.md)。
* 正在从 Flask-Admin 迁移？请阅读[从 Flask-Admin 迁移](flask-admin.md)。
* 全新开始？[快速入门](../getting-started/quickstart.md)能让你在几分钟内得到一个可用的管理界面。
