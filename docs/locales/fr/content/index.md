---
title: Interfaces d'administration extensibles pour FastAPI et Starlette
description: Générez une interface d'administration complète à partir de vos modèles
  SQLAlchemy, SQLModel, Beanie, MongoEngine ou Tortoise ORM.
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
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/)
<!-- translation-notice:end -->

<div class="home-hero">
  <a class="home-badge" href="changelog/">
    <span class="home-badge-dot"></span>
    Nouvelle documentation &nbsp;·&nbsp; Découvrez ce qui a changé
  </a>
  <h1 class="home-title"><span class="home-gradient">Interfaces d'administration</span> extensibles<br>pour FastAPI et Starlette</h1>
  <p class="home-sub">Générez une interface d'administration complète à partir de vos modèles SQLAlchemy, SQLModel, Beanie, MongoEngine ou Tortoise ORM. Basé sur le <a href="https://tabler.io">kit UI Tabler</a>, starlette-admin vous offre des vues en liste, des formulaires générés automatiquement, des exports de données et une authentification sécurisée. Configurez l'intégralité de l'interface en Python, sans écrire la moindre ligne de code frontend.</p>
  <div class="home-actions">
    <a class="md-button md-button--primary home-btn" href="getting-started/quickstart/">Premiers pas</a>
    <a class="md-button home-btn" href="https://starlette-admin-demo.jowilf.com/">Démo en direct</a>
    <a class="md-button home-btn home-btn--github" href="https://github.com/jowilf/starlette-admin">
      <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      Star sur GitHub
    </a>
  </div>
  <div class="home-pip"><code>pip install starlette-admin</code></div>
  <div class="home-shot">
    <img src="assets/images/list-preview.png" alt="tableau de bord starlette-admin avec widgets statistiques, tables d'activité récente et barre latérale pour les vues de modèles" loading="lazy">
  </div>
</div>

<h2 class="home-section-title">Fonctionnalités intégrées</h2>
<p class="home-lede">Tout ce dont vous avez besoin fonctionne dès l'installation. Chaque fonctionnalité principale inclut des points d'extension documentés, afin que vous puissiez l'adapter à vos exigences.</p>

<div class="home-cards">
  <a class="home-card" href="user-guide/views/">
    <span class="home-card-icon hc-sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/><path d="M10 3v18"/></svg></span>
    <h3>Tables</h3>
    <p>Parcourez, recherchez et triez vos données avec pagination, tri multi-colonnes et URLs préservant l'état. Modifiez les champs directement depuis la vue en liste.</p>
  </a>
  <a class="home-card" href="user-guide/filters/">
    <span class="home-card-icon hc-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v2.172a2 2 0 0 1-.586 1.414L15 12v7l-6 2v-8.5L4.52 7.572A2 2 0 0 1 4 6.227z"/></svg></span>
    <h3>Filtres</h3>
    <p>Composez des requêtes AND/OR imbriquées dans l'interface, avec des opérateurs adaptés aux types pour le texte, les nombres, les dates et les booléens.</p>
  </a>
  <a class="home-card" href="user-guide/fields/">
    <span class="home-card-icon hc-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1"/><path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3z"/><path d="M16 5l3 3"/></svg></span>
    <h3>Formulaires et téléversements</h3>
    <p>Générez automatiquement des formulaires pour plus de 25 types de champs ainsi que pour les données relationnelles. Envoyez les fichiers vers un stockage local ou S3.</p>
  </a>
  <a class="home-card" href="user-guide/actions/">
    <span class="home-card-icon hc-rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3v7h6l-8 11v-7H5z"/></svg></span>
    <h3>Actions</h3>
    <p>Créez des opérations en masse ou au niveau de chaque ligne avec de simples décorateurs Python. Protégez chaque exécution derrière des modales de confirmation et des formulaires de payload personnalisés.</p>
  </a>
  <a class="home-card" href="user-guide/export-import/">
    <span class="home-card-icon hc-emerald"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M7 11l5 5 5-5"/><path d="M12 4v12"/></svg></span>
    <h3>Export et import</h3>
    <p>Exportez vos enregistrements en CSV, Excel, JSON, PDF ou dans tout format pris en charge par tablib. Importez des données en masse grâce à un assistant axé sur l'aperçu qui valide chaque ligne avant toute écriture en base.</p>
  </a>
  <a class="home-card" href="user-guide/auth/">
    <span class="home-card-icon hc-indigo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3A12 12 0 0 1 12 21 12 12 0 0 1 3.5 6 12 12 0 0 0 12 3"/><circle cx="12" cy="11" r="1"/><path d="M12 12v2.5"/></svg></span>
    <h3>Authentification et sécurité</h3>
    <p>Connectez le fournisseur d'authentification que vous utilisez déjà. Déployez avec des réglages prêts pour la production, incluant la protection CSRF et des limites intégrées pour les exports et imports.</p>
  </a>
  <a class="home-card" href="user-guide/inline-forms/">
    <span class="home-card-icon hc-cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8"/><path d="M13 9h5"/><path d="M13 15h8"/><path d="M13 19h5"/><rect x="3" y="4" width="6" height="6" rx="1"/><rect x="3" y="14" width="6" height="6" rx="1"/></svg></span>
    <h3>Formulaires inline</h3>
    <p>Gérez les données relationnelles directement sur place. Modifiez les enregistrements enfants dans le formulaire du modèle parent sans quitter la page.</p>
  </a>
  <a class="home-card" href="user-guide/custom-views/">
    <span class="home-card-icon hc-orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/></svg></span>
    <h3>Tableaux de bord</h3>
    <p>Construisez une page d'accueil à partir de widgets statistiques, graphiques et tableaux intégrés, ou remplacez-la par une vue entièrement personnalisée.</p>
  </a>
  <a class="home-card" href="user-guide/i18n/">
    <span class="home-card-icon hc-teal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h7"/><path d="M9 3v2c0 4.418-2.239 8-5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4-9 4 9"/><path d="M19.1 18h-6.2"/></svg></span>
    <h3>i18n et fuseaux horaires</h3>
    <p>Servez l'interface d'administration en plusieurs langues, avec un formatage tenant compte de la locale et une gestion précise des fuseaux horaires, dès l'installation.</p>
  </a>
