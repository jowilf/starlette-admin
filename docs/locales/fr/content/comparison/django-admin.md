---
title: Venir de Django Admin
description: Un guide de migration complet qui associe les concepts de Django Admin
  à leurs équivalents starlette-admin pour construire des interfaces d'administration
  déclaratives.
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

??? info "Traduction automatique supervisée"

    Ce contenu est généré par traduction automatique, guidée par des
    glossaires et des guides de style validés par des humains. Comme le
    texte n'est pas relu ligne par ligne, des erreurs ou des formulations
    maladroites peuvent parfois apparaître.

    En cas de divergence, la [version originale en anglais](https://jowilf.github.io/starlette-admin/) fait foi.

# Venir de Django Admin

Si vous connaissez Django Admin, starlette-admin vous semblera familier. Les deux génèrent une interface d'administration à partir d'une configuration déclarative par modèle, et tous deux prennent en charge l'édition en ligne, les actions groupées et les permissions par requête.

Les différences sont structurelles. starlette-admin fonctionne sur n'importe quelle application ASGI au lieu d'exiger Django, prend en charge plusieurs ORM, et vous permet de brancher votre propre authentification plutôt que d'imposer un modèle utilisateur intégré.

Ce guide associe chaque concept majeur de `ModelAdmin` à son équivalent starlette-admin, avec du code côte à côte.

## Modèle mental

| Concept Django Admin | Équivalent starlette-admin |
| --- | --- |
| `AdminSite` | Instance de [`Admin`](../api/admin.md) montée sur votre application |
| `ModelAdmin` | Sous-classe de [`ModelView`](../user-guide/views.md) |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` dans `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie ou Tortoise ORM via `starlette_admin.contrib.*` |
| `__str__` sur le modèle | `__admin_repr__(self, request)`, qui est asynchrone et sensible à la requête |
| Champs de formulaire déduits des champs du modèle | [Champs](../user-guide/fields.md) déduits par le convertisseur du backend, personnalisables champ par champ |

## Enregistrer un modèle

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

Deux différences structurelles se distinguent :

1. **Une seule liste de champs pilote chaque page.** `fields` est la source unique de vérité. Vous utilisez ensuite [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create` et `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization) pour les variations par page.
2. **L'instance de `Admin` possède le moteur de base de données.** Vous ne passez pas une session à chaque vue.

## Options de la page de liste

| Django Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `list_display` | `fields` moins [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | Une seule liste de champs pilote chaque page. |
| `list_display` avec un callable ou `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield), ou `getter=` sur n'importe quel champ | Par exemple, `ComputedField("full_name", getter=lambda request, obj: ...)`. Utilisez `getter=` sur un champ typé, comme un champ de date ou d'image, pour conserver le rendu de ce type. |
| Reformater une vraie colonne pour l'affichage | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) sur le champ | Un `dict[RequestAction, callable]`, ainsi la page de liste, la page de détail et l'exportation peuvent formater différemment. Django nécessite un callable plus `admin_order_field` pour conserver le tri ; ici la colonne reste triable. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | Alimente à la fois la recherche plein texte et le constructeur de filtres. |
| `list_filter` | `searchable_fields` combiné avec `filters=` par champ | Les utilisateurs obtiennent un constructeur visuel avec des groupes `AND`/`OR` imbriqués au lieu d'une barre latérale fixe. Voir [Filtres](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Par exemple, `fields_default_sort = [("created_at", True)]` trie dans l'ordre décroissant. |
| `admin_order_field` / triabilité | [`sortable_fields`](../user-guide/views.md#search-and-sort) | Chaque champ est triable par défaut. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Les utilisateurs sélectionnent une cellule et la modifient sur place. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Contrôle les limites de pagination. |
| `date_hierarchy` | Filtres de date, tels que `between` et `in the past` | Il n'y a pas de barre de navigation hiérarchique dédiée ; le constructeur de filtres couvre ce cas. |
| `empty_value_display` | Une entrée `formatter=`, ou `null_template` | Les formatters reçoivent les valeurs `None`, ils peuvent donc substituer un texte indicatif. `null_template` remplace le balisage rendu à la place. |

## Formulaires

| Django Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Contrôle la visibilité des champs du formulaire. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Composez librement avec `FieldsetWidget`, `TabsWidget`, `GridWidget` et `RowWidget`. |
| `readonly_fields` | `read_only=True` sur le champ | Vous pouvez également exclure le champ des vues de création et d'édition. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | Même comportement de slugification en direct. |
| `autocomplete_fields`, `raw_id_fields` | Comportement par défaut de [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) | Les widgets de relation sont des entrées Select2 avec recherche côté serveur dès l'installation. |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Rendu sous forme de composant multi-sélection avec recherche. |
| `formfield_overrides` | Entrées explicites dans la liste `fields` | Remplacez directement le champ détecté automatiquement : `fields = ["id", TextAreaField("bio")]` |
| Validation de formulaire personnalisée | `validators=` sur le champ ou `FormValidationError` dans les hooks | Voir [Validators](../api/validators.md). |
| `to_python()` du champ de formulaire / coercition personnalisée | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) sur le champ | Remplace l'analyse par défaut du formulaire ou de l'importation du champ selon `RequestAction`. |
| Texte d'aide du formulaire de modèle | `help_text=` | Disponible sur toute définition de champ. |

### Exemple de fieldsets

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

`form_layout` va plus loin que les fieldsets : vous pouvez construire des onglets, des grilles responsives et des mises en page imbriquées. Voir [Form Layout](../advanced/form-layout.md).

## Inlines

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

starlette-admin détecte la clé étrangère lorsqu'elle est non ambiguë, et il prend en charge les clés étrangères composites. Voir [Inline Forms](../user-guide/inline-forms.md) pour les configurations avancées.

## Actions

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

Là où Django Admin passe un `QuerySet`, le gestionnaire starlette-admin reçoit un objet [`ActionSelection`](../user-guide/actions.md). Il résout les lignes, les clés primaires et les filtres actifs paresseusement, et il se comporte de la même manière lorsqu'un utilisateur sélectionne tous les enregistrements correspondants.

Les actions peuvent également afficher un formulaire HTML personnalisé dans la boîte de dialogue de confirmation, ce qui, dans Django Admin, signifie construire une page intermédiaire. Pour les opérations par ligne, utilisez [`@row_action` et `@link_row_action`](../user-guide/actions.md#row-actions), qui n'ont pas d'équivalent dans Django Admin.

## Permissions et authentification

Django Admin délègue à `django.contrib.auth`. starlette-admin scinde le problème en deux : un [`AuthProvider`](../user-guide/auth.md) répond à « qui est cet utilisateur », et les [méthodes par vue](../user-guide/views.md#security-and-authorization) répondent à « que peut-il faire ».

| Django Admin | starlette-admin |
| --- | --- |
| Connexion via `django.contrib.auth` | `AuthProvider` (page de connexion intégrée) ou `OAuthProvider` (flux de redirection OIDC) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` sur la vue |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` par utilisateur | `can_access_field(request, field)` |
| Pas d'équivalent | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

La vue suivante restreint la suppression aux utilisateurs ayant le rôle `admin` :

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Chaque méthode `can_*` reçoit la requête, vos décisions d'autorisation peuvent donc lire l'utilisateur courant, les en-têtes HTTP ou tout autre élément de la requête.

## Hooks de sauvegarde et signaux

| Django Admin | starlette-admin | Remarques |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) sur la vue | Natif asynchrone, et reçoit les données de formulaire analysées avec l'instance du modèle. |
| `delete_model` | `before_delete` | Gère la logique avant suppression. |
| `post_save` et autres signaux | [Events](../advanced/events.md) | Par exemple, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` diffuse à toutes les vues. |
| Historique des modifications `LogEntry` | Construisez-le avec le système d'événements | Abonnez-vous à `AFTER_CREATE`, `AFTER_EDIT` et `AFTER_DELETE` pour remplir votre propre table d'audit. |
| `messages.success(request, ...)` | `flash(request, ...)` | Voir [Flash Messages](../user-guide/flash-messages.md). |

## Configuration globale du site

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Logo personnalisé via une surcharge de template | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` avec des [widgets](../user-guide/custom-views.md) pour un tableau de bord riche |
| Surcharges de templates dans `templates/admin/` | `Admin(templates_dir="...")`, voir [Templates](../advanced/templates.md) |
| Plusieurs instances de `AdminSite` | Plusieurs instances de `Admin` montées sur différents chemins d'application |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query` ou `get_detail_query` pour le backend SQLAlchemy |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, voir [i18n and Timezones](../user-guide/i18n.md) |

## Ce que vous gagnez en changeant

* **Asynchrone de bout en bout :** les gestionnaires, les hooks de cycle de vie et les callbacks de widget peuvent tous être des coroutines exécutées sur votre boucle d'événements existante, à côté de vos endpoints FastAPI.
* **Flexibilité de la base de données :** la même configuration d'administration s'applique que vous utilisiez SQLAlchemy, SQLModel, MongoDB via MongoEngine ou Beanie, ou Tortoise ORM.
* **Exportation et importation intégrées :** CSV, JSON et PDF, plus Excel et d'autres formats via `tablib`. Exportez directement des enregistrements, ou importez des données en masse via un assistant axé sur la prévisualisation qui applique une validation au niveau des lignes et prend en charge les upserts optionnels par clé primaire. Voir [Export and Import](../user-guide/export-import.md).
* **Widgets de tableau de bord :** les cartes statistiques, ApexCharts et les grilles de mise en page se combinent en pages d'accueil et vues personnalisées, vous n'avez donc pas besoin d'un package de thème externe pour construire un tableau de bord. Voir [Custom Views and Widgets](../user-guide/custom-views.md).
* **Interface utilisateur moderne :** Tabler (Bootstrap 5) vous offre le mode sombre, les bascules de visibilité des colonnes et la mise en surbrillance des résultats de recherche par défaut.

## Ce que vous devez apporter vous-même

* **Authentification :** il n'y a ni modèle utilisateur ni base de données de permissions fournis. Implémentez `AuthProvider.authenticate()` sur le magasin de données que votre application utilise déjà.
* **Journalisation d'audit :** starlette-admin ne génère pas de table `LogEntry`. Branchez le [système d'événements](../advanced/events.md) sur votre propre table d'audit.
* **Configuration UI au niveau du modèle :** les commodités de Django telles que `choices`, `verbose_name` et les validators au niveau du modèle ne sont pas transférées. Déclarez-les plutôt sur le champ starlette-admin, avec `EnumField`, `label=` et `validators=`.
