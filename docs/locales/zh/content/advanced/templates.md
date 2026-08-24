---
title: 模板
description: 覆盖 starlette-admin 中的 Jinja2 模板，完全自定义特定视图或字段的 HTML 结构。
source_hash: 92643d00ab546c400a73e995d391d57cd0f5c054cba9d3ca8a5438df8eeb86ae
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/advanced/templates/)
<!-- translation-notice:end -->

# 模板

管理后台中的每个页面都是一个可覆盖的 Jinja2 模板。无需分叉内置模板树，即可修改单个列表页面、某一字段的表格单元格或仪表盘部件。

## 模板加载器的工作原理

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
admin = Admin(engine, title="My Admin", templates_dir="my_templates/")
```

`Admin` 会构建一个 Jinja2 `ChoiceLoader`，先检查你的 `templates_dir`，再检查内置的 `starlette_admin/templates/` 包目录。只要在 `my_templates/` 下按其在 `starlette_admin/templates/` 中的相同相对路径放置文件，你的文件就会遮蔽内置版本。其余所有模板仍从内置目录渲染。

!!! note
    加载器链还会以键 `@starlette-admin` 注册一个 `PrefixLoader`，无论 `templates_dir` 中的文件如何遮蔽内置模板，它都始终解析到内置模板。使用路径格式 `@starlette-admin/<name>.html` 即可访问它们，注意前缀本身不带尾部斜杠。其用途见下文[覆盖单个页面模板](#overriding-a-single-page-template)。

## 模板目录结构一览

| 路径 | 渲染内容 |
| --- | --- |
| `base.html` | 外层 HTML 布局（`<html>`、`<head>`、脚本） |
| `layout.html` | 侧边栏与顶栏界面框架（继承 `base.html`） |
| `index.html` | 仪表盘或首页 |
| `list.html` | 模型列表页（表格、过滤器栏、分页） |
| `detail.html` | 单条记录的详情（只读）视图 |
| `create.html` | 创建表单 |
| `edit.html` | 编辑表单 |
| `login.html` | 登录页面 |
| `error.html` | HTTP 错误页面（403、404 等） |
| `actions.html` | 批量动作模态框 |
| `row-actions.html` | 单行动作下拉菜单 |
| `inline.html` | 创建/编辑页面上的内联表单集 |
| `inline_detail.html` | 详情页面上的内联表格 |
| `inline_row.html` | 内联表单集中的单行 |
| `_filter_bar.html` | 列表上方活动的过滤器标签栏 |
| `_filter_builder.html` | 过滤器构建器模态框 |
| `_pagination.html` | 分页控件 |
| `_column_header.html` | 可排序的列标题单元格 |
| `_form_footer.html` | “保存”、“保存并继续”或“添加另一条”按钮 |
| `_form_group.html` | 创建/编辑表单上单个[表单布局](form-layout.md)分组的字段集 |
| `_form_group_fields.html` | 表单布局分组内渲染的字段输入元素 |
| `fields/list/<type>.html` | 某字段类型的列表列单元格 |
| `fields/detail/<type>.html` | 某字段类型的详情页面显示 |
| `fields/form/<type>.html` | 某字段类型的表单输入部件 |
| `widgets/<name>.html` | 仪表盘部件模板 |
| `modals/actions.html` | 动作确认模态框 |
| `modals/delete.html` | 删除确认模态框 |
| `modals/error.html` | 错误模态框 |
| `modals/import.html` | 导入模态框 |
| `macros/views.html` | 各页面共享的 Jinja2 宏 |

!!! note
    内置模板树还包含 `modals/loading.html`（一个通用的加载状态模态框），以及 `fields/list/`、`fields/detail/` 和 `fields/form/` 中的若干字段专属模板。在覆盖通用 `<type>.html` 文件之前，请查看你所安装版本的 `starlette_admin/templates/` 目录中的确切文件名。

## 覆盖单个页面模板 {#overriding-a-single-page-template}

```
my_templates/
└── list.html   ← shadows the built-in list.html

```

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block content %}
  <div class="alert alert-info">Custom banner above the list.</div>
  {{ super() }}
{% endblock %}

```

`{% extends "list.html" %}` 会重新解析到你自己的 `my_templates/list.html`，因为 `templates_dir` 会被优先检查，这种循环引用会引发无限递归错误。`@starlette-admin/` 前缀始终指向内置副本，因此覆盖中的每个 `extends` 和 `include` 都必须使用该前缀，而不能使用裸文件名。

## 可覆盖的块

