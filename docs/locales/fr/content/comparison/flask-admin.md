---
title: Migrer depuis Flask-Admin
description: Un guide de migration directe de Flask-Admin vers starlette-admin, montrant
  comment faire évoluer vos configurations ModelView vers l'écosystème ASGI.
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# Migrer depuis Flask-Admin

starlette-admin est né d'un portage des concepts de Flask-Admin vers l'écosystème ASGI ; la migration est donc directe. Vous continuez à hériter d'une `ModelView`, à la configurer avec des attributs de classe et à l'enregistrer sur une instance d'`Admin`. L'essentiel du travail consiste à renommer des attributs et à passer du contexte de requête implicite de Flask à l'objet `request` explicite de Starlette.

Ce guide met en correspondance l'API de Flask-Admin, attribut par attribut, avec son équivalent starlette-admin.

## Modèle mental

| Concept Flask-Admin | Équivalent starlette-admin |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, puis `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)` ; l'instance d'`Admin` possède l'engine et les sessions de base de données |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| backends peewee / pymongo | Beanie, Tortoise ORM, SQLModel, ou un [backend personnalisé](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Contexte de requête Flask (`flask.request`) | Paramètre explicite `request: Request` sur chaque hook |
| Méthodes synchrones | Méthodes `async` ; le synchrone fonctionne toujours là où des callables sont acceptés |

## Configuration

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

Il n'existe pas d'interrupteur `template_mode`. L'interface utilise [Tabler](https://tabler.io) (Bootstrap 5) et inclut le mode sombre. Pour changer l'apparence, écrivez une [`BaseTheme`](../advanced/custom-themes.md) personnalisée ou [remplacez les templates](../advanced/templates.md).

## Attributs de la page de liste

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `column_list` | `fields` | Détermine également les pages de détail et de formulaire. Utilisez les attributs `exclude_fields_from_*` pour des variantes par page. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Par exemple, `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | S'applique à la définition du champ. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) sur le champ | Par exemple, `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / formatters d'export | Le même dictionnaire `formatter=`, indexé par `RequestAction` | Un seul mappage couvre le formatage pour la liste, le détail et l'export. Les actions sans entrée conservent la valeur brute. |
| `column_type_formatters` | `formatter=` par champ, ou une sous-classe de champ personnalisée | Il n'existe pas de registre par type. Attachez le formatter à chaque champ, ou [sous-classez le champ](../advanced/custom-fields.md) et réutilisez-le. |
| Propriétés du modèle ou callables dans `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) ou `getter=` sur n'importe quel champ | Ajoute des colonnes virtuelles ou redirige la recherche de valeur d'un champ existant, sans sous-classe. |
| Champs WTForms personnalisés (coercion de valeur) | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) sur le champ | Remplace l'analyse par défaut du formulaire ou de l'import selon le `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | `searchable_fields` combiné avec `filters=` par champ | Remplace la liste plate de filtres par un [constructeur visuel](../user-guide/filters.md) prenant en charge des groupes imbriqués `AND`/`OR`. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Par exemple, `[("created_at", True)]` trie par ordre décroissant. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | L'utilisateur sélectionne une cellule et la modifie sur place. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Vaut par défaut `[10, 25, 50, 100]`. L'utilisateur choisit parmi ces options. |
| `column_display_pk` | Inclure la clé primaire dans `fields` |  |
| `column_details_list` | `fields` moins `exclude_fields_from_detail` | La page de détail est intégrée. Il n'existe pas d'option `can_view_details`. |

## Attributs de formulaire

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `form_columns` | `fields` moins `exclude_fields_from_create` et `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Contrôles de visibilité distincts par formulaire. |
| `form_overrides` | Instances de champs explicites dans `fields` | Par exemple, `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Arguments du constructeur du champ | Par exemple, `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Par exemple, `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Entrées supplémentaires dans `fields` | Prend en charge tout champ non adossé à une colonne de base de données, tel qu'un [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Attributs du champ | Définissez `read_only`, `disabled` ou `placeholder` directement sur le champ. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Remplace les règles plates par des fieldsets, des onglets et des grilles responsives. |
| `create_modal` / `edit_modal` | Non disponible | Les vues de création et d'édition s'affichent comme des pages complètes. |
| `on_form_prefill` | Hook `before_edit` |  |

## Export et import

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

L'export CSV et JSON est activé par défaut. Des limites de lignes s'appliquent automatiquement, et l'échappement des formules de tableur est une option d'exporter à activer explicitement. L'import, que Flask-Admin ne propose pas, inclut une étape d'aperçu avec validation ligne par ligne et mises à jour optionnelles des enregistrements existants par clé primaire. Voir [Export et import](../user-guide/export-import.md).

## Actions

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

Le gestionnaire reçoit un objet [`ActionSelection`](../user-guide/actions.md) au lieu d'identifiants bruts. Il résout les lignes paresseusement, expose les filtres actifs et se comporte de la même manière lorsqu'un utilisateur sélectionne tous les enregistrements correspondants sur l'ensemble des pages. Les actions peuvent également afficher un formulaire HTML personnalisé dans la boîte de dialogue de confirmation. Pour les opérations par ligne, [`@row_action` et `@link_row_action`](../user-guide/actions.md#row-actions) remplacent les formatters de colonne personnalisés.

