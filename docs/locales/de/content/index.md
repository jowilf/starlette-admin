---
title: Erweiterbare Admin-Interfaces für FastAPI & Starlette
description: Generieren Sie ein komplettes Admin-Interface aus Ihren SQLAlchemy-,
  SQLModel-, Beanie-, MongoEngine- oder Tortoise-ORM-Modellen.
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
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/)
<!-- translation-notice:end -->

<div class="home-hero">
  <a class="home-badge" href="changelog/">
    <span class="home-badge-dot"></span>
    Neue Dokumentation &nbsp;·&nbsp; Sehen Sie, was sich geändert hat
  </a>
  <h1 class="home-title">Erweiterbare <span class="home-gradient">Admin-Interfaces</span><br>für FastAPI &amp; Starlette</h1>
  <p class="home-sub">Generieren Sie ein komplettes Admin-Interface aus Ihren SQLAlchemy-, SQLModel-, Beanie-, MongoEngine- oder Tortoise-ORM-Modellen. Auf dem <a href="https://tabler.io">Tabler UI Kit</a> aufbauend bietet Ihnen starlette-admin Listenviews, automatisch generierte Formulare, Datenexporte und eine sichere Authentifizierung. Konfigurieren Sie das gesamte Interface in Python, ohne Frontend-Code zu schreiben.</p>
  <div class="home-actions">
    <a class="md-button md-button--primary home-btn" href="getting-started/quickstart/">Loslegen</a>
    <a class="md-button home-btn" href="https://starlette-admin-demo.jowilf.com/">Live-Demo</a>
    <a class="md-button home-btn home-btn--github" href="https://github.com/jowilf/starlette-admin">
      <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      Auf GitHub einen Stern vergeben
    </a>
  </div>
  <div class="home-pip"><code>pip install starlette-admin</code></div>
  <div class="home-shot">
    <img src="assets/images/list-preview.png" alt="starlette-admin-Dashboard mit statistischen Widgets, Tabellen mit aktuellen Aktivitäten und einer Seitenleiste für Modellviews" loading="lazy">
  </div>
</div>

<h2 class="home-section-title">Integrierte Features</h2>
<p class="home-lede">Alles, was Sie brauchen, funktioniert sofort nach dem Installieren. Jedes Kernfeature enthält dokumentierte Erweiterungspunkte, damit Sie es an Ihre Anforderungen anpassen können.</p>

