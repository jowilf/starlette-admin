---
title: Interfaces de administración extensibles para FastAPI y Starlette
description: Genere una interfaz de administración completa a partir de sus modelos
  de SQLAlchemy, SQLModel, Beanie, MongoEngine o Tortoise ORM.
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
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/)
<!-- translation-notice:end -->

<div class="home-hero">
  <a class="home-badge" href="changelog/">
    <span class="home-badge-dot"></span>
    Nueva documentación &nbsp;·&nbsp; Vea qué ha cambiado
  </a>
  <h1 class="home-title">Interfaces de administración <span class="home-gradient">extensibles</span><br>para FastAPI &amp; Starlette</h1>
  <p class="home-sub">Genere una interfaz de administración completa a partir de sus modelos de SQLAlchemy, SQLModel, Beanie, MongoEngine o Tortoise ORM. Construido sobre el <a href="https://tabler.io">kit de interfaz de usuario Tabler</a>, starlette-admin le ofrece vistas de lista, formularios generados automáticamente, exportación de datos y autenticación segura. Configure toda la interfaz en Python, sin escribir código de frontend.</p>
  <div class="home-actions">
    <a class="md-button md-button--primary home-btn" href="getting-started/quickstart/">Comenzar</a>
    <a class="md-button home-btn" href="https://starlette-admin-demo.jowilf.com/">Demostración en vivo</a>
    <a class="md-button home-btn home-btn--github" href="https://github.com/jowilf/starlette-admin">
      <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      Dar una estrella en GitHub
    </a>
  </div>
  <div class="home-pip"><code>pip install starlette-admin</code></div>
  <div class="home-shot">
    <img src="assets/images/list-preview.png" alt="starlette-admin dashboard showing statistical widgets, recent activity tables, and a sidebar for model views" loading="lazy">
  </div>
</div>

<h2 class="home-section-title">Funcionalidades integradas</h2>
<p class="home-lede">Todo lo que necesita funciona desde el primer momento. Cada funcionalidad principal incluye puntos de extensión documentados, de modo que pueda adaptarla a sus requisitos.</p>

<div class="home-cards">
  <a class="home-card" href="user-guide/views/">
    <span class="home-card-icon hc-sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/><path d="M10 3v18"/></svg></span>
    <h3>Tablas</h3>
    <p>Explore, busque y ordene sus datos con paginación, ordenación por varias columnas y URL que conservan el estado. Edite los campos en línea desde la vista de lista.</p>
  </a>
  <a class="home-card" href="user-guide/filters/">
    <span class="home-card-icon hc-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v2.172a2 2 0 0 1-.586 1.414L15 12v7l-6 2v-8.5L4.52 7.572A2 2 0 0 1 4 6.227z"/></svg></span>
    <h3>Filtros</h3>
    <p>Cree consultas AND/OR anidadas en la interfaz, con operadores adaptados al tipo de dato para texto, números, fechas y booleanos.</p>
  </a>
  <a class="home-card" href="user-guide/fields/">
    <span class="home-card-icon hc-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1"/><path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3z"/><path d="M16 5l3 3"/></svg></span>
    <h3>Formularios y cargas de archivos</h3>
    <p>Genere formularios automáticamente para más de 25 tipos de campo y para datos relacionales. Envíe las cargas de archivos a almacenamiento local o S3.</p>
  </a>
  <a class="home-card" href="user-guide/actions/">
    <span class="home-card-icon hc-rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3v7h6l-8 11v-7H5z"/></svg></span>
    <h3>Acciones</h3>
    <p>Cree operaciones masivas y a nivel de fila con decoradores estándar de Python. Proteja cada ejecución detrás de modales de confirmación y formularios de payload personalizados.</p>
  </a>
  <a class="home-card" href="user-guide/export-import/">
    <span class="home-card-icon hc-emerald"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M7 11l5 5 5-5"/><path d="M12 4v12"/></svg></span>
    <h3>Exportación e importación</h3>
    <p>Exporte registros a CSV, Excel, JSON, PDF o cualquier formato compatible con tablib. Importe datos en bloque con un asistente que muestra primero la vista previa y valida cada fila antes de escribir en la base de datos.</p>
  </a>
  <a class="home-card" href="user-guide/auth/">
    <span class="home-card-icon hc-indigo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3A12 12 0 0 1 12 21 12 12 0 0 1 3.5 6 12 12 0 0 0 12 3"/><circle cx="12" cy="11" r="1"/><path d="M12 12v2.5"/></svg></span>
    <h3>Autenticación y seguridad</h3>
    <p>Conecte el proveedor de autenticación que ya utiliza. Despliegue con valores predeterminados listos para producción, incluida la protección CSRF y límites integrados para exportaciones e importaciones.</p>
  </a>
  <a class="home-card" href="user-guide/inline-forms/">
    <span class="home-card-icon hc-cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8"/><path d="M13 9h5"/><path d="M13 15h8"/><path d="M13 19h5"/><rect x="3" y="4" width="6" height="6" rx="1"/><rect x="3" y="14" width="6" height="6" rx="1"/></svg></span>
    <h3>Formularios en línea</h3>
    <p>Gestione los datos relacionales en su lugar. Edite los registros secundarios dentro del formulario del modelo principal sin salir de la página.</p>
  </a>
  <a class="home-card" href="user-guide/custom-views/">
    <span class="home-card-icon hc-orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/></svg></span>
    <h3>Paneles de control</h3>
    <p>Cree una página de inicio a partir de widgets integrados de estadísticas, gráficos y tablas, o reemplácela por una vista totalmente personalizada.</p>
  </a>
  <a class="home-card" href="user-guide/i18n/">
    <span class="home-card-icon hc-teal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h7"/><path d="M9 3v2c0 4.418-2.239 8-5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4-9 4 9"/><path d="M19.1 18h-6.2"/></svg></span>
    <h3>i18n y zonas horarias</h3>
    <p>Sirva el panel de administración en varios idiomas, con formato adaptado a la configuración regional y manejo preciso de zonas horarias desde el primer momento.</p>
  </a>