每个内置页面都继承自 `layout.html`，而后者又继承自 `base.html`。只需覆盖单个 `{% block %}` 而非整个文件，即可修改某个片段，而不必复制页面的其余部分：

```jinja
{# my_templates/list.html #}
{% extends "@starlette-admin/list.html" %}

{% block list_toolbar_extra %}
  {{ super() }}
  <a class="btn btn-outline-primary" href="/reports/export">Custom report</a>
{% endblock %}

```

### `base.html`

| 块 | 内容 |
| --- | --- |
| `favicon` | 网站图标的 `<link>` 标签 |
| `title` | `<title>` 标签 |
| `head_meta` | `<head>` 元素内的 `<meta>` 标签 |
| `head_css` | 样式表 `<link>` 标签 |
| `head` | `<head>` 元素内的自由插入点 |
| `body` | 整个 `<body>` 内容（会被 `layout.html` 覆盖） |
| `modal` | 页面级的模态框插入点 |
| `script` | 位于闭合 `</body>` 标签紧前的 `<script>` 标签 |
| `tail` | `<body>` 最末尾、`script` 之后的空插入点 |

### `layout.html`

| 块 | 内容 |
| --- | --- |
| `sidebar` | 整个侧边栏 `<aside>` 元素（包括品牌区、菜单和页脚） |
| `brand` | 侧边栏品牌链接内的 Logo 图片（缺失时回退为 `app_title`） |
| `sidebar_menu` | 侧边栏中的视图链接列表 |
| `sidebar_footer` | 侧边栏底部区域 |
| `user_menu_trigger` | 用户菜单按钮上显示的头像和用户名。只定义一次，并通过 `self.user_menu_trigger()` 同时复用于移动端侧边栏和桌面端导航栏，因此覆盖它会同时更新两者 |
| `user_menu_items` | 用户菜单中的下拉项 |
| `navbar` | 顶部导航栏 |
| `navbar_extra` | 放置在导航栏中用户菜单旁的附加内容 |
| `header` | 位于 `content` 上方的页面头部区域（包含标题和面包屑导航） |
| `flash_messages` | 用于渲染Flash 消息（flash messages）的指定区域 |
| `content_before` | 紧邻 `content` 之前的插入点 |
| `content` | 页面主要内容（即由 `list.html`、`detail.html` 等填充的块） |
| `content_after` | 紧随 `content` 之后的插入点 |
| `page_footer` | 页面内容下方的页脚区域 |

### `list.html`

| 块 | 内容 |
| --- | --- |
| `header` | 页面头部（包含标题和面包屑导航） |
| `page_title` | 头部内的 `<h1>` 标题 |
| `breadcrumbs` | 头部内的面包屑导航路径 |
| `modal` | 删除、动作和导入模态框 |
| `content` | 列表页面的完整主体 |
| `list_search` | 搜索输入区域 |
| `list_toolbar` | 包含过滤器、导出、导入和创建按钮的工具栏行 |
| `list_toolbar_extra` | 工具栏最末尾的额外插入点 |
| `list_before_table` | 表格之前的插入点 |
| `list_table` | `<table>` 元素本身 |
| `list_header` | 包含复选框和列标题单元格的 `<thead>` 行 |
| `list_row` | 结果表中的单个 `<tr>`（作用域块；可访问 `row`、`row_pk` 和 `row_clickable`） |
| `list_row_actions_before` | `row_actions_position` 为 `BEFORE_COLUMNS` 时的行动作单元格（作用域块） |
| `list_row_actions_after` | `row_actions_position` 为 `AFTER_COLUMNS` 时的行动作单元格（作用域块） |
| `list_empty` | “无数据”占位内容（为空状态渲染的作用域块） |
| `list_after_table` | 表格之后的插入点 |
| `list_footer` | 分页与范围页脚 |
| `head_css` | 页面特定的样式表补充 |
| `script` | 页面特定的脚本补充 |

### `detail.html`

| 块 | 内容 |
| --- | --- |
| `header` | 页面头部（包含标题、面包屑导航和动作） |
| `page_title` | 头部内的 `<h1>` 标题 |
| `breadcrumbs` | 头部内的面包屑导航路径 |
| `modal` | 删除和动作模态框 |
| `content` | 详情页面的完整主体 |
| `detail_before` | 详情卡片之前的插入点 |
| `detail_title` | 详情卡片内的标题区域 |
| `detail_actions` | 详情卡片内的动作按钮 |
| `details_table` | 主字段与值的表格 |
| `detail_after` | 详情卡片之后的插入点 |
| `head_css` | 页面特定的样式表补充 |
| `script` | 页面特定的脚本补充 |

