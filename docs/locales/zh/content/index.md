---
title: 适用于 FastAPI 和 Starlette 的可扩展管理界面
description: 根据你的 SQLAlchemy、SQLModel、Beanie、MongoEngine 或 Tortoise ORM 模型生成完整的管理界面。
keywords:
- fastapi admin
- starlette admin
- python admin panel
- crud dashboard
- admin framework
hide:
- navigation
- toc
source_hash: d144ed398cb294767fbc083f9434f9ff94fb01c5c9c76618db5300ead610e8f6
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "受监督的机器翻译"

    本文内容由机器翻译生成，并遵循人工维护的术语表与风格指南。由于译文未经逐行人工审校，可能偶有错误或表达不当之处。

    如有任何出入，请以英文原版为准，英文原版是权威来源。

    [阅读英文原版](https://jowilf.github.io/starlette-admin/)
<!-- translation-notice:end -->

<div class="home-hero">
  <a class="home-badge" href="changelog/">
    <span class="home-badge-dot"></span>
    文档全新上线 &nbsp;·&nbsp; 了解更新内容
  </a>
  <h1 class="home-title">为 FastAPI &amp; Starlette 打造<br>可扩展的<span class="home-gradient">管理界面</span></h1>
  <p class="home-sub">根据你的 SQLAlchemy、SQLModel、Beanie、MongoEngine 或 Tortoise ORM 模型生成完整的管理界面。starlette-admin 基于 <a href="https://tabler.io">Tabler UI 组件库</a>构建，为你提供列表视图、自动生成的表单、数据导出以及安全的身份认证。整个界面都可以用 Python 配置，无需编写任何前端代码。</p>
  <div class="home-actions">
    <a class="md-button md-button--primary home-btn" href="getting-started/quickstart/">快速开始</a>
    <a class="md-button home-btn" href="https://starlette-admin-demo.jowilf.com/">在线演示</a>
    <a class="md-button home-btn home-btn--github" href="https://github.com/jowilf/starlette-admin">
      <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      在 GitHub 上加星
    </a>
  </div>
  <div class="home-pip"><code>pip install starlette-admin</code></div>
  <div class="home-shot">
    <img src="assets/images/list-preview.png" alt="starlette-admin dashboard showing statistical widgets, recent activity tables, and a sidebar for model views" loading="lazy">
  </div>
</div>

<h2 class="home-section-title">内置功能</h2>
<p class="home-lede">你所需的一切开箱即用。每项核心功能都带有完善的扩展点文档，方便你按自己的需求进行定制。</p>

<div class="home-cards">
  <a class="home-card" href="user-guide/views/">
    <span class="home-card-icon hc-sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/><path d="M10 3v18"/></svg></span>
    <h3>表格</h3>
    <p>通过分页、多列排序和可保留状态的 URL 浏览、搜索并排序你的数据。还可以直接在列表视图中行内编辑字段。</p>
  </a>
  <a class="home-card" href="user-guide/filters/">
    <span class="home-card-icon hc-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v2.172a2 2 0 0 1-.586 1.414L15 12v7l-6 2v-8.5L4.52 7.572A2 2 0 0 1 4 6.227z"/></svg></span>
    <h3>过滤器</h3>
    <p>在界面中构建嵌套的 AND/OR 查询，针对文本、数字、日期和布尔值提供感知类型的操作符。</p>
  </a>
  <a class="home-card" href="user-guide/fields/">
    <span class="home-card-icon hc-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1"/><path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3z"/><path d="M16 5l3 3"/></svg></span>
    <h3>表单与上传</h3>
    <p>为 25 种以上的字段类型以及关联数据自动生成表单。文件上传可直接发送到本地存储或 S3 存储。</p>
  </a>
  <a class="home-card" href="user-guide/actions/">
    <span class="home-card-icon hc-rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3v7h6l-8 11v-7H5z"/></svg></span>
    <h3>动作</h3>
    <p>使用标准 Python 装饰器创建批量与行级操作。每次执行都可设置确认弹窗和自定义载荷表单加以保护。</p>
  </a>
  <a class="home-card" href="user-guide/export-import/">
    <span class="home-card-icon hc-emerald"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M7 11l5 5 5-5"/><path d="M12 4v12"/></svg></span>
    <h3>导出与导入</h3>
    <p>将记录导出为 CSV、Excel、JSON、PDF 或 tablib 支持的任何格式。批量导入数据时提供先预览后写入的向导，在写入数据库之前逐行校验。</p>
  </a>
  <a class="home-card" href="user-guide/auth/">
    <span class="home-card-icon hc-indigo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3A12 12 0 0 1 12 21 12 12 0 0 1 3.5 6 12 12 0 0 0 12 3"/><circle cx="12" cy="11" r="1"/><path d="M12 12v2.5"/></svg></span>
    <h3>认证与安全</h3>
    <p>接入你已有的身份认证方案。默认配置即可安全上生产，包括 CSRF 防护以及内置的导出与导入限制。</p>
  </a>
  <a class="home-card" href="user-guide/inline-forms/">
    <span class="home-card-icon hc-cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8"/><path d="M13 9h5"/><path d="M13 15h8"/><path d="M13 19h5"/><rect x="3" y="4" width="6" height="6" rx="1"/><rect x="3" y="14" width="6" height="6" rx="1"/></svg></span>
    <h3>内联表单</h3>
    <p>就地管理关联数据。在父模型表单内直接编辑子记录，无需离开当前页面。</p>
  </a>
  <a class="home-card" href="user-guide/custom-views/">
    <span class="home-card-icon hc-orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/></svg></span>
    <h3>仪表盘</h3>
    <p>使用内置的统计、图表和表格部件搭建首页，也可以将其完全替换为自定义视图。</p>
  </a>
  <a class="home-card" href="user-guide/i18n/">
    <span class="home-card-icon hc-teal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h7"/><path d="M9 3v2c0 4.418-2.239 8-5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4-9 4 9"/><path d="M19.1 18h-6.2"/></svg></span>
    <h3>国际化与时区</h3>
    <p>以多种语言呈现管理界面，开箱即用地提供符合区域设置的格式化和精确的时区处理。</p>
  </a>
</div>

<div class="home-code-head">
  <svg class="home-code-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg>
  <h2 class="home-section-title">一切皆 Python</h2>
  <p class="home-lede">使用纯 Python API 构建完整的管理界面，专为<strong>快速开发</strong>、<strong>语法可读</strong>和<strong>长期可维护</strong>而设计。</p>
</div>

=== "挂载 Admin"

    <span class="home-tour-title" role="heading" aria-level="3">挂载管理后台</span>

    注册一个模型，并把管理后台挂载到任意 FastAPI 或 Starlette 应用上。然后运行 `fastapi dev` 并打开 `/admin`。

    <a class="home-tour-btn" href="getting-started/quickstart/">查看文档</a>

    ```python title="main.py"
    from fastapi import FastAPI
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqla import Admin, ModelView

    from models import Base, Post

    engine = create_engine("sqlite:///blog.db")
    Base.metadata.create_all(engine)

    app = FastAPI()

    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(ModelView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)
    ```

=== "视图"

    <span class="home-tour-title" role="heading" aria-level="3">视图</span>

    使用简单的类属性即可设置搜索、排序、默认排列顺序和导出格式。并通过 `form_layout` 排列新建与编辑表单。

    <a class="home-tour-btn" href="user-guide/views/">查看文档</a>

    ```python title="views.py"
    from starlette_admin.contrib.sqla import ModelView


    class PostView(ModelView):
        fields = ["id", "title", "author", "content", "published", "created_at"]
        searchable_fields = ["title", "content"]
        fields_default_sort = [("created_at", True)]
        exporters = ["csv", "xlsx", "json"]
        form_layout = [
            ("title", "author"),
            "content",
            ("published", "created_at"),
        ]


    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    ```

=== "字段"

    <span class="home-tour-title" role="heading" aria-level="3">字段</span>

    重写任何自动检测的字段，以控制校验、页面级可见性，以及 starlette-admin 读取和展示值的方式。

    <a class="home-tour-btn" href="user-guide/fields/">查看文档</a>

    ```python title="views.py"
    from starlette_admin import DateTimeField, RequestAction, StringField, TextAreaField
    from starlette_admin.contrib.sqla import ModelView


    class PostView(ModelView):
        fields = [
            "id",
            StringField("title", required=True, help_text="Shown on the blog"),
            TextAreaField("content", exclude_from_list=True),
            StringField(
                "author_email",
                getter=lambda request, obj: obj.author.email,
                formatter={RequestAction.LIST: lambda request, value: value or "unset"},
            ),
            DateTimeField("created_at", read_only=True, exclude_from_create=True),
        ]
    ```

=== "过滤器"

    <span class="home-tour-title" role="heading" aria-level="3">过滤器</span>

    使用符合业务规则的自定义过滤器扩展内置查询构建器。你可以把所需的操作直接应用到底层数据库模型上。

    <a class="home-tour-btn" href="user-guide/filters/">查看文档</a>

    ```python title="filters.py"
    from datetime import datetime
    from typing import Any

    from starlette_admin.contrib.sqla import ModelView
    from starlette_admin.filters.base import BaseFilter, FilterApplyContext, FilterDataType


    class ActiveThisMonthFilter(BaseFilter):
        name = "this_month"
        label = "Created this month"
        data_type = FilterDataType.NONE  # No value input. The range comes from now().

        def apply(self, ctx: FilterApplyContext) -> Any:
            now = datetime.utcnow()
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            col = getattr(ctx.view.model, ctx.field_name)
            return col.between(start, now)

    class ProductView(ModelView):
        fields = [
            DateTimeField(
                "created_at",
                filters=[ActiveThisMonthFilter, ...],
            ),
        ]
    ```

=== "动作"

    <span class="home-tour-title" role="heading" aria-level="3">动作</span>

    只需一个装饰器即可附加业务操作。确认弹窗、自定义表单和 Flash 消息都已内置于框架之中。

    <a class="home-tour-btn" href="user-guide/actions/">查看文档</a>

    ```python title="views.py"
    from starlette.requests import Request
    from starlette_admin import ActionSelection, action, flash
    from starlette_admin.contrib.sqla import ModelView


    class ArticleView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Mark as published",
            confirmation="Publish the selected articles?",
            submit_btn_text="Yes, publish",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            articles = await selection.rows()
            for article in articles:
                article.published = True
            flash(request, f"{len(articles)} articles published.", "success")
    ```

=== "认证"

    <span class="home-tour-title" role="heading" aria-level="3">认证</span>

    围绕你自己的凭据校验逻辑实现三个标准方法。登录页、会话和重定向都由 starlette-admin 替你处理。

    <a class="home-tour-btn" href="user-guide/auth/">查看文档</a>

    ```python title="auth.py"
    from starlette.requests import Request
    from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed


    class MyAuthProvider(AuthProvider):
        async def login(self, username, password, remember_me, request: Request) -> None:
            if not await check_credentials(username, password):
                raise LoginFailed("Invalid username or password")
            request.session["username"] = username

        async def authenticate(self, request: Request) -> AdminUser | None:
            if username := request.session.get("username"):
                return AdminUser(username=username)
            return None

        async def logout(self, request: Request) -> None:
            request.session.clear()


    admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)
    ```

=== "仪表盘"

    <span class="home-tour-title" role="heading" aria-level="3">仪表盘</span>

    使用统计、图表和表格部件组合出管理首页，它们会在每次请求时查询实时数据。

    <a class="home-tour-btn" href="user-guide/custom-views/">查看文档</a>

    ```python title="dashboard.py"
    from starlette_admin import CardRowWidget, ChartWidget, CustomView, StatWidget

    dashboard = CardRowWidget(
        children=[
            StatWidget(title="Orders", value_callback=count_orders, countup=True),
            StatWidget(title="Revenue", value_callback=sum_revenue, color="success"),
            ChartWidget(title="Sales", chart_type="area", series_callback=sales_series),
        ]
    )

    admin = Admin(
        engine,
        title="Shop Admin",
        secret_key="change-me",
        index_view=CustomView(menu_label="Dashboard", icon="fa fa-home", widget=dashboard),
    )
    ```

<h2 class="home-section-title">插件与扩展</h2>
<p class="home-lede">每一层都可以替换。将功能打包为独立自足的插件，或挂接到专门的扩展点，让框架贴合你的业务领域。</p>

<div class="home-plugins">
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-violet">即插即用插件</span>
    <h3>零样板代码的插件</h3>
<p>安装插件包并将其传入你的 <code>Admin</code> 实例即可。字段、转换器、模板和静态资源会自动完成装配。</p>
    <div class="home-snippet">

    ```python
    from starlette_admin_geospatial import GeospatialPlugin
    from starlette_admin.contrib.sqla import Admin

    admin = Admin(
        engine,
        plugins=[GeospatialPlugin(default_zoom=13)],
    )
    ```

    </div>
    <a class="home-more" href="advanced/plugins/">阅读插件指南</a>
  </div>
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-emerald">扩展点</span>
    <h3>挂接到任意组件</h3>
    <p>预定义的接口让你可以独立地替换或扩展每个关注点。子类化所需的基类并注册即可。从认证流程到导出格式，一切皆可定制。</p>
    <ul class="home-hooks">
      <li><a href="advanced/custom-fields/"><span>自定义字段</span><code>BaseField</code></a></li>
      <li><a href="advanced/custom-filters/"><span>自定义过滤器</span><code>BaseFilter</code></a></li>
      <li><a href="user-guide/export-import/"><span>导出器</span><code>BaseExporter</code></a></li>
      <li><a href="user-guide/export-import/"><span>导入器</span><code>BaseImporter</code></a></li>
      <li><a href="advanced/custom-themes/"><span>主题</span><code>BaseTheme</code></a></li>
      <li><a href="user-guide/auth/"><span>认证提供方</span><code>BaseAuthProvider</code></a></li>
      <li><a href="user-guide/file-storage/"><span>存储后端</span><code>BaseStorage</code></a></li>
      <li><a href="user-guide/custom-views/"><span>仪表盘部件</span><code>BaseWidget</code></a></li>
      <li><a href="advanced/templates/"><span>模板</span><code>templates_dir</code></a></li>
    </ul>
    <a class="home-more" href="advanced/extension-points/">浏览全部扩展点</a>
  </div>
</div>
