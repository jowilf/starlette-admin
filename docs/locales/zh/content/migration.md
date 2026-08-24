---
title: 迁移指南
description: 从旧版本的 starlette-admin 迁移到最新发布的升级指南，包括破坏性变更和新功能。
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# 迁移指南

本页面汇总了 `starlette-admin` 各个版本之间的升级说明。请直接跳转到与你要升级的起始版本相对应的部分。

---

## 从 0.17.x 升级到 1.0.0

此版本重构了 `starlette-admin` 的内部实现，并引入了大量新功能。虽然高层 API 基本保持不变，但最重要的更新是列表页面渲染方式的重写。我们已弃用 DataTables，改用服务端渲染的表格。其余大部分更新只是重命名或微小的签名变更。

本指南按你最有可能遇到这些问题的顺序涵盖了每一项破坏性变更。每个部分都将旧 API 与其替代方案进行对比。如果你的实现只依赖基础功能或少量自定义（例如一个 `Admin` 实例、几个 `ModelView` 子类、`fields` 和 `searchable_fields`），那么你的迁移工作很可能仅限于[环境要求](#requirements)和 [Admin 构造函数](#the-admin-constructor)这两个部分，再加上少量重命名。

对旧列表页面的自定义需要格外关注。DataTables 选项和 JavaScript 渲染函数没有直接的对应物，必须移植到服务端模板（参见 [DataTables 的移除](#datatables-removal)）。

!!! tip
    一次性完成依赖升级并启动你的应用程序。大多数被移除或重命名的属性会在启动时抛出明确的错误，而不是在运行时静默失败。

### 新增内容

除下文列出的破坏性变更之外，此版本还包括：

* **原生列表表格：**已移除 DataTables，改用内置的服务端渲染实现。表格状态现在完全由 URL 驱动，这意味着所有分页、过滤和排序配置均可立即共享并加入书签。
* **[过滤器](user-guide/filters.md)：**嵌套的 `AND`/`OR` 过滤器构建器取代了 DataTables SearchBuilder。过滤器基于字段类型派生，并且可以用纯 Python 完全扩展。你无需编写任何 JavaScript 即可创建过滤器类。
* **[导入与服务端导出](user-guide/export-import.md)：**支持从 CSV、JSON、Excel 等格式导入数据并提供逐行错误报告，同时提供服务端导出器（CSV、JSON、Excel、PDF 等）以取代客户端 DataTables 按钮。
* **[事件](advanced/events.md)：**订阅 `before_create`、`after_edit_committed`、`after_login` 等生命周期钩子以及各种动作事件。
* **[主题](advanced/custom-themes.md)与[插件](advanced/plugins.md)：**打包并复用自定义外观与行为。Cookiecutter 模板可帮助你快速上手。
* **[部件与仪表盘](user-guide/custom-views.md)：**使用 `StatWidget`、`ChartWidget`、`TableWidget` 等构建索引页面与自定义视图。
* **[表单布局](advanced/form-layout.md)：**使用行、列、字段集和选项卡对创建/编辑表单进行逻辑组织。
* **[行内编辑](user-guide/inline-edit.md)：**直接在列表页面上编辑单个字段。
* **[行内表单](user-guide/inline-forms.md)：**使用 `InlineModelView` 在父表单内编辑关联模型。
* **其他增强：**[Flash 消息](user-guide/flash-messages.md)、[OAuth 登录](user-guide/auth.md)、[Tortoise ORM 后端](integrations/tortoise.md)、新字段（`ComputedField`、`SlugField`、`UUIDField`、`IPAddressField`）、字段级 `validators`，以及任意字段的剪贴板复制功能。
* **[日志记录](user-guide/admin.md#debugging)：**该包现在在 `starlette_admin` 命名空间下进行内部日志记录，默认静默。传入 `Admin(debug=True)` 或调用 `starlette_admin.logging.configure_logging()` 即可在控制台中查看请求路由、中间件和权限决策，这在迁移过程中尤为实用。
* **更广的测试覆盖：**测试套件规模显著扩大，新增了 Playwright 端到端测试，用于验证管理界面中的关键工作流程。
* **更轻量的包**：PyPI 上发布的包体积已减少约 50%

### 环境要求 {#requirements}

* **Python 支持：**需要 Python 3.11 或更高版本。已停止支持 Python 3.9 和 3.10。
* **核心依赖：**`itsdangerous` 现在是核心依赖项，用于对管理后台 cookie 进行签名（CSRF 令牌和Flash 消息）。
* **新增可选附加依赖：**

    | 附加依赖 | 启用的功能 |
    | --- | --- |
    | `starlette-admin[email]` | 通过 `email-validator` 实现 `EmailField` 服务端校验 |
    | `starlette-admin[pdf]` | 通过 `reportlab` 实现 PDF 导出 |
    | `starlette-admin[s3]` | 通过 `aiobotocore` 实现 S3 文件存储 |
    | `starlette-admin[tinymce]` | 通过 `nh3` 实现 `TinyMCEEditorField` HTML 消毒 |
    | `starlette-admin[i18n]` | 通过 `babel` 实现翻译（无变化） |

* **Beanie 后端：**需要 Beanie 2.0+。
* **Odmantic 后端：**已移除。如果你依赖它，请继续使用 `starlette-admin<=0.17.1`，并通过[提交 issue](https://github.com/jowilf/starlette-admin/issues) 表达你的需求；如果有足够多的需求，可能会重新提供支持。

### Admin 构造函数 {#the-admin-constructor}

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` 已重命名为 `static_dir`。
* **设置 `secret_key`。**此密钥用于对 CSRF 与Flash 消息 cookie 进行签名。若省略该参数，应用启动时会生成随机密钥（这在开发环境中没有问题）。但这样一来，签名值将在每次重启时以及在多个 worker 之间失效。生产环境中请务必传入稳定的密钥。
* `logo_url`、`login_logo_url` 和 `favicon_url` 现在接受可调用对象 `(request) -> str | None`。这取代了之前由 `AdminConfig` 提供的按请求定制品牌信息的功能。
* **新增可选参数：**`theme`、`plugins`、`additional_loaders`、`import_config` 和 `export_config`。
* **SQLAlchemy 特有说明：**第一个参数现在是 `session_provider`。它接受 `Engine` 或 `AsyncEngine`，现在也接受 `sessionmaker` 或 `async_sessionmaker`。现有的 `Admin(engine)` 调用将继续正常工作。
* `timezone_config` 的默认值现在是 `TimezoneConfig()` 而不是 `None`。日期时间默认以查看者的本地时区显示。传入 `timezone_config=None` 可保留原始值。

### 重命名的视图标识符

视图的命名规范现已统一。请相应地更新你的 `ModelView` 构造函数和类属性：

| 之前 | 之后 |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Before
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# After
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

请注意，`Link` 和 `DropDown` 同样使用 `menu_label` 而非 `label`。

### DataTables 的移除 {#datatables-removal}

列表页面不再使用 DataTables。之前用于配置它的属性已被彻底移除：

| 已移除 | 替代方案 |
| --- | --- |
| `datatables_options` | 无。表格由服务端渲染。请通过模板自定义。 |
| `search_builder` | 新的[过滤器构建器](user-guide/filters.md)，由 `searchable_fields` 启用。 |
| `responsive_table` | 无。表格原生处理溢出。 |
| `save_state` | 始终启用。列表状态（页码、排序、过滤器、搜索、可见列）现在保存在 URL 中。 |
| `BaseField.search_builder_type` | `BaseField.filters`（过滤器类的列表）。 |
| `BaseField.render_function_key` | `BaseField.list_template`（服务端 Jinja 模板）。 |

如果你之前编写过自定义 JavaScript 渲染函数或 DataTables 插件，请将它们移植为 `list_template` 覆盖。现在，每个字段的列表单元格都直接从 `templates/fields/list/*.html` 渲染。

### 动作

批量动作处理程序现在接收 `ActionSelection` 对象，而不是主键列表。这支持了新的“全选匹配项”横幅，可作用于匹配当前过滤器的所有行，而无需在客户端将它们实例化。

```python
# Before
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# After
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* `selection.rows()`、`selection.pks()` 和 `selection.count()` 等方法会延迟解析目标行。无论是用户逐个勾选行，还是选择了所有匹配行，这一机制都适用。
* `selection.is_select_all`、`selection.filters` 和 `selection.q` 等属性允许你将操作下沉为单个批量查询。
* 返回成功消息字符串的做法已被[Flash 消息](user-guide/flash-messages.md)取代。
* 行动作处理程序保留原有的 `(request, pk)` 签名。
* **新增 `@action` 选项：**`header`、`allow_empty_selection`、`dedicated_button`、`modal_size`，以及针对每个请求的 `form` 可调用对象。

### 身份验证 {#authentication}

`starlette_admin/auth.py` 模块现在是 `starlette_admin.auth` 包。现有从 `starlette_admin.auth` 导入的代码仍可正常工作，但提供程序契约已发生变化。

```python
# Before
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request, response):
        request.session.update({"username": username})
        return response

    async def logout(self, request, response):
        request.session.clear()
        return response

    async def is_authenticated(self, request) -> bool:
        request.state.user = my_users_db.get(request.session.get("username"))
        return request.state.user is not None

    def get_admin_user(self, request) -> AdminUser:
        return AdminUser(username=request.state.user["name"])

    def get_admin_config(self, request) -> AdminConfig:
        return AdminConfig(app_title="My Admin")


# After
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request):
        if username in my_users_db:
            request.session.update({"username": username})
            return None  # default redirect (`next` param or admin index)
        raise LoginFailed("Invalid username or password")

    async def logout(self, request):
        request.session.clear()

    async def authenticate(self, request) -> AdminUser | None:
        user = my_users_db.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None
```

* `is_authenticated`、`get_admin_user` 和 `get_admin_config` 三个方法已合并为单一方法 `authenticate(request) -> AdminUser | None`。返回 `None` 表示未通过身份验证。
* `login` 和 `logout` 方法不再接收或返回预先构造好的 `response`。返回 `None` 表示执行默认重定向，也可以返回自定义的 `Response` 来覆盖该行为。
* `AdminConfig` 已被移除。请在 `Admin` 实例上使用 `logo_url` 和 `login_logo_url` 的可调用形式来处理按请求设置的标题和徽标。
* 内置的 [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) 可开箱即用地处理 OAuth2/OIDC 登录流程。
* `login_not_required` 装饰器保持不变。

### 导出与导入

导出已从客户端的 DataTables 按钮迁移到服务端流式端点。导入功能是全新的，且 `ExportType` 已不复存在。

```python
# Before
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# After
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` 已更名为 `exporters`。它接受格式名称或 `BaseExporter` 实例的列表。支持的内置格式包括 `csv`、`json`、`tsv`、`xlsx`、`ods`、`html`、`yaml` 和 `pdf`。除 `csv` 和 `json` 以外的格式需要 `tablib`，PDF 则需要 `pdf` 附加依赖。
* `importers` 接受格式名称或 `BaseImporter` 实例的列表。支持的内置格式包括 `csv`、`tsv`、`json`、`yaml`、`xlsx`、`xls`、`ods`、`dbf` 和 `html`。除 `csv`、`tsv` 和 `json` 以外的格式需要 `tablib`。
* `export_fields`（包含列表）已被 `exclude_fields_from_export`（排除列表）取代。这与其他 `exclude_fields_from_*` 属性的命名约定保持一致。
* 字段也可以单独设置 `exclude_from_export` 和 `exclude_from_import`。
* 请在 `Admin` 实例上使用 `ExportConfig` 和 `ImportConfig` 配置全局限制。详情请参阅[导出与导入](user-guide/export-import.md)文档。

### 自定义字段与模板覆盖

字段模板现已重新组织。如果你覆盖了内置模板或发布了自定义字段，请更新你的路径：

| 之前 | 之后 |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| （客户端渲染函数） | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template`（路径） | 属性名不变，路径前缀改为 `fields/form/` |

```python
# Before
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# After
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

值得探索的新字段级功能包括 `validators`、`filters`、`default`、钩子（`getter`、`formatter`、`parser`）、`copy_to_clipboard`，以及用于存放任意元数据的 `extra` 字典。更多信息请查阅[自定义字段](advanced/custom-fields.md)文档。

### CustomView

`CustomView` 类不再接受 `template_path` 和 `methods`。请使用[部件](user-guide/custom-views.md)构建简单的页面。对于需要完全控制的页面，请继承 `CustomView` 并直接声明路由。

```python
# Before
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# After: widget-based page
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# After: full control
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

`@route` 装饰器还允许任何视图暴露额外的端点，以满足 JSON 图表数据或 webhook 等需求。

### 自定义后端

如果你针对自定义数据源实现了 `BaseModelView`，请注意以下更新后的数据访问契约：

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# After
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* 字符串类型的 `where` 参数被拆分为 `q`（用于全文搜索词）和 `filters`（由过滤器构建器提供的类型化 `FilterGroup` 树）。
* `order_by` 参数（之前是 `"field direction"` 格式的字符串列表）现在是 `sorts`，接受 `(field_name, direction)` 元组的列表。
* 每个后端现在都附带一个过滤器注册表，用于将字段类型映射到过滤器实现。完整的契约和工作示例请查阅[自定义后端](integrations/custom-backend.md)文档。

### 需要注意的行为变更

* **时区：**日期时间默认以查看者的本地时区渲染（参见 Admin 构造函数部分关于 `timezone_config` 的说明）。
* **URL 状态：**列表状态现在保存在 URL 中。由于已保存的 DataTables 状态不会被迁移，来自旧版本的收藏管理后台 URL 将显示默认的列表状态。
* **邮箱校验：**安装 `email-validator` 后，`EmailField` 现在会在服务端进行校验。
* **CSRF 防护：**CSRF 防护已内置且基于 cookie。如果你之前使用自定义 CSRF 中间件包装过管理后台，可以放心将其移除。请确保设置了 `secret_key`，以便令牌在服务器重启后仍然有效。
* **FileField 上传大小：**`FileField.max_size` 现在默认为 50 MB，而不是无限制。传入 `max_size=None` 可恢复旧的无限制行为，或者设置显式值来更改上限。

### 已移除且无替代的功能

* `AdminConfig`（参见[身份验证](#authentication)）。
* `datatables_options`、`responsive_table` 和 `save_state`（参见 [DataTables 的移除](#datatables-removal)）。
* Odmantic 后端（参见[环境要求](#requirements)）。

## 获取帮助

如果你遇到本指南未涵盖的迁移问题，请[提交 issue](https://github.com/jowilf/starlette-admin/issues)。请附上问题的最小复现示例，并注明你所升级来源的版本。使用 [`Admin(debug=True)`](user-guide/admin.md#debugging) 运行通常能直接揭示原因，产生的日志也是问题报告的重要补充。