</div>

<div class="home-code-head">
  <svg class="home-code-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg>
  <h2 class="home-section-title">Tout se fait en Python</h2>
  <p class="home-lede">Construisez une interface d'administration complète avec une API Python pure, conçue pour le <strong>développement rapide</strong>, une <strong>syntaxe lisible</strong> et une <strong>maintenabilité durable</strong>.</p>
</div>

=== "Monter l'admin"

    <span class="home-tour-title" role="heading" aria-level="3">Monter le panneau d'administration</span>

    Enregistrez un modèle et montez le panneau d'administration sur n'importe quelle application FastAPI ou Starlette. Exécutez ensuite `fastapi dev` et ouvrez `/admin`.

    <a class="home-tour-btn" href="getting-started/quickstart/">Consulter la documentation</a>

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

=== "Vues"

    <span class="home-tour-title" role="heading" aria-level="3">Vues</span>

    Définissez la recherche, le tri, l'ordre par défaut et les formats d'export à l'aide de simples attributs de classe. Agencez vos formulaires de création et d'édition avec `form_layout`.

    <a class="home-tour-btn" href="user-guide/views/">Consulter la documentation</a>

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

=== "Champs"

    <span class="home-tour-title" role="heading" aria-level="3">Champs</span>

    Remplacez n'importe quel champ détecté automatiquement pour contrôler la validation, la visibilité par page et la façon dont starlette-admin lit et affiche les valeurs.

    <a class="home-tour-btn" href="user-guide/fields/">Consulter la documentation</a>

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

=== "Filtres"

    <span class="home-tour-title" role="heading" aria-level="3">Filtres</span>

    Étendez le générateur de requêtes intégré avec des filtres personnalisés qui reflètent vos règles métier. Vous pouvez appliquer les opérations dont vous avez besoin directement sur le modèle de base de données sous-jacent.

    <a class="home-tour-btn" href="user-guide/filters/">Consulter la documentation</a>

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

    <span class="home-tour-title" role="heading" aria-level="3">Actions</span>

    Attachez des opérations métier avec un seul décorateur. Les modales de confirmation, les formulaires personnalisés et les messages flash sont intégrés au framework.

    <a class="home-tour-btn" href="user-guide/actions/">Consulter la documentation</a>

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

=== "Authentification"

    <span class="home-tour-title" role="heading" aria-level="3">Authentification</span>

    Implémentez trois méthodes standard autour de votre propre vérification des identifiants. starlette-admin gère pour vous la page de connexion, les sessions et les redirections.

    <a class="home-tour-btn" href="user-guide/auth/">Consulter la documentation</a>

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

=== "Tableau de bord"

    <span class="home-tour-title" role="heading" aria-level="3">Tableau de bord</span>

    Composez la page d'accueil de l'admin à partir de widgets statistiques, graphiques et tableaux qui interrogent des données en temps réel à chaque requête.

    <a class="home-tour-btn" href="user-guide/custom-views/">Consulter la documentation</a>

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

<h2 class="home-section-title">Plugins et extensions</h2>
<p class="home-lede">Chaque couche est remplaçable. Empaquetez des fonctionnalités sous forme de plugins autonomes, ou accrochez-vous à un point d'extension dédié pour adapter le framework à votre domaine.</p>

<div class="home-plugins">
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-violet">Plugins prêts à l'emploi</span>
    <h3>Des plugins sans code superflu</h3>
<p>Installez un paquet de plugin et transmettez-le à votre instance <code>Admin</code>. Champs, convertisseurs, templates et ressources se connectent entre eux automatiquement.</p>
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
    <a class="home-more" href="advanced/plugins/">Lire le guide des plugins</a>
  </div>
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-emerald">Points d'extension</span>
    <h3>Accrochez-vous à n'importe quel composant</h3>
    <p>Des interfaces prédéfinies vous permettent de remplacer ou d'étendre chaque préoccupation de manière indépendante. Héritez de la classe de base souhaitée et enregistrez-la. Vous pouvez tout personnaliser, du flux d'authentification aux formats d'export.</p>
    <ul class="home-hooks">
      <li><a href="advanced/custom-fields/"><span>Champs personnalisés</span><code>BaseField</code></a></li>
      <li><a href="advanced/custom-filters/"><span>Filtres personnalisés</span><code>BaseFilter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Exporters</span><code>BaseExporter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Importers</span><code>BaseImporter</code></a></li>
      <li><a href="advanced/custom-themes/"><span>Thèmes</span><code>BaseTheme</code></a></li>
      <li><a href="user-guide/auth/"><span>Fournisseurs d'authentification</span><code>BaseAuthProvider</code></a></li>
      <li><a href="user-guide/file-storage/"><span>Backends de stockage</span><code>BaseStorage</code></a></li>
      <li><a href="user-guide/custom-views/"><span>Widgets du tableau de bord</span><code>BaseWidget</code></a></li>
      <li><a href="advanced/templates/"><span>Templates</span><code>templates_dir</code></a></li>
    </ul>
    <a class="home-more" href="advanced/extension-points/">Explorer tous les points d'extension</a>
  </div>
</div>