<div class="home-cards">
  <a class="home-card" href="user-guide/views/">
    <span class="home-card-icon hc-sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/><path d="M10 3v18"/></svg></span>
    <h3>Tabellen</h3>
    <p>Durchsuchen und sortieren Sie Ihre Daten mit Paginierung, Sortierung über mehrere Spalten und zustandserhaltenden URLs. Bearbeiten Sie Felder direkt inline von der Listenseite aus.</p>
  </a>
  <a class="home-card" href="user-guide/filters/">
    <span class="home-card-icon hc-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v2.172a2 2 0 0 1-.586 1.414L15 12v7l-6 2v-8.5L4.52 7.572A2 2 0 0 1 4 6.227z"/></svg></span>
    <h3>Filter</h3>
    <p>Erstellen Sie verschachtelte AND/OR-Queries im UI, mit typbewussten Operatoren für Text, Zahlen, Datumsangaben und Booleans.</p>
  </a>
  <a class="home-card" href="user-guide/fields/">
    <span class="home-card-icon hc-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1"/><path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3z"/><path d="M16 5l3 3"/></svg></span>
    <h3>Formulare &amp; Uploads</h3>
    <p>Generieren Sie Formulare automatisch für mehr als 25 Feldtypen und für relationale Daten. Senden Sie Datei-Uploads an lokale oder S3-Speicher.</p>
  </a>
  <a class="home-card" href="user-guide/actions/">
    <span class="home-card-icon hc-rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3v7h6l-8 11v-7H5z"/></svg></span>
    <h3>Aktionen</h3>
    <p>Erstellen Sie Massenaktionen und Aktionen auf Zeilenebene mit gewöhnlichen Python-Decorators. Schützen Sie jede Ausführung mit einem Bestätigungsmodal und einem benutzerdefinierten Payload-Formular.</p>
  </a>
  <a class="home-card" href="user-guide/export-import/">
    <span class="home-card-icon hc-emerald"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M7 11l5 5 5-5"/><path d="M12 4v12"/></svg></span>
    <h3>Export &amp; Import</h3>
    <p>Exportieren Sie Einträge als CSV, Excel, JSON, PDF oder in ein beliebiges Format, das tablib unterstützt. Importieren Sie Daten massenhaft mit einem Assistenten, der zuerst eine Vorschau zeigt und jede Zeile validiert, bevor sie in die Datenbank geschrieben wird.</p>
  </a>
  <a class="home-card" href="user-guide/auth/">
    <span class="home-card-icon hc-indigo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3A12 12 0 0 1 12 21 12 12 0 0 1 3.5 6 12 12 0 0 0 12 3"/><circle cx="12" cy="11" r="1"/><path d="M12 12v2.5"/></svg></span>
    <h3>Auth &amp; Sicherheit</h3>
    <p>Verbinden Sie den Authentifizierungsanbieter, den Sie bereits verwenden. Deployen Sie mit produktionsbereiten Defaultwerten, einschließlich CSRF-Schutz und integrierten Limits für Exporte und Importe.</p>
  </a>
  <a class="home-card" href="user-guide/inline-forms/">
    <span class="home-card-icon hc-cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8"/><path d="M13 9h5"/><path d="M13 15h8"/><path d="M13 19h5"/><rect x="3" y="4" width="6" height="6" rx="1"/><rect x="3" y="14" width="6" height="6" rx="1"/></svg></span>
    <h3>Inline-Formulare</h3>
    <p>Verwalten Sie relationale Daten direkt am Ort. Bearbeiten Sie untergeordnete Einträge innerhalb des Formulars des übergeordneten Modells, ohne die Seite zu verlassen.</p>
  </a>
  <a class="home-card" href="user-guide/custom-views/">
    <span class="home-card-icon hc-orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/></svg></span>
    <h3>Dashboards</h3>
    <p>Bauen Sie eine Startseite aus integrierten Statistik-, Diagramm- und Tabellen-Widgets oder ersetzen Sie sie durch eine vollständig benutzerdefinierte View.</p>
  </a>
  <a class="home-card" href="user-guide/i18n/">
    <span class="home-card-icon hc-teal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h7"/><path d="M9 3v2c0 4.418-2.239 8-5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4-9 4 9"/><path d="M19.1 18h-6.2"/></svg></span>
    <h3>i18n &amp; Zeitzonen</h3>
    <p>Stellen Sie das Admin-Panel in mehreren Sprachen bereit, mit gebietsschemabewusster Formatierung und präziser Handhabung von Zeitzonen ganz ohne zusätzliche Konfiguration.</p>
  </a>
</div>

<div class="home-code-head">
  <svg class="home-code-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg>
  <h2 class="home-section-title">Alles ist Python</h2>
  <p class="home-lede">Bauen Sie ein komplettes Admin-Interface mit einer reinen Python-API, die für <strong>schnelle Entwicklung</strong>, <strong>lesbare Syntax</strong> und <strong>langfristige Wartbarkeit</strong> ausgelegt ist.</p>
</div>

=== "Das Admin-Panel einbinden"

    <span class="home-tour-title" role="heading" aria-level="3">Das Admin-Panel einbinden</span>

    Registrieren Sie ein Modell und binden Sie das Admin-Panel in eine beliebige FastAPI- oder Starlette-Anwendung ein. Führen Sie dann `fastapi dev` aus und öffnen Sie `/admin`.

    <a class="home-tour-btn" href="getting-started/quickstart/">Dokumentation ansehen</a>

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

    <span class="home-tour-title" role="heading" aria-level="3">Views</span>

    Legen Sie Suche, Sortierung, Standardsortierung und Exportformate mit einfachen Klassenattributen fest. Ordnen Sie Ihre Create- und Edit-Formulare mit `form_layout` an.

    <a class="home-tour-btn" href="user-guide/views/">Dokumentation ansehen</a>

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