### `create.html` / `edit.html`

| 块 | 内容 |
| --- | --- |
| `header` | 页面头部（包含标题和面包屑导航） |
| `page_title` | 头部内的 `<h1>` 标题 |
| `breadcrumbs` | 头部内的面包屑导航路径 |
| `content` | 表单页面的完整主体 |
| `form_before` | 表单卡片之前的插入点 |
| `create_card_header` / `edit_card_header` | 表单卡片内的头部区域 |
| `create_form` / `edit_form` | [表单布局](form-layout.md)分组（每组通过 `_form_group.html` 渲染）及其字段输入元素 |
| `create_inlines` / `edit_inlines` | 内联表单集区域 |
| `form_footer` | “保存”、“保存并继续”和“添加另一条”按钮 |
| `form_after` | 表单卡片之后的插入点 |
| `head_css` | 页面特定的样式表补充 |
| `script` | 页面特定的脚本补充 |

### `login.html`

| 块 | 内容 |
| --- | --- |
| `header` / `sidebar` | 留空（登录页面隐藏标准的应用界面框架） |
| `content` | 登录页面的完整主体 |
| `login_logo` | 登录表单上方显示的 Logo |
| `login_title` | 登录页面的标题文本 |
| `login_form_before` | 表单字段之前的插入点 |
| `login_fields` | 用户名和密码输入字段 |
| `login_form_footer` | 字段之后、仍位于表单之内的插入点 |
| `login_card_footer` | 紧邻登录卡片下方的插入点 |
| `script` | 页面特定的脚本补充 |

### `index.html`

| 块 | 内容 |
| --- | --- |
| `head_css` | 部件特定的样式表补充 |
| `content` | 仪表盘部件网格 |
| `script` | 部件特定的脚本补充 |

### `error.html`

| 块 | 内容 |
| --- | --- |
| `header` / `sidebar` | 留空（错误页面隐藏标准的应用界面框架） |
| `content` | 错误消息及相关动作 |
| `error_actions` | 错误消息下方显示的动作按钮（如“返回”按钮） |

!!! tip
    在覆盖中调用 `{{ super() }}` 可以保留内置块的内容并在此基础上追加，而非替换它。上文的 `list_toolbar_extra` 示例正是这样做的，内置的 `index.html` 和 `create.html` 在 `head_css` 块中也采用了相同的模式。

### 示例：用内联 SVG 替换侧边栏 Logo

将 URL 传给 `Admin(logo_url=...)` 是设置 Logo 最快捷的方式，且适用于大多数情况，包括外部 `.svg` 文件。不过，内置模板会将该 URL 渲染在 `<img>` 标签内，因此 SVG 无法从周围的页面继承 CSS 属性。

当你需要让 Logo 响应界面的其余部分时，请使用**内联 `<svg>` 标记**覆盖 `brand` 块。

#### 实现方式

在你的模板目录中创建一个 `layout.html` 文件。管理后台的每个页面都继承自 `layout.html`，因此这一处覆盖即可应用于全站。

```jinja
{# my_templates/layout.html #}
{% extends "@starlette-admin/layout.html" %}

{% block brand %}
  <svg class="navbar-logo" viewBox="0 0 32 32" fill="currentColor">
    <path d="M16 2 L30 9 L30 23 L16 30 L2 23 L2 9 Z" />
  </svg>
{% endblock %}

```

!!! tip "保留 navbar-logo 类"
    请在自定义的 `<svg>` 元素上保留 `navbar-logo` CSS 类。它可以让你的内联图形直接获得框架提供的对齐、内边距和尺寸设置，无需自己编写任何 CSS。

## 覆盖字段模板

每种字段上下文使用三个子目录：

| 目录 | 使用位置 |
| --- | --- |
| `fields/list/<type>.html` | 列表表格单元格（紧凑、只读） |
| `fields/detail/<type>.html` | 详情页面显示（完整、只读） |
| `fields/form/<type>.html` | 创建和编辑表单输入 |

你可以只覆盖文本字段的列表单元格，而不影响表单或详情显示：

```
my_templates/
└── fields/
    └── list/
        └── text.html

```

要让某一个**字段实例**改用你的模板，而不是在所有地方覆盖该类型，可以在字段本身上设置 `list_template`、`detail_template`、`form_template`、`null_template` 或 `empty_template`：

```python
from starlette_admin.fields import StringField

StringField("status", list_template="fields/list/status_badge.html")
```

