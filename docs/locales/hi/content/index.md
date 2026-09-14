---
title: FastAPI और Starlette के लिए विस्तारशील एडमिन इंटरफ़ेस
description: अपने SQLAlchemy, SQLModel, Beanie, MongoEngine, या Tortoise ORM models
  से पूर्ण एडमिन इंटरफ़ेस जनरेट करें।
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
??? info "पर्यवेक्षित मशीन अनुवाद"

    यह सामग्री मानव-निर्मित शब्दावलियों और शैली गाइडों के मार्गदर्शन में
    मशीन जनरेशन द्वारा अनुवादित की गई है। चूँकि इस पाठ की समीक्षा
    लाइन-दर-लाइन मैन्युअल रूप से नहीं की गई है, इसलिए कभी-कभी त्रुटियाँ या
    अनाड़ी वाक्य-रचना हो सकती है।

    किसी भी विसंगति की स्थिति में, मूल अंग्रेज़ी संस्करण ही प्रामाणिक स्रोत
    है।

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/)
<!-- translation-notice:end -->

<div class="home-hero">
  <a class="home-badge" href="changelog/">
    <span class="home-badge-dot"></span>
    नई documentation &nbsp;·&nbsp; देखें क्या बदला
  </a>
  <h1 class="home-title">विस्तारशील <span class="home-gradient">एडमिन इंटरफ़ेस</span><br>FastAPI और Starlette के लिए</h1>
  <p class="home-sub">अपने SQLAlchemy, SQLModel, Beanie, MongoEngine, या Tortoise ORM models से पूर्ण एडमिन इंटरफ़ेस जनरेट करें। <a href="https://tabler.io">Tabler UI kit</a> पर निर्मित starlette-admin आपको list views, auto-generated forms, data exports, और secure authentication देता है। पूरा interface Python में configure करें — frontend code की एक भी line लिखे बिना।</p>
  <div class="home-actions">
    <a class="md-button md-button--primary home-btn" href="getting-started/quickstart/">शुरुआत करें</a>
    <a class="md-button home-btn" href="https://starlette-admin-demo.jowilf.com/">Live demo</a>
    <a class="md-button home-btn home-btn--github" href="https://github.com/jowilf/starlette-admin">
      <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      GitHub पर star दें
    </a>
  </div>
  <div class="home-pip"><code>pip install starlette-admin</code></div>
  <div class="home-shot">
    <img src="assets/images/list-preview.png" alt="starlette-admin dashboard showing statistical widgets, recent activity tables, and a sidebar for model views" loading="lazy">
  </div>
</div>

<h2 class="home-section-title">बिल्ट-इन फ़ीचर्स</h2>
<p class="home-lede">आपकी ज़रूरत की हर चीज box से बाहर काम करती है। हर core feature documented extension points include करता है, ताकि आप उसे अपनी requirements के अनुसार ढाल सकें।</p>

<div class="home-cards">
  <a class="home-card" href="user-guide/views/">
    <span class="home-card-icon hc-sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/><path d="M10 3v18"/></svg></span>
    <h3>Tables</h3>
    <p>Pagination, multi-column ordering, और state-preserving URLs के साथ data browse, search, और sort करें। List view से fields inline edit करें।</p>
  </a>
  <a class="home-card" href="user-guide/filters/">
    <span class="home-card-icon hc-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v2.172a2 2 0 0 1-.586 1.414L15 12v7l-6 2v-8.5L4.52 7.572A2 2 0 0 1 4 6.227z"/></svg></span>
    <h3>Filters</h3>
    <p>UI में nested AND/OR queries बनाएँ — text, numbers, dates, और booleans के लिए type-aware operators के साथ।</p>
  </a>
  <a class="home-card" href="user-guide/fields/">
    <span class="home-card-icon hc-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1"/><path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3z"/><path d="M16 5l3 3"/></svg></span>
    <h3>Forms और uploads</h3>
    <p>25 से अधिक field types और relational data के लिए forms automatically generate करें। File uploads local या S3 storage पर भेजें।</p>
  </a>
  <a class="home-card" href="user-guide/actions/">
    <span class="home-card-icon hc-rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3v7h6l-8 11v-7H5z"/></svg></span>
    <h3>Actions</h3>
    <p>Standard Python decorators से bulk और row-level operations बनाएँ। हर run को confirmation modals और custom payload forms के पीछे gate करें।</p>
  </a>
  <a class="home-card" href="user-guide/export-import/">
    <span class="home-card-icon hc-emerald"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M7 11l5 5 5-5"/><path d="M12 4v12"/></svg></span>
    <h3>Export और import</h3>
    <p>Records को CSV, Excel, JSON, PDF, या tablib द्वारा supported किसी भी format में export करें। Preview-first wizard से bulk import करें जो database में लिखने से पहले हर row validate करता है।</p>
  </a>
  <a class="home-card" href="user-guide/auth/">
    <span class="home-card-icon hc-indigo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3A12 12 0 0 1 12 21 12 12 0 0 1 3.5 6 12 12 0 0 0 12 3"/><circle cx="12" cy="11" r="1"/><path d="M12 12v2.5"/></svg></span>
    <h3>Auth और security</h3>
    <p>वह authentication provider connect करें जो आप पहले से उपयोग करते हैं। Production-ready defaults के साथ deploy करें — CSRF protection और exports/imports की built-in limits सहित।</p>
  </a>
  <a class="home-card" href="user-guide/inline-forms/">
    <span class="home-card-icon hc-cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8"/><path d="M13 9h5"/><path d="M13 15h8"/><path d="M13 19h5"/><rect x="3" y="4" width="6" height="6" rx="1"/><rect x="3" y="14" width="6" height="6" rx="1"/></svg></span>
    <h3>Inline forms</h3>
    <p>Relational data को जगह पर manage करें। Page छोड़े बिना parent model form के भीतर child records edit करें।</p>
  </a>
  <a class="home-card" href="user-guide/custom-views/">
    <span class="home-card-icon hc-orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/></svg></span>
    <h3>Dashboards</h3>
    <p>Built-in statistic, chart, और table widgets से home page बनाएँ, या उसे पूर्ण custom view से replace कर दें।</p>
  </a>
  <a class="home-card" href="user-guide/i18n/">
    <span class="home-card-icon hc-teal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h7"/><path d="M9 3v2c0 4.418-2.239 8-5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4-9 4 9"/><path d="M19.1 18h-6.2"/></svg></span>
    <h3>i18n और timezones</h3>
    <p>Admin को multiple languages में serve करें — locale-aware formatting और precise timezone handling box से बाहर।</p>
  </a>