## Permissions et contrôle d'accès

Les indicateurs de classe `can_*` de Flask-Admin deviennent des [méthodes par requête](../user-guide/views.md#security-and-authorization) dans starlette-admin, si bien que les décisions d'autorisation peuvent dépendre de l'utilisateur connecté.

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Masque la vue dans le menu et bloque l'accès direct. |
| `inaccessible_callback()` | Pris en charge par le flux d'authentification | Les requêtes non authentifiées sont redirigées vers la page de connexion. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` et `can_delete` suivent le même schéma. |
| `can_view_details` | `can_view_detail(request)` | La page de détail existe par défaut. |
| `can_export` | `can_export(request)`, plus `can_import(request)` |  |
| Aucun équivalent | `can_access_field(request, field)` | Contrôle la visibilité des champs par utilisateur. |
| Aucun équivalent | `is_action_allowed(request, name)` | Fournit une autorisation par action. |

Avec Flask-Admin, vous intégrez Flask-Login vous-même. starlette-admin fournit un [`AuthProvider`](../user-guide/auth.md) accompagné d'une page de connexion prête à l'emploi, et vous implémentez les méthodes `login`, `logout` et `authenticate` auprès de votre magasin d'utilisateurs. Un `OAuthProvider` couvre les flux de redirection OIDC. L'utilisateur connecté est disponible partout via `request.state.admin_user`.

## Hooks du cycle de vie du modèle

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, spécifiques au backend SQLAlchemy |
| `handle_view_exception` | Levez `FormValidationError` ou `ActionFailed` |

Au-delà des hooks par vue, le [système d'événements](../advanced/events.md) permet à un seul gestionnaire d'observer toutes les vues. Flask-Admin n'a pas d'équivalent.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Vues personnalisées et page d'index

| Flask-Admin | starlette-admin | Notes |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Composez des pages à partir de [widgets](../user-guide/custom-views.md) sans écrire de templates bruts. |
| Rendu de templates personnalisés | Sous-classe de `CustomView` | Vous donne un contrôle total sur les routes et les réponses. |
| `AdminIndexView` | `Admin(index_view=...)` | Construisez des tableaux de bord à partir de `StatWidget`, `ChartWidget`, `TableWidget` et des widgets de mise en page. |
| `MenuLink` | Vue [`Link`](../user-guide/views.md#link) | Par exemple, `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Catégories dans le menu | Vue [`DropDown`](../user-guide/views.md#sidebar-organization) | Regroupe les vues ensemble dans la barre latérale. |
| `FileAdmin` | Non disponible | Les champs fichier et image avec [stockage local ou S3](../user-guide/file-storage.md) gèrent les pièces jointes. Il n'existe pas d'explorateur de fichiers côté serveur. |

## Modèles inline

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

Une classe explicite offre à chaque modèle inline toute la surface de configuration d'une `ModelView` : sélection des champs, validation et prise en charge des clés étrangères composites. Voir [Formulaires inline](../user-guide/inline-forms.md).

## Internationalisation

Flask-Admin dépend de Flask-Babel et de l'environnement Flask qui l'entoure. starlette-admin utilise plutôt un objet de configuration :

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Le rendu des dates et heures tenant compte des fuseaux horaires fonctionne de la même manière, via `TimezoneConfig`. Voir [Internationalisation et fuseaux horaires](../user-guide/i18n.md).

## Ce que vous gagnez en migrant

* **Une pile asynchrone.** Fonctionne nativement sous FastAPI et Starlette, avec prise en charge de SQLAlchemy asynchrone, Beanie et Tortoise ORM. Flask-Admin est synchrone.
* **Des fonctionnalités de sécurité intégrées.** La protection CSRF, l'assainissement des noms de fichiers téléversés, la vérification du contenu des images et les limites de lignes d'export sont actives dès l'instanciation de `Admin`, et vous pouvez activer l'échappement des formules de tableur sur les exporters. Voir [Sécurité](../user-guide/security.md).
* **L'import de données.** Une étape d'aperçu valide chaque ligne avant toute écriture. Flask-Admin ne propose aucune fonctionnalité d'import.
* **Un système de widgets pour tableau de bord.** Construisez les pages d'index et les vues personnalisées en Python plutôt qu'en écrivant des templates à la main.
* **Un design moderne.** Une base de code activement maintenue, dotée d'une interface soignée, d'un mode sombre intégré et d'annotations de types de premier ordre.

## Ce à quoi vous devez vous adapter

* **Des objets `request` explicites.** Il n'existe pas de contexte de requête ambiant. Chaque hook et chaque méthode de permission reçoit la `request` en paramètre.
* **Des gestionnaires asynchrones.** Les hooks et les actions sont des coroutines ; évitez donc les appels bloquants ou déplacez ces traitements vers un thread.
* **Pas de `FileAdmin`.** Si votre flux de travail dépend de la navigation dans le système de fichiers du serveur, starlette-admin ne le couvre pas.
* **Pas de fenêtres modales de création ni d'édition.** Les formulaires s'affichent comme des pages complètes plutôt que comme des fenêtres contextuelles.