`null_template`（默认值 `"fields/detail/_null.html"`）和 `empty_template`（默认值 `"fields/detail/_empty.html"`）是两个独立的槽位。只要字段的值为 `None` 或空列表、空元组，列表和详情页面就会用它们替代 `list_template` 或 `detail_template` 进行渲染：

```python
StringField("status", null_template="fields/detail/_status_null.html")
```

## 覆盖部件模板

部件遵循相同的覆盖模式。将你的文件放在 `widgets/` 目录下：

```
my_templates/
└── widgets/
    └── stat_widget.html

```

## 全局模板变量

这些变量无需显式传入即可在每个模板中使用。`Admin` 会在设置阶段一次性将其安装为 Jinja2 全局变量：

| 变量 | 类型 | 描述 |
| --- | --- | --- |
| `views` | `list[BaseView]` | 所有已注册的视图（用于渲染侧边栏） |
| `app_title` | `str` | 管理后台标题（`Admin(title=...)`） |
| `is_auth_enabled` | `bool` | 已配置认证提供方时为 `True` |
| `__name__` | `str` | 管理后台的路由名称前缀（例如 `"admin"`） |
| `static_url` | `callable` | `static_url(request, path, v=None)` → 内置静态资源的 URL。`v` 参数会追加一个用于清除缓存的 `?v=` 查询参数。 |
| `logo_url` | `callable` | `logo_url(request)` → 侧边栏 Logo 的 URL，未设置则为 `None` |
| `login_logo_url` | `callable` | `login_logo_url(request)` → 登录页面 Logo 的 URL，未设置则为 `None` |
| `favicon_url` | `callable` | `favicon_url(request)` → 网站图标的 URL，未设置则为 `None` |
| `list_url` | `callable` | `list_url(request, **overrides)` → 将 `overrides` 合并进查询字符串后的 URL（用于排序、分页或搜索链接）。传入 `None` 即可移除某个键。 |
| `detail_url` | `callable` | `detail_url(request, key, pk)` → 记录详情页面的 URL |
| `edit_url` | `callable` | `edit_url(request, key, pk)` → 记录编辑页面的 URL |
| `export_url` | `callable` | `export_url(request, key, fmt)` → 携带当前列表页过滤器/排序/搜索状态的导出下载 URL |
| `import_url` | `callable` | `import_url(request, key)` → 导入 POST URL |
| `get_locale` | `callable` | `get_locale()` → 当前生效的区域设置字符串（不需要 `request` 参数） |
| `get_locale_display_name` | `callable` | `get_locale_display_name(locale)` → 区域设置字符串的人类可读名称 |
| `i18n_config` | `I18nConfig` | 管理后台的 i18n 配置对象 |
| `get_timezone` | `callable` | `get_timezone()` → 当前生效的时区字符串（不需要 `request` 参数） |
| `get_timezone_display_name` | `callable` | `get_timezone_display_name(timezone, show_offset=False)` → 时区字符串的人类可读名称 |
| `timezone_config` | `TimezoneConfig | None` | 管理后台的时区配置 |
| `theme_settings` | `TablerSettings` | 由 `DefaultTheme` 暴露的当前生效的 Tabler 主题配置（base、primary、radius、mode） |
| `csrf_input` | `callable` | `csrf_input(request)` → 渲染隐藏的 CSRF `<input>` |

!!! note
    `get_locale`、`get_locale_display_name`、`get_timezone` 和 `get_timezone_display_name` 不接受 `request` 参数。它们从 `contextvars` 中读取区域设置和时区——这些变量由 `LocaleMiddleware` 在请求期间填充——而不是从 `Request` 对象读取。

## 页面级上下文变量

除上述全局变量之外，每个页面还会把自己的上下文字典传递给 `TemplateResponse`。

### `list.html`

| 变量 | 类型 | 描述 |
| --- | --- | --- |
| `view` | `BaseModelView` | 当前视图 |
| `title` | `str` | 页面标题 |
| `fields` | `list[BaseField]` | 当前可见的列 |
| `all_fields` | `list[BaseField]` | 所有列表字段（包括隐藏字段） |
| `rows` | `list[dict]` | 序列化后的行数据 |
| `total` | `int` | 用于分页的匹配记录总数 |
| `total_pages` | `int` | 总页数 |
| `range_start` | `int` | 本页第一条记录的序号（从 1 开始） |
| `range_end` | `int` | 本页最后一条记录的序号 |
| `list_params` | `ListParams` | 解析后的 URL 状态（page、page_size、q、sorts、filters） |
| `filter_logic` | `str | None` | 对于活动的顶层过滤器组，取值为 `"and"` 或 `"or"` |
| `filter_chips` | `list` | 活动过滤器标签的描述符 |
| `filter_builder_fields` | `list` | 过滤器构建器界面中可用的字段 |
| `raw_filter` | `str | None` | 来自 URL 的原始 JSON 过滤器字符串 |
| `_actions` | `list` | 可用的批量动作 |
| `row_actions` | `dict[Any, list]` | 每条记录可用的行动作，以主键为键 |

