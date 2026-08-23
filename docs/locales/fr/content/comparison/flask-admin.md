---
title: Migrer depuis Flask-Admin
description: Un guide de migration directe de Flask-Admin vers starlette-admin, montrant
  comment transposer vos configurations ModelView vers l'écosystème ASGI.
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
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

starlette-admin a commencé comme un portage des concepts de Flask-Admin vers l'écosystème ASGI ; la migration est donc directe. Vous héritez toujours d'une classe `ModelView`, vous la configurez avec des attributs de classe et vous l'enregistrez sur une instance `Admin`. L'essentiel du travail consiste à renommer des attributs et à passer du contexte de requête implicite de Flask à l'objet `request` explicite de Starlette.

Ce guide fait correspondre l'API de Flask-Admin, attribut par attribut, à son équivalent starlette-admin.

## Modèle mental

| Concept Flask-Admin | Équivalent starlette-admin |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, puis `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)` ; l'instance `Admin` possède le moteur et les sessions de base de données |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| backends peewee / pymongo | Beanie, Tortoise ORM, SQLModel, ou un [backend personnalisé](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Contexte de requête Flask (`flask.request`) | Paramètre `request: Request` explicite sur chaque hook |
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

Il n'y a pas de commutateur `template_mode`. L'interface utilise [Tabler](https://tabler.io) (Bootstrap 5) et inclut le mode sombre. Pour changer l'apparence, écrivez une classe [`BaseTheme`](../advanced/custom-themes.md) personnalisée ou [remplacez les templates](../advanced/templates.md).

## Attributs de la page de liste

| Flask-Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `column_list` | `fields` | Pilote également les pages de détail et de formulaire. Utilisez les attributs `exclude_fields_from_*` pour des variations par page. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Par exemple, `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | S'applique à la définition du champ. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#calculer-mettre-en-forme-et-analyser-les-valeurs) sur le champ | Par exemple, `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / formateurs d'exportation | Le même dictionnaire `formatter=`, indexé par `RequestAction` | Une seule correspondance couvre le formatage pour la liste, le détail et l'exportation. Les actions sans entrée conservent la valeur brute. |
| `column_type_formatters` | `formatter=` par champ, ou une sous-classe de champ personnalisée | Il n'existe pas de registre par type. Attachez le formateur à chaque champ, ou [créez une sous-classe du champ](../advanced/custom-fields.md) et réutilisez-la. |
| Propriétés du modèle ou callables dans `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) ou `getter=` sur n'importe quel champ | Ajoute des colonnes virtuelles, ou redirige la recherche de valeur d'un champ existant, sans sous-classe. |
| Champs WTForms personnalisés (conversion de valeur) | [`parser=`](../user-guide/fields.md#calculer-mettre-en-forme-et-analyser-les-valeurs) sur le champ | Remplace l'analyse par défaut du formulaire ou de l'importation du champ selon `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#recherche-et-tri) |  |
| `column_filters` | `searchable_fields` combiné aux `filters=` par champ | Remplace la liste plate de filtres par un [constructeur visuel](../user-guide/filters.md) qui prend en charge des groupes imbriqués `AND`/`OR`. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#recherche-et-tri) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#recherche-et-tri) | Par exemple, `[("created_at", True)]` trie dans l'ordre décroissant. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Les utilisateurs sélectionnent une cellule et la modifient sur place. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-et-controles-de-linterface) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-et-controles-de-linterface) | Valeurs par défaut : `[10, 25, 50, 100]`. Les utilisateurs choisissent parmi ces options. |
| `column_display_pk` | Incluez la clé primaire dans `fields` |  |
| `column_details_list` | `fields` moins `exclude_fields_from_detail` | La page de détail est intégrée. Il n'y a pas d'activation via `can_view_details`. |

## Attributs du formulaire

| Flask-Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `form_columns` | `fields` moins `exclude_fields_from_create` et `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Contrôles de visibilité distincts par formulaire. |
| `form_overrides` | Instances de champ explicites dans `fields` | Par exemple, `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Arguments du constructeur sur le champ | Par exemple, `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Par exemple, `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Entrées supplémentaires dans `fields` | Prend en charge tout champ non adossé à une colonne de base de données, tel qu'un [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Attributs du champ | Définissez `read_only`, `disabled` ou `placeholder` directement sur le champ. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Remplace les règles plates par des fieldsets, des onglets et des grilles responsives. |
| `create_modal` / `edit_modal` | Non disponible | Les vues de création et de modification s'affichent sous forme de pages complètes. |
| `on_form_prefill` | Hook `before_edit` |  |

## Exportation et importation

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

L'exportation CSV et JSON est activée par défaut. Des limites de lignes s'appliquent automatiquement, et l'échappement des formules de tableur est une option à activer sur l'exportateur. L'importation, que Flask-Admin ne fournit pas, comprend une étape d'aperçu avec validation ligne par ligne et mises à jour facultatives des enregistrements existants par clé primaire. Voir [Exportation et importation](../user-guide/export-import.md).

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

Le gestionnaire reçoit un objet [`ActionSelection`](../user-guide/actions.md) au lieu d'identifiants bruts. Il résout les lignes paresseusement, expose les filtres actifs et fonctionne de la même manière lorsqu'un utilisateur sélectionne tous les enregistrements correspondants sur plusieurs pages. Les actions peuvent également afficher un formulaire HTML personnalisé dans la boîte de dialogue de confirmation. Pour les opérations par ligne, [`@row_action` et `@link_row_action`](../user-guide/actions.md#actions-de-ligne) remplacent les formateurs de colonnes personnalisés.

## Autorisations et contrôle d'accès

Les indicateurs de classe `can_*` de Flask-Admin deviennent des [méthodes par requête](../user-guide/views.md#securite-et-autorisations) dans starlette-admin ; les décisions d'autorisation peuvent donc dépendre de l'utilisateur connecté.

| Flask-Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Masque la vue dans le menu et bloque l'accès direct. |
| `inaccessible_callback()` | Géré par le flux d'authentification | Les requêtes non authentifiées sont redirigées vers la page de connexion. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` et `can_delete` suivent le même modèle. |
| `can_view_details` | `can_view_detail(request)` | La page de détail existe par défaut. |
| `can_export` | `can_export(request)`, plus `can_import(request)` |  |
| Aucun équivalent | `can_access_field(request, field)` | Contrôle la visibilité des champs au niveau de chaque utilisateur. |
| Aucun équivalent | `is_action_allowed(request, name)` | Fournit une autorisation par action. |

Avec Flask-Admin, vous intégrez Flask-Login vous-même. starlette-admin fournit un [`AuthProvider`](../user-guide/auth.md) avec une page de connexion prête à l'emploi, et vous implémentez les méthodes `login`, `logout` et `authenticate` à partir de votre magasin d'utilisateurs. Un `OAuthProvider` couvre les flux de redirection OIDC. L'utilisateur connecté est disponible partout via `request.state.admin_user`.

## Hooks du cycle de vie des modèles

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#hooks-de-cycle-de-vie) |
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

| Flask-Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Composez des pages à partir de [widgets](../user-guide/custom-views.md) sans écrire de templates bruts. |
| Rendu de template personnalisé | Sous-classe de `CustomView` | Vous donne un contrôle total sur les routes et les réponses. |
| `AdminIndexView` | `Admin(index_view=...)` | Construisez des tableaux de bord à partir de `StatWidget`, `ChartWidget`, `TableWidget` et des widgets de mise en page. |
| `MenuLink` | Vue [`Link`](../user-guide/views.md#link) | Par exemple, `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Catégories dans le menu | Vue [`DropDown`](../user-guide/views.md#organisation-de-la-barre-laterale) | Regroupe les vues dans la barre latérale. |
| `FileAdmin` | Non disponible | Les champs de fichiers et d'images avec [stockage local ou S3](../user-guide/file-storage.md) gèrent les pièces jointes. Il n'y a pas d'explorateur de fichiers côté serveur. |

## Modèles en ligne

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

Une classe explicite donne à chaque modèle en ligne toute la surface de configuration de `ModelView` : sélection des champs, validation et prise en charge des clés étrangères composites. Voir [Formulaires en ligne](../user-guide/inline-forms.md).

## Internationalisation

Flask-Admin dépend de Flask-Babel et de l'environnement Flask environnant. starlette-admin utilise plutôt un objet de configuration :

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Le rendu des dates et heures tenant compte des fuseaux horaires fonctionne de la même manière, via `TimezoneConfig`. Voir [Internationalisation et fuseaux horaires](../user-guide/i18n.md).

## Ce que vous gagnez en migrant

* **Une pile asynchrone.** Fonctionne nativement avec FastAPI et Starlette, avec prise en charge de SQLAlchemy asynchrone, Beanie et Tortoise ORM. Flask-Admin est synchrone.
* **Des fonctionnalités de sécurité intégrées.** La protection CSRF, l'assainissement des noms de fichiers téléversés, la vérification du contenu des images et les limites de lignes à l'exportation sont actives dès l'instanciation de `Admin`, et vous pouvez activer l'échappement des formules de tableur sur les exportateurs. Voir [Sécurité](../user-guide/security.md).
* **L'importation de données.** Une étape d'aperçu valide chaque ligne avant toute écriture. Flask-Admin n'a pas de fonctionnalité d'importation.
* **Un système de widgets de tableau de bord.** Construisez les pages d'index et les vues personnalisées en Python au lieu d'écrire des templates à la main.
* **Un design moderne.** Une base de code activement maintenue avec une interface soignée, un mode sombre intégré et des annotations de type de premier ordre.

## Ce à quoi vous devez vous adapter

* **Des objets requête explicites.** Il n'existe pas de contexte de requête ambiant. Chaque hook et chaque méthode d'autorisation reçoit la `request` en paramètre.
* **Des gestionnaires asynchrones.** Les hooks et les actions sont des coroutines ; évitez donc les appels bloquants ou déplacez ce travail vers un thread.
* **Pas de `FileAdmin`.** Si votre flux de travail dépend de la navigation dans le système de fichiers du serveur, starlette-admin ne le couvre pas.
* **Pas de fenêtres modales de création ou de modification.** Les formulaires s'affichent sous forme de pages complètes plutôt que de fenêtres modales contextuelles.