=== "Felder"

    <span class="home-tour-title" role="heading" aria-level="3">Felder</span>

    Überschreiben Sie jedes automatisch erkannte Feld, um Validierung, Sichtbarkeit pro Seite und die Art zu steuern, wie starlette-admin Werte liest und anzeigt.

    <a class="home-tour-btn" href="user-guide/fields/">Dokumentation ansehen</a>

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

=== "Filter"

    <span class="home-tour-title" role="heading" aria-level="3">Filter</span>

    Erweitern Sie den integrierten Query-Builder mit benutzerdefinierten Filtern, die zu Ihren Geschäftsregeln passen. Sie können die benötigten Operationen direkt auf das zugrunde liegende Datenbankmodell anwenden.

    <a class="home-tour-btn" href="user-guide/filters/">Dokumentation ansehen</a>

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

=== "Aktionen"

    <span class="home-tour-title" role="heading" aria-level="3">Aktionen</span>

    Hängen Sie Geschäftsoperationen mit einem einzigen Decorator an. Bestätigungsmodals, benutzerdefinierte Formulare und Flash-Nachrichten sind bereits im Framework enthalten.

    <a class="home-tour-btn" href="user-guide/actions/">Dokumentation ansehen</a>

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

=== "Authentifizierung"

    <span class="home-tour-title" role="heading" aria-level="3">Authentifizierung</span>

    Implementieren Sie drei Standardmethoden rund um Ihre eigene Prüfung der Zugangsdaten. starlette-admin kümmert sich für Sie um die Login-Seite, die Sessions und die Weiterleitungen.

    <a class="home-tour-btn" href="user-guide/auth/">Dokumentation ansehen</a>

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

    <span class="home-tour-title" role="heading" aria-level="3">Dashboard</span>

    Setzen Sie die Startseite des Admin-Panels aus Statistik-, Diagramm- und Tabellen-Widgets zusammen, die bei jedem Request Live-Daten abfragen.

    <a class="home-tour-btn" href="user-guide/custom-views/">Dokumentation ansehen</a>

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

<h2 class="home-section-title">Plugins &amp; Erweiterungen</h2>
<p class="home-lede">Jede Ebene ist austauschbar. Packen Sie Features als eigenständige Plugins oder hängen Sie sich in einen dedizierten Erweiterungspunkt ein, um das Framework auf Ihre Domain zuzuschneiden.</p>

<div class="home-plugins">
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-violet">Plug-and-Play-Plugins</span>
    <h3>Plugins ohne Boilerplate</h3>
<p>Installieren Sie ein Plugin-Paket und übergeben Sie es an Ihre <code>Admin</code>-Instanz. Felder, Konverter, Templates und Assets verdrahten sich automatisch miteinander.</p>
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
    <a class="home-more" href="advanced/plugins/">Die Plugin-Anleitung lesen</a>
  </div>
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-emerald">Erweiterungspunkte</span>
    <h3>In jede Komponente einhängen</h3>
    <p>Vordefinierte Interfaces ermöglichen es Ihnen, jeden Bereich unabhängig auszutauschen oder zu erweitern. Leiten Sie von der Basisklasse ab, die Sie benötigen, und registrieren Sie sie. Sie können alles anpassen, vom Authentifizierungsfluss bis zu den Exportformaten.</p>
    <ul class="home-hooks">
      <li><a href="advanced/custom-fields/"><span>Benutzerdefinierte Felder</span><code>BaseField</code></a></li>
      <li><a href="advanced/custom-filters/"><span>Benutzerdefinierte Filter</span><code>BaseFilter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Exporter</span><code>BaseExporter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Importer</span><code>BaseImporter</code></a></li>
      <li><a href="advanced/custom-themes/"><span>Themes</span><code>BaseTheme</code></a></li>
      <li><a href="user-guide/auth/"><span>Auth-Anbieter</span><code>BaseAuthProvider</code></a></li>
      <li><a href="user-guide/file-storage/"><span>Storage-Backends</span><code>BaseStorage</code></a></li>
      <li><a href="user-guide/custom-views/"><span>Dashboard-Widgets</span><code>BaseWidget</code></a></li>
      <li><a href="advanced/templates/"><span>Templates</span><code>templates_dir</code></a></li>
    </ul>
    <a class="home-more" href="advanced/extension-points/">Alle Erweiterungspunkte entdecken</a>
  </div>
</div>