### `detail.html`

| 变量 | 类型 | 描述 |
| --- | --- | --- |
| `view` | `BaseModelView` | 当前视图 |
| `title` | `str` | 页面标题 |
| `obj` | `dict` | 序列化后的记录 |
| `raw_obj` | `Any` | 序列化前的原始模型对象 |
| `inlines` | `list[dict]` | 内联上下文（`[{"inline": InlineModelView, "rows": [...]}]`） |
| `_actions` | `list` | 可用的行动作 |

### `create.html` / `edit.html`

| 变量 | 类型 | 描述 |
| --- | --- | --- |
| `view` | `BaseModelView` | 当前视图 |
| `title` | `str` | 页面标题 |
| `obj` | `dict` | 当前字段值（创建时为默认值，编辑时为现有值） |
| `raw_obj` | `Any` | 原始模型对象（仅编辑时存在，创建时没有） |
| `errors` | `dict[str, list[str]]` | 以字段名为键的校验错误（仅在提交失败后出现） |
| `inlines` | `list[dict]` | 内联表单集上下文 |

## 添加自定义全局变量和过滤器

要向模板添加自己的变量和函数，请子类化 `Admin` 并覆盖 `__init__`。先调用 `super().__init__()`，以确保在你添加内容之前 `self.templates` 已经存在：

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin


class MyAdmin(Admin):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.templates.env.globals["site_name"] = "My App"
        self.templates.env.filters["currency"] = lambda v: f"${v:,.2f}"


engine = create_engine("sqlite:///admin.sqlite")
admin = MyAdmin(engine, title="My Admin")
```

## 内置 Jinja2 过滤器

每个 Admin 实例都会在 `_setup_templates` 期间注册以下过滤器：

| 过滤器 | 签名 | 描述 |
| --- | --- | --- |
| `is_custom_view` | `view | is_custom_view` | 若资源是 `CustomView` 则返回 `True` |
| `is_link` | `view | is_link` | 若资源是 `Link` 则返回 `True` |
| `is_model_view` | `view | is_model_view` | 若资源是 `BaseModelView` 则返回 `True` |
| `is_dropdown` | `view | is_dropdown` | 若资源是 `DropDown` 则返回 `True` |
| `tojson` | `value | tojson` | HTML 安全的 JSON 序列化（替换 Jinja2 默认的 `tojson`） |
| `file_icon` | `mime_type | file_icon` | 返回 MIME 类型对应的完整图标类（例如 `application/pdf` → `fa-solid fa-fw fa-file-pdf`）；要使用自己的图标集，可覆盖 `self.templates.env.filters["file_icon"]` |
| `to_view` | `key | to_view` | 通过键字符串查找已注册的 `BaseModelView`；找不到时会抛出 404 `HTTPException` |
| `is_iter` | `value | is_iter` | 若值为 `list` 或 `tuple` 则返回 `True` |
| `is_str` | `value | is_str` | 若值为 `str` 则返回 `True` |
| `is_dict` | `value | is_dict` | 若值为 `dict` 则返回 `True` |
| `ra` | `value | ra` | 将字符串转换为 `RequestAction` 枚举成员 |
| `safe_url` | `url | safe_url` | 仅当 URL 通过安全检查时才返回该 URL，否则返回 `""` |
| `sanitize_html` | `html | sanitize_html` | 从 HTML 字符串中移除不允许的标签并返回 `Markup` |

---

## 后续步骤

* **[表单布局](form-layout.md)**：将创建和编辑表单拆分为带标题、可选择折叠的分组，并可覆盖 `_form_group.html` 来修改其标记。
* **[自定义主题](custom-themes.md)**：在不改动单个模板的情况下重塑管理后台的样式。
* **[自定义字段](custom-fields.md)**：将字段的 Python 类与其专属的 `list_template` 或 `form_template` 配对使用。
* **[扩展点](extension-points.md)**：模板之外全部可插拔扩展点的完整列表。
