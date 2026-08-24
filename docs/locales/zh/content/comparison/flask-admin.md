---
title: 从 Flask-Admin 迁移
description: 一份从 Flask-Admin 到 starlette-admin 的直接迁移指南，展示如何将你的 ModelView 配置过渡到 ASGI
  生态。
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# 从 Flask-Admin 迁移

starlette-admin 最初就是将 Flask-Admin 的理念移植到 ASGI 生态的产物，因此迁移路径非常直接。你仍然继承 `ModelView`，用类属性进行配置，并在 `Admin` 实例上注册。大部分工作只是重命名属性，以及从 Flask 的隐式请求上下文转向 Starlette 的显式 `request` 对象。

本指南将逐一对照属性，把 Flask-Admin API 映射到 starlette-admin 中的对应实现。

## 心智模型

| Flask-Admin 概念 | starlette-admin 对应实现 |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`，然后调用 `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`；`Admin` 实例持有引擎和数据库会话 |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| peewee / pymongo 后端 | Beanie、Tortoise ORM、SQLModel，或[自定义后端](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`、`DefaultIndexView` |
| Flask 请求上下文（`flask.request`） | 每个钩子上显式的 `request: Request` 参数 |
| 同步方法 | `async` 方法；在接受可调用对象之处仍可使用同步 |

## 初始设置

=== "Flask-Admin"

    ```python
    from flask import Flask
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView

    app = Flask(__name__)
    admin = Admin(app, name="My Admin", template_mode="bootstrap4")
    admin.add_view(ModelView(Post, db.session))
    ```

=== "starlette-admin"

    ```python
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView

    app = Starlette()  # or FastAPI()
    admin = Admin(engine, title="My Admin", secret_key="change-me")
    admin.add_view(ModelView(Post))
    admin.mount_to(app)
    ```