</div>

<div class="home-code-head">
  <svg class="home-code-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg>
  <h2 class="home-section-title">Todo es Python</h2>
  <p class="home-lede">Cree una interfaz de administración completa con una API pura de Python diseñada para el <strong>desarrollo rápido</strong>, la <strong>sintaxis legible</strong> y el <strong>mantenimiento a largo plazo</strong>.</p>
</div>

=== "Montar el admin"

    <span class="home-tour-title" role="heading" aria-level="3">Montar el panel de administración</span>

    Registre un modelo y monte el panel de administración en cualquier aplicación de FastAPI o Starlette. A continuación, ejecute `fastapi dev` y abra `/admin`.

    <a class="home-tour-btn" href="getting-started/quickstart/">Ver la documentación</a>

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

=== "Vistas"

    <span class="home-tour-title" role="heading" aria-level="3">Vistas</span>

    Defina la búsqueda, la ordenación, el orden predeterminado y los formatos de exportación con atributos de clase sencillos. Organice sus formularios de creación y edición con `form_layout`.

    <a class="home-tour-btn" href="user-guide/views/">Ver la documentación</a>

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

=== "Campos"

    <span class="home-tour-title" role="heading" aria-level="3">Campos</span>

    Sustituya cualquier campo detectado automáticamente para controlar la validación, la visibilidad por página y cómo starlette-admin lee y muestra los valores.

    <a class="home-tour-btn" href="user-guide/fields/">Ver la documentación</a>

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

=== "Filtros"

    <span class="home-tour-title" role="heading" aria-level="3">Filtros</span>

    Amplíe el constructor de consultas integrado con filtros personalizados que se ajusten a sus reglas de negocio. Puede aplicar las operaciones que necesite directamente sobre el modelo de base de datos subyacente.

    <a class="home-tour-btn" href="user-guide/filters/">Ver la documentación</a>

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

=== "Acciones"

    <span class="home-tour-title" role="heading" aria-level="3">Acciones</span>

    Adjunte operaciones de negocio con un solo decorador. Los modales de confirmación, los formularios personalizados y los mensajes flash están integrados en el framework.

    <a class="home-tour-btn" href="user-guide/actions/">Ver la documentación</a>

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

=== "Autenticación"

    <span class="home-tour-title" role="heading" aria-level="3">Autenticación</span>

    Implemente tres métodos estándar en torno a su propia comprobación de credenciales. starlette-admin gestiona por usted la página de inicio de sesión, las sesiones y las redirecciones.

    <a class="home-tour-btn" href="user-guide/auth/">Ver la documentación</a>

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

=== "Panel de control"

    <span class="home-tour-title" role="heading" aria-level="3">Panel de control</span>

    Componga la página de inicio del panel de administración con widgets de estadísticas, gráficos y tablas que consultan datos en vivo en cada solicitud.

    <a class="home-tour-btn" href="user-guide/custom-views/">Ver la documentación</a>

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

<h2 class="home-section-title">Plugins y extensiones</h2>
<p class="home-lede">Cada capa es sustituible. Empaquete funcionalidades como plugins autocontenidos o conéctese a un punto de extensión dedicado para adaptar el framework a su dominio.</p>

<div class="home-plugins">
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-violet">Plugins listos para usar</span>
    <h3>Plugins sin boilerplate</h3>
<p>Instale un paquete de plugin y páselo a su instancia de <code>Admin</code>. Los campos, convertidores, plantillas y recursos se conectan entre sí automáticamente.</p>
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
    <a class="home-more" href="advanced/plugins/">Lea la guía de plugins</a>
  </div>
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-emerald">Puntos de extensión</span>
    <h3>Conéctese a cualquier componente</h3>
    <p>Las interfaces predefinidas le permiten sustituir o extender cada aspecto de forma independiente. Cree una subclase de la clase base que necesite y regístrela. Puede personalizarlo todo, desde el flujo de autenticación hasta los formatos de exportación.</p>
    <ul class="home-hooks">
      <li><a href="advanced/custom-fields/"><span>Campos personalizados</span><code>BaseField</code></a></li>
      <li><a href="advanced/custom-filters/"><span>Filtros personalizados</span><code>BaseFilter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Exportadores</span><code>BaseExporter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Importadores</span><code>BaseImporter</code></a></li>
      <li><a href="advanced/custom-themes/"><span>Temas</span><code>BaseTheme</code></a></li>
      <li><a href="user-guide/auth/"><span>Proveedores de autenticación</span><code>BaseAuthProvider</code></a></li>
      <li><a href="user-guide/file-storage/"><span>Backends de almacenamiento</span><code>BaseStorage</code></a></li>
      <li><a href="user-guide/custom-views/"><span>Widgets del panel</span><code>BaseWidget</code></a></li>
      <li><a href="advanced/templates/"><span>Plantillas</span><code>templates_dir</code></a></li>
    </ul>
    <a class="home-more" href="advanced/extension-points/">Explore todos los puntos de extensión</a>
  </div>
</div>
