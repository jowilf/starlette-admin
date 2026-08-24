---
title: 从 Django Admin 迁移
description: 一份全面的迁移指南，将 Django Admin 的各项概念映射到 starlette-admin 中的对应实现，帮助你构建声明式的管理界面。
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# 从 Django Admin 迁移

如果你熟悉 Django Admin，那么 starlette-admin 会让你感到似曾相识。两者都通过声明式的按模型配置生成管理界面，并且都支持内联编辑、批量动作和按请求权限。

差异在于结构层面。starlette-admin 可以运行在任何 ASGI 应用上，而不要求 Django；它支持多种 ORM，并允许你接入自己的认证方案，而不是强制使用内置的用户模型。

本指南将每一个主要的 `ModelAdmin` 概念映射到 starlette-admin 中的对应实现，并提供并排的代码示例。

## 心智模型

| Django Admin 概念 | starlette-admin 对应实现 |
| --- | --- |
| `AdminSite` | 挂载到你的应用上的 [`Admin`](../api/admin.md) 实例 |
| `ModelAdmin` | [`ModelView`](../user-guide/views.md) 子类 |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `urlpatterns` 中的 `admin.site.urls` | `admin.mount_to(app)` |
| Django ORM | 通过 `starlette_admin.contrib.*` 支持的 SQLAlchemy、SQLModel、MongoEngine、Beanie 或 Tortoise ORM |
| 模型上的 `__str__` | `__admin_repr__(self, request)`，异步且可感知请求 |
| 由模型字段推断的表单字段 | 由后端转换器推断的[字段](../user-guide/fields.md)，可按字段自定义 |

## 注册模型

=== "Django Admin"

    ```python
    from django.contrib import admin
    from .models import Post


    @admin.register(Post)
    class PostAdmin(admin.ModelAdmin):
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import Admin, ModelView


    class PostView(ModelView):
        fields = ["id", "title", "content", "published", "created_at"]
        exclude_fields_from_list = ["content"]
        searchable_fields = ["title", "content"]


    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)  # app is your FastAPI or Starlette instance
    ```

两个结构性差异尤为突出：