</div>

<div class="home-code-head">
  <svg class="home-code-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg>
  <h2 class="home-section-title">सब कुछ Python है</h2>
  <p class="home-lede"><strong>rapid development</strong>, <strong>readable syntax</strong>, और <strong>long-term maintainability</strong> के लिए डिज़ाइन किए गए pure Python API से पूर्ण admin interface बनाएँ।</p>
</div>

=== "Mount the admin"

    <span class="home-tour-title" role="heading" aria-level="3">एडमिन पैनल माउंट करें</span>

    कोई model register करें और admin panel को किसी भी FastAPI या Starlette application पर mount करें। फिर `fastapi dev` चलाएँ और `/admin` खोलें।

    <a class="home-tour-btn" href="getting-started/quickstart/">Documentation देखें</a>

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

=== "Views"

    <span class="home-tour-title" role="heading" aria-level="3">व्यूज़</span>

    Search, sorting, default ordering, और export formats plain class attributes से सेट करें। Create/edit forms को `form_layout` से arrange करें।

    <a class="home-tour-btn" href="user-guide/views/">Documentation देखें</a>

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

=== "Fields"

    <span class="home-tour-title" role="heading" aria-level="3">फ़ील्ड्स</span>

    Validation, per-page visibility, और starlette-admin values को कैसे पढ़े/दिखाए — इसे नियंत्रित करने के लिए किसी भी auto-detected field को override करें।

    <a class="home-tour-btn" href="user-guide/fields/">Documentation देखें</a>

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

=== "Filters"

    <span class="home-tour-title" role="heading" aria-level="3">फ़िल्टर</span>

    Built-in query builder को अपने business rules से match करने वाले custom filters से extend करें। आपको जो operations चाहिए, वे underlying database model पर सीधे apply हो सकते हैं।

    <a class="home-tour-btn" href="user-guide/filters/">Documentation देखें</a>

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

=== "Actions"

    <span class="home-tour-title" role="heading" aria-level="3">एक्शन</span>

    Single decorator से business operations attach करें। Confirmation modals, custom forms, और flash messages framework में बने हैं।

    <a class="home-tour-btn" href="user-guide/actions/">Documentation देखें</a>

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

=== "Authentication"

    <span class="home-tour-title" role="heading" aria-level="3">प्रमाणीकरण</span>

    अपने credential check के चारों ओर तीन standard methods implement करें। Login page, sessions, और redirects starlette-admin handle कर लेता है।

    <a class="home-tour-btn" href="user-guide/auth/">Documentation देखें</a>

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

=== "Dashboard"

    <span class="home-tour-title" role="heading" aria-level="3">डैशबोर्ड</span>

    Statistic, chart, और table widgets — जो हर request पर live data query करते हैं — से admin home page compose करें।

    <a class="home-tour-btn" href="user-guide/custom-views/">Documentation देखें</a>

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

<h2 class="home-section-title">प्लगइन और एक्सटेंशन</h2>
<p class="home-lede">हर layer replaceable है। Features को self-contained plugins के रूप में package करें, या dedicated extension point में hook करके framework को अपने domain के अनुसार ढालें।</p>

<div class="home-plugins">
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-violet">Drop-in plugins</span>
    <h3>Zero-boilerplate plugins</h3>
<p>Plugin package इंस्टॉल करें और उसे अपने <code>Admin</code> instance को pass करें। Fields, converters, templates, और assets स्वयं-ही-स्वयं wire up हो जाते हैं।</p>
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
    <a class="home-more" href="advanced/plugins/">Plugins guide पढ़ें</a>
  </div>
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-emerald">Extension points</span>
    <h3>किसी भी component में hook करें</h3>
    <p>Predefined interfaces से आप हर concern को independently swap या extend कर सकते हैं। आवश्यक base class subclass करें और register करें — authentication flow से export formats तक सब customize किया जा सकता है।</p>
    <ul class="home-hooks">
      <li><a href="advanced/custom-fields/"><span>Custom fields</span><code>BaseField</code></a></li>
      <li><a href="advanced/custom-filters/"><span>Custom filters</span><code>BaseFilter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Exporters</span><code>BaseExporter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Importers</span><code>BaseImporter</code></a></li>
      <li><a href="advanced/custom-themes/"><span>Themes</span><code>BaseTheme</code></a></li>
      <li><a href="user-guide/auth/"><span>Auth providers</span><code>BaseAuthProvider</code></a></li>
      <li><a href="user-guide/file-storage/"><span>Storage backends</span><code>BaseStorage</code></a></li>
      <li><a href="user-guide/custom-views/"><span>Dashboard widgets</span><code>BaseWidget</code></a></li>
      <li><a href="advanced/templates/"><span>Templates</span><code>templates_dir</code></a></li>
    </ul>
    <a class="home-more" href="advanced/extension-points/">सभी extension points देखें</a>
  </div>
</div>