这里没有 `template_mode` 开关。UI 使用 [Tabler](https://tabler.io)（Bootstrap 5），并包含深色模式。要改变外观，可以编写自定义的 [`BaseTheme`](../advanced/custom-themes.md) 或[覆盖模板](../advanced/templates.md)。

## 列表页属性

| Flask-Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `column_list` | `fields` | 同时驱动详情页和表单页。使用 `exclude_fields_from_*` 属性可实现各页面的差异化。 |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | 例如，`StringField("title", label="Headline")`。 |
| `column_descriptions` | `help_text=` | 应用于字段定义。 |
| `column_formatters` | 字段上的 [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | 例如，`StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`。 |
| `column_formatters_detail` / 导出格式化器 | 同一个 `formatter=` 字典，以 `RequestAction` 为键 | 一个映射即可覆盖列表、详情和导出的格式化。没有对应条目的动作将保留原始值。 |
| `column_type_formatters` | 每字段的 `formatter=`，或自定义字段子类 | 没有按类型划分的注册表。将格式化器附加到各个字段，或者[继承字段类](../advanced/custom-fields.md)以便复用。 |
| `column_list` 中的模型属性或可调用对象 | [`ComputedField`](../user-guide/fields.md#computedfield)，或任意字段上的 `getter=` | 无需子类即可添加虚拟列，或改变已有字段的取值来源。 |
| 自定义 WTForms 字段（值转换） | 字段上的 [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | 按 `RequestAction` 替换字段的默认表单解析或导入解析逻辑。 |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | `searchable_fields` 结合每字段的 `filters=` | 用一个支持嵌套 `AND`/`OR` 分组的[可视化构建器](../user-guide/filters.md)取代扁平的过滤器列表。 |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | 例如，`[("created_at", True)]` 表示按降序排序。 |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | 用户选中单元格后即可就地编辑。 |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | 默认为 `[10, 25, 50, 100]`。用户从这些选项中选择。 |
| `column_display_pk` | 在 `fields` 中包含主键 |  |
| `column_details_list` | `fields` 减去 `exclude_fields_from_detail` | 详情页是内置的，无需 `can_view_details` 选择性开启。 |

## 表单属性

| Flask-Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `form_columns` | `fields` 减去 `exclude_fields_from_create` 和 `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`、`exclude_fields_from_edit` | 为每个表单提供独立的可见性控制。 |
| `form_overrides` | `fields` 中的显式字段实例 | 例如，`fields = ["id", TextAreaField("bio")]` |
| `form_args` | 字段上的构造参数 | 例如，`StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | 例如，`EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | `fields` 中的额外条目 | 支持任何不基于数据库列的字段，例如 [`ComputedField`](../user-guide/fields.md#computedfield)。 |
| `form_widget_args` | 字段属性 | 直接在字段上设置 `read_only`、`disabled` 或 `placeholder`。 |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | 用字段集、选项卡和响应式网格取代扁平规则。 |
| `create_modal` / `edit_modal` | 不支持 | 创建和编辑视图渲染为完整页面。 |
| `on_form_prefill` | `before_edit` 钩子 |  |

## 导出与导入

=== "Flask-Admin"

    ```python
    class PostView(ModelView):
        can_export = True
        export_types = ["csv", "xlsx"]
        export_max_rows = 10000
    ```

=== "starlette-admin"

    ```python
    class PostView(ModelView):
        exporters = ["csv", "xlsx", "pdf"]
        importers = ["csv", "xlsx"]
        exclude_fields_from_export = ["internal_notes"]
    ```

CSV 和 JSON 导出默认开启。行数上限自动生效，电子表格公式转义则是导出器的可选设置。导入是 Flask-Admin 所不具备的功能：它包含一个预览步骤，可逐行校验，并能通过主键选择性地更新现有记录。参见[导出与导入](../user-guide/export-import.md)。

## 动作

=== "Flask-Admin"

    ```python
    from flask_admin.actions import action


    class PostView(ModelView):
        @action("publish", "Publish", "Publish selected posts?")
        def action_publish(self, ids):
            query = Post.query.filter(Post.id.in_(ids))
            for post in query.all():
                post.published = True
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class PostView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Publish",
            confirmation="Publish selected posts?",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            for post in await selection.rows():
                post.published = True
            flash(request, "Posts published")
    ```

处理函数接收的是 [`ActionSelection`](../user-guide/actions.md) 对象，而不是原始 ID。它会惰性解析行数据，暴露当前生效的过滤器，并且在用户跨页勾选所有匹配记录时同样适用。动作还可以在确认对话框内渲染自定义 HTML 表单。对于行级操作，可以用 [`@row_action` 和 `@link_row_action`](../user-guide/actions.md#row-actions) 取代自定义列格式化器。

## 权限与访问控制

Flask-Admin 的 `can_*` 类标志在 starlette-admin 中变成了[按请求方法](../user-guide/views.md#security-and-authorization)，因此授权决策可以取决于当前登录的用户。

| Flask-Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | 在菜单中隐藏该视图，并阻止直接访问。 |
| `inaccessible_callback()` | 由认证流程处理 | 未认证的请求会重定向到登录页。 |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` 和 `can_delete` 采用相同模式。 |
| `can_view_details` | `can_view_detail(request)` | 详情页默认存在。 |
| `can_export` | `can_export(request)`，外加 `can_import(request)` |  |
| 无对应概念 | `can_access_field(request, field)` | 按用户控制字段级可见性。 |
| 无对应概念 | `is_action_allowed(request, name)` | 提供按动作的授权。 |

使用 Flask-Admin 时，你需要自行集成 Flask-Login。starlette-admin 自带一个配有现成登录页的 [`AuthProvider`](../user-guide/auth.md)，你只需针对自己的用户存储实现 `login`、`logout` 和 `authenticate` 方法。`OAuthProvider` 覆盖 OIDC 重定向流程。当前登录的用户在任何地方都可通过 `request.state.admin_user` 获取。

## 模型生命周期钩子

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`，特定于 SQLAlchemy 后端 |
| `handle_view_exception` | 抛出 `FormValidationError` 或 `ActionFailed` |

除单个视图的钩子之外，[事件系统](../advanced/events.md)还能让单个处理函数观察所有视图。Flask-Admin 没有对应的机制。

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## 自定义视图与索引页

| Flask-Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | 使用[部件](../user-guide/custom-views.md)组合页面，无需手写原始模板。 |
| 自定义模板渲染 | `CustomView` 子类 | 让你完全掌控路由和响应。 |
| `AdminIndexView` | `Admin(index_view=...)` | 用 `StatWidget`、`ChartWidget`、`TableWidget` 和布局部件构建仪表盘。 |
| `MenuLink` | [`Link`](../user-guide/views.md#link) 视图 | 例如，`admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| 菜单中的分类 | [`DropDown`](../user-guide/views.md#sidebar-organization) 视图 | 在侧边栏中将视图分组。 |
| `FileAdmin` | 不支持 | 文件和图片字段配合[本地或 S3 存储](../user-guide/file-storage.md)处理附件。没有服务器文件浏览器。 |

## 内联模型

=== "Flask-Admin"

    ```python
    class ArticleView(ModelView):
        inline_models = [Comment]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import InlineModelView, ModelView


    class CommentInline(InlineModelView):
        model = Comment
        fields = ["author", "body"]


    class ArticleView(ModelView):
        inlines = [CommentInline]
    ```

显式声明的类使每个内联模型都能使用完整的 `ModelView` 配置面：字段选择、校验以及复合外键支持。参见[内联表单](../user-guide/inline-forms.md)。

## 国际化

Flask-Admin 依赖 Flask-Babel 及其周边的 Flask 环境。starlette-admin 则改用配置对象：

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

支持时区的日期时间渲染也以同样的方式通过 `TimezoneConfig` 实现。参见[国际化与时区](../user-guide/i18n.md)。

## 切换后你能获得什么

* **异步技术栈。** 在 FastAPI 和 Starlette 上原生运行，支持异步 SQLAlchemy、Beanie 和 Tortoise ORM。Flask-Admin 是同步的。
* **内置安全特性。** CSRF 保护、上传文件名净化、图片内容校验和导出行数限制在你实例化 `Admin` 时即刻生效，你还可以在导出器上启用电子表格公式转义。参见[安全性](../user-guide/security.md)。
* **数据导入。** 在写入任何数据之前，预览步骤会对每一行进行校验。Flask-Admin 没有导入功能。
* **仪表盘部件系统。** 用 Python 构建索引页和自定义视图，而不是手写模板。
* **现代设计。** 代码库持续积极维护，UI 精致，内置深色模式，并具备一流的类型提示。

## 需要适应的变化

* **显式的请求对象。** 不存在隐式的全局请求上下文。每个钩子和权限方法都将 `request` 作为参数接收。
* **异步处理函数。** 钩子和动作都是协程，因此不要在其中进行阻塞调用，或将此类工作移到线程中执行。
* **没有 `FileAdmin`。** 如果你的工作流依赖于浏览服务器文件系统，starlette-admin 无法满足这一需求。
* **没有创建或编辑模态框。** 表单渲染为完整页面，而不是弹出式模态框。