1. **一份字段列表驱动所有页面。** `fields` 是唯一事实来源。随后使用 [`exclude_fields_from_list`、`exclude_fields_from_detail`、`exclude_fields_from_create` 和 `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization) 实现各页面的差异化。
2. **由 `Admin` 实例持有数据库引擎。** 你不需要向每个视图传入会话。

## 列表页选项

| Django Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `list_display` | `fields` 减去 [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | 一份字段列表驱动所有页面。 |
| 使用可调用对象或 `@admin.display` 的 `list_display` | [`ComputedField`](../user-guide/fields.md#computedfield)，或任意字段上的 `getter=` | 例如，`ComputedField("full_name", getter=lambda request, obj: ...)`。在带类型的字段（如日期或图片字段）上使用 `getter=`，可保留该类型原有的渲染效果。 |
| 重新格式化真实列用于显示 | 字段上的 [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | 一个 `dict[RequestAction, callable]`，因此列表、详情和导出可以有不同的格式化结果。在 Django 中需要可调用对象加上 `admin_order_field` 才能保持排序；而在这里该列始终可排序。 |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | 同时驱动全文搜索和过滤器构建器。 |
| `list_filter` | `searchable_fields` 结合每个字段的 `filters=` | 用户得到的是一个支持嵌套 `AND`/`OR` 分组的可视化构建器，而非固定的侧边栏。参见[过滤器](../user-guide/filters.md)。 |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | 例如，`[("created_at", True)]` 表示按降序排序。 |
| `admin_order_field` / 可排序性 | [`sortable_fields`](../user-guide/views.md#search-and-sort) | 默认情况下所有字段均可排序。 |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | 用户选中单元格后即可就地编辑。 |
| `list_per_page` | [`page_size`、`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | 控制分页上限。 |
| `date_hierarchy` | 日期过滤器，如 `between` 和 `in the past` | 没有专门的层级下钻工具栏；过滤器构建器可以覆盖这一场景。 |
| `empty_value_display` | 一个 `formatter=` 条目，或 `null_template` | 格式化器会收到 `None` 值，因此可以用占位内容替代。`null_template` 则替换渲染出来的标记。 |

## 表单

| Django Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `fields` / `exclude` | `fields`、`exclude_fields_from_create`、`exclude_fields_from_edit` | 控制表单字段的可见性。 |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | 用 `FieldsetWidget`、`TabsWidget`、`GridWidget` 和 `RowWidget` 自由组合。 |
| `readonly_fields` | 字段上的 `read_only=True` | 你也可以将该字段从创建和编辑视图中排除。 |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | 同样的实时 slug 生成行为。 |
| `autocomplete_fields`、`raw_id_fields` | [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) 的默认行为 | 关联部件是开箱即用、支持服务端搜索的 Select2 输入框。 |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | 渲染为可搜索的多选组件。 |
| `formfield_overrides` | `fields` 列表中的显式条目 | 直接替换自动检测的字段：`fields = ["id", TextAreaField("bio")]` |
| 自定义表单校验 | 字段的 `validators=`，或钩子中的 `FormValidationError` | 参见[校验器](../api/validators.md)。 |
| 表单字段的 `to_python()` / 自定义类型转换 | 字段上的 [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) | 按 `RequestAction` 替换字段的默认表单解析或导入解析逻辑。 |
| 模型表单的帮助文本 | `help_text=` | 在任何字段定义上都可用。 |

### 字段集示例

=== "Django Admin"

    ```python
    class PostAdmin(admin.ModelAdmin):
        fieldsets = [
            ("Content", {"fields": ["title", "body"]}),
            ("Publication", {"fields": ["published", "created_at"]}),
        ]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import FieldsetWidget


    class PostView(ModelView):
        fields = ["id", "title", "body", "published", "created_at"]
        form_layout = [
            FieldsetWidget(legend="Content", children=["title", "body"]),
            FieldsetWidget(legend="Publication", children=["published", "created_at"]),
        ]
    ```

`form_layout` 比字段集更进一步：你还可以构建选项卡、响应式网格和嵌套布局。参见[表单布局](../advanced/form-layout.md)。

## 内联

=== "Django Admin"

    ```python
    class CommentInline(admin.TabularInline):
        model = Comment
        extra = 1


    class ArticleAdmin(admin.ModelAdmin):
        inlines = [CommentInline]
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

在外键无歧义时，starlette-admin 会自动检测外键，并且支持复合外键。高级配置参见[内联表单](../user-guide/inline-forms.md)。

## 动作

=== "Django Admin"

    ```python
    @admin.action(description="Mark selected articles as published")
    def make_published(modeladmin, request, queryset):
        queryset.update(published=True)


    class ArticleAdmin(admin.ModelAdmin):
        actions = [make_published]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class ArticleView(ModelView):
        actions = ["make_published", "delete"]

        @action(
            name="make_published",
            text="Mark selected articles as published",
            confirmation="Publish the selected articles?",
        )
        async def make_published(
            self, request: Request, selection: ActionSelection
        ) -> None:
            for article in await selection.rows():
                article.published = True
            flash(request, "Articles published")
    ```

Django Admin 传入的是 `QuerySet`，而 starlette-admin 的处理函数接收的是一个 [`ActionSelection`](../user-guide/actions.md) 对象。该对象会惰性解析行、主键和当前生效的过滤器，并且在用户勾选所有匹配记录时行为完全相同。

动作还可以在确认对话框中渲染自定义 HTML 表单，这在 Django Admin 中意味着需要构建一个中间页面。对于行级操作，请使用 [`@row_action` 和 `@link_row_action`](../user-guide/actions.md#row-actions)，它们在 Django Admin 中没有对应概念。

## 权限与认证

Django Admin 将工作委托给 `django.contrib.auth`。starlette-admin 把问题拆分为两部分：[`AuthProvider`](../user-guide/auth.md) 回答“这个用户是谁”，而[按视图方法](../user-guide/views.md#security-and-authorization)回答“他能做什么”。

| Django Admin | starlette-admin |
| --- | --- |
| `django.contrib.auth` 登录 | `AuthProvider`（内置登录页）或 `OAuthProvider`（OIDC 重定向流程） |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | 视图上的 `is_accessible(request)` |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| 按用户的 `get_readonly_fields` | `can_access_field(request, field)` |
| 无对应概念 | `can_export(request)`、`can_import(request)`、`is_action_allowed(request, name)` |

下面的视图将删除操作限制为具有 `admin` 角色的用户：

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

每个 `can_*` 方法都会接收请求，因此授权决策可以读取当前用户、HTTP 请求头或请求上的任何其他信息。

## 保存钩子与信号

| Django Admin | starlette-admin | 说明 |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | 视图上的 [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) | 原生异步，并同时接收解析后的表单数据和模型实例。 |
| `delete_model` | `before_delete` | 处理删除前的逻辑。 |
| `post_save` 及其他信号 | [事件](../advanced/events.md) | 例如，`admin.events.on(AdminEvent.AFTER_CREATE, handler)` 会向所有视图广播。 |
| `LogEntry` 变更历史 | 用事件系统自行构建 | 订阅 `AFTER_CREATE`、`AFTER_EDIT` 和 `AFTER_DELETE` 来填充你自己的审计表。 |
| `messages.success(request, ...)` | `flash(request, ...)` | 参见[Flash 消息](../user-guide/flash-messages.md)。 |

## 站点级配置

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`、`site_title` | `Admin(title="...")` |
| 通过模板覆盖自定义 logo | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)`，配合[部件](../user-guide/custom-views.md)打造丰富的仪表盘 |
| `templates/admin/` 中的模板覆盖 | `Admin(templates_dir="...")`，参见[模板](../advanced/templates.md) |
| 多个 `AdminSite` 实例 | 挂载在不同应用路径上的多个 `Admin` 实例 |
| `ModelAdmin.get_queryset` | SQLAlchemy 后端的 `get_list_query`、`get_count_query` 或 `get_detail_query` |
| `USE_I18N`、`LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`，参见[i18n 与时区](../user-guide/i18n.md) |

## 切换后你能获得什么

* **端到端异步：** 处理函数、生命周期钩子和部件回调都可以是协程，在与 FastAPI 端点相同的事件循环上运行。
* **数据库灵活性：** 无论你使用 SQLAlchemy、SQLModel、通过 MongoEngine 或 Beanie 访问的 MongoDB，还是 Tortoise ORM，同一套 admin 配置均适用。
* **内置导出与导入：** 支持 CSV、JSON 和 PDF，并通过 `tablib` 支持 Excel 等其他格式。可以直接导出记录，也可以通过预览优先的向导导入批量数据；向导强制执行行级校验，并支持可选的主键 upsert。参见[导出与导入](../user-guide/export-import.md)。
* **仪表盘部件：** 统计卡片、ApexCharts 和布局网格可组合成索引页和自定义视图，无需外部主题软件包即可构建仪表盘。参见[自定义视图与部件](../user-guide/custom-views.md)。
* **现代化用户界面：** Tabler（Bootstrap 5）默认提供深色模式、列可见性切换和搜索高亮。

## 需要你自己提供的部分

* **认证：** 没有捆绑的用户模型或权限数据库。请针对你的应用已有的数据存储实现 `AuthProvider.authenticate()`。
* **审计日志：** starlette-admin 不会生成 `LogEntry` 表。请将[事件系统](../advanced/events.md)接入你自己的审计表。
* **模型级 UI 配置：** Django 的一些便利特性，例如模型级的 `choices`、`verbose_name` 和校验器，无法直接迁移。请在 starlette-admin 的字段上声明这些配置，使用 `EnumField`、`label=` 和 `validators=`。
