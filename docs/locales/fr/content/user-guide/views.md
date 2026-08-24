---
title: Vues
description: Apprenez à configurer les vues de liste et de détail dans starlette-admin,
  y compris la recherche, le tri et la pagination.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# Vues

`starlette-admin` construit sa barre latérale à partir de trois types de vue : `ModelView` expose un modèle de base de données, `CustomView` affiche une page autonome et `Link` ajoute un hyperlien.

## ModelView

Une sous-classe de `ModelView` est le moyen d'exposer un modèle de base de données dans l'admin. Les attributs de classe et les méthodes surchargées de cette vue définissent l'apparence, le comportement et la gestion des données de la ressource.

Tous les exemples de cette section utilisent la configuration SQLAlchemy suivante :

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### Utilisation de base

Pour exposer le modèle `Post`, créez une sous-classe de `ModelView` et configurez ses attributs.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

Une classe de vue ne fait rien tant que vous ne l'avez pas enregistrée auprès d'une instance d'`Admin` :

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

Consultez [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) pour un admin fonctionnel construit de la même manière, sur un modèle `Post`.

L'enregistrement d'une vue génère des interfaces paginées, triables et recherchables pour lister, consulter, créer, modifier et supprimer des enregistrements. Vous n'écrivez ni routes ni templates.

!!! note
    Vous importez `ModelView` depuis le package contrib de votre backend, tel que `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` ou `.tortoise`. **Chaque attribut décrit ci-dessous est identique quel que soit le backend**, ce qui vous permet de remplacer plus tard un modèle SQLAlchemy par un document MongoEngine sans modifier votre logique de vue.

### Configuration principale

#### Nommage et routage

Par défaut, l'admin dérive le routage URL et les libellés de l'interface du nom de classe du modèle. Pour le modèle `Post`, il utilise :

* **Clé :** `post` (URL : `/admin/post/list`)
* **Libellé de menu :** `Posts` (entrée dans la barre latérale)
* **Nom d'affichage :** `Post` (boutons de l'interface tels que **New Post**)

Lorsque les valeurs dérivées ne conviennent pas, redéfinissez-les lors de l'enregistrement ou dans le constructeur.

| Attribut | Description | Exemple de redéfinition | Interface ou URL résultante |
| --- | --- | --- | --- |
| **`key`** | Le slug interne et la route URL de base. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | Le nom au pluriel utilisé dans la barre latérale. | `menu_label="Blog Posts"` | **Barre latérale :** Blog Posts |
| **`display_name`** | Le nom au singulier utilisé dans les actions et les formulaires. | `display_name="Article"` | **Boutons :** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Sélection et personnalisation des champs {#field-selection-and-customization}

La liste `fields` définit quels attributs du modèle apparaissent dans la vue de liste, la page de détail et les formulaires. Omettez-la pour exposer tous les attributs du modèle.

Mélangez des noms sous forme de chaînes et des instances explicites de `BaseField` pour contrôler les widgets, la validation et les libellés :

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    L'admin détecte la clé primaire pour vous. Définissez `pk_attr` uniquement lorsque la détection échoue, par exemple sur un backend personnalisé sans clé primaire à champ unique.

#### Visibilité contextuelle des champs

Certains champs ont leur place dans la liste ou la page de détail, mais pas dans un formulaire de création, comme les horodatages et les statuts gérés par le système. Utilisez les attributs `exclude_fields_from_*` pour masquer un champ sur des surfaces spécifiques :

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Les attributs d'exclusion disponibles se terminent par `_create`, `_edit`, `_list`, `_detail`, `_export` et `_import`.

!!! important
    Pour permettre aux utilisateurs de définir la clé primaire lors de la création d'un enregistrement — désactivé par défaut — définissez `show_pk_in_forms = True`.

#### Disposition des formulaires

Par défaut, `fields` affiche vos formulaires de création et de modification sous forme de liste verticale simple. Pour réorganiser l'interface sans toucher à vos définitions de données, utilisez l'attribut `form_layout`.

**Le raccourci tuple**

Pour une grille basique, vous n'avez pas besoin d'importer de classes de widget. Regroupez des noms de champs dans un tuple pour les afficher côte à côte sur une même ligne.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Widgets de disposition avancés**

À mesure que vos formulaires s'étoffent, structurez-les avec des widgets de disposition. Le raccourci tuple fonctionne également à l'intérieur de ceux-ci :

* **`PanelWidget` ou `FieldsetWidget` :** regroupez des champs liés sous un titre, ou rendez une section repliable.
* **`TabsWidget` :** séparez des catégories de données distinctes, telles que les informations de livraison et les métadonnées SEO, qui n'ont pas besoin d'être visibles simultanément.

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

Consultez [Form Layouts](../advanced/form-layout.md) pour les lignes multi-colonnes avec largeurs explicites, les onglets, le contenu statique et le comportement lié au contrôle d'accès.

### Fonctionnalités du tableau de données

#### Recherche et tri {#search-and-sort}

Contrôlez comment les utilisateurs trouvent et ordonnent les données avec `searchable_fields` et `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`** : active le constructeur de filtres et la zone de recherche globale. La recherche globale exécute une requête plein texte sur ces champs.
* **`sortable_fields`** : restreint les en-têtes de colonnes sur lesquels les utilisateurs peuvent trier. Une requête de tri portant sur un autre champ, transmise via les paramètres URL, est ignorée.
* **`fields_default_sort`** : définit l'état initial du tableau. Passez une chaîne seule pour trier par ordre croissant, un tuple avec `True` pour trier par ordre décroissant, ou un tuple avec `False` pour trier explicitement par ordre croissant. Enchaînez plusieurs éléments pour un tri multi-colonnes.

#### Pagination et contrôles d'interface {#pagination-and-ui-controls}

Ajustez finement la mise en page de la page de liste avec ces attributs :

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` et `page_size_options`** : la limite de pagination par défaut et les choix du menu déroulant.
* **`show_goto_page`** : ajoute un champ « aller à la page » pour les grands jeux de données.
* **`search_auto_submit`** : filtre pendant que l'utilisateur saisit son texte.
* **`show_detail_search`** : ajoute une zone de recherche sur la page de détail pour filtrer les tableaux de relations intégrés.
* **`row_click_navigate`** : ouvre la page de détail lorsque l'utilisateur clique n'importe où sur une ligne du tableau. Cette option est activée par défaut. Définissez-la sur `False` pour rendre les lignes inertes ; les utilisateurs naviguent alors via les actions de ligne. Les lignes ne sont jamais cliquables pour les utilisateurs dont la vérification `can_view_detail` échoue.

#### Édition intégrée

Vous pouvez permettre aux utilisateurs de modifier certains champs directement depuis la vue de liste, sans ouvrir le formulaire complet d'édition.

Utilisez l'attribut `inline_editable_fields` pour déclarer quelles colonnes le prennent en charge. Cliquer sur une cellule activée ouvre alors une fenêtre contextuelle pour une mise à jour rapide.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "Security and access"
    L'édition intégrée est désactivée par défaut. Lorsque vous l'activez, la permission `can_edit` existante de la vue continue de la contrôler.

Pour les détails de configuration, le comportement de validation et la matrice complète des types de champs pris en charge, consultez le guide [Inline Edit](inline-edit.md).

### Données relationnelles

L'admin gère les relations entre données pour vous. Pour la relation plusieurs-à-un entre `Post` et `Author`, ajoutez l'attribut de relation à votre liste `fields`. Tant que les deux modèles disposent de vues enregistrées, l'interface affiche les widgets appropriés.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Déclaration manuelle des relations

Déclarez vous-même les champs `HasOne` ou `HasMany` uniquement lorsque la vue cible est enregistrée sous une `key` personnalisée.

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Représentation des objets

Lorsque l'admin doit afficher un enregistrement sous forme de valeur unique, il utilise la clé primaire par défaut. Un `Post` lié à `Author #3` s'affiche alors comme « 3 » dans les colonnes de relation, ce qui n'apprend presque rien à l'utilisateur. Deux méthodes optionnelles, définies sur le **modèle** plutôt que sur la vue, remplacent ce comportement par défaut par quelque chose de significatif. Toutes deux acceptent la `Request` courante et peuvent être synchrones ou asynchrones.

#### `__admin_repr__`

Renvoie une chaîne simple, utilisée partout où l'enregistrement apparaît sous forme de texte : colonnes de relation dans les pages de liste et de détail, fils d'Ariane et messages de confirmation d'action.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

Avec cette méthode en place, l'auteur d'un article s'affiche comme « Gabriel Garcia Marquez » au lieu de « 3 ».

#### `__admin_select2_repr__`

Renvoie un fragment HTML qui affiche les options dans les menus déroulants `select2` utilisés par les champs de formulaire de relation, ce qui vous permet d'enrichir les choix avec des images, des badges ou du texte secondaire. Sans cette méthode, l'admin utilise la sortie échappée de `__admin_repr__`. Sans aucune des deux méthodes, il utilise un résumé généré des champs non relationnels de l'enregistrement.

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    La valeur renvoyée doit être du HTML valide.

!!! warning
    Échappez les valeurs issues de la base de données pour prévenir les attaques de type cross-site scripting (XSS). Affichez le fragment avec Jinja2 et `autoescape=True`, comme illustré ci-dessus, ou échappez chaque valeur vous-même avec `html.escape`. Pour plus d'informations, consultez la [documentation OWASP](https://owasp.org/www-community/attacks/xss/).

### Sécurité et autorisation {#security-and-authorization}

Restreignez l'accès en surchargeant les méthodes de permission de votre `ModelView`. Chacune renvoie un booléen, et les implémentations de base renvoient toutes `True`.

Ce schéma se branche directement sur votre `AuthProvider`. Dans l'exemple ci-dessous, chaque vérification lit une liste `roles` depuis l'objet `admin_user` de la session :

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

Pour en savoir plus sur la configuration de votre `AuthProvider` et le remplissage de l'objet `admin_user`, consultez [Authentication](auth.md).

!!! note
    Ne surchargez que les méthodes que vous souhaitez restreindre. Celles que vous laissez intactes continuent d'autoriser l'accès.

### Hooks de cycle de vie {#lifecycle-hooks}

Utilisez les hooks de cycle de vie pour exécuter des effets secondaires ou modifier des données juste avant ou après une transaction en base de données.

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

Les hooks disponibles sont `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete` et `after_delete_committed`.

#### Hooks committed

`after_create_committed`, `after_edit_committed` et `after_delete_committed` ne s'exécutent qu'une fois la transaction en base de données validée (commit). Utilisez-les pour les effets secondaires qui ne doivent pas se produire lorsqu'une écriture est annulée (rollback), comme l'envoi d'e-mails ou la mise en file de tâches en arrière-plan :

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    Au moment où ces hooks s'exécutent, la session de la requête a été validée puis fermée. N'écrivez pas en base de données via `request.state.session` à l'intérieur de ceux-ci. Utilisez des E/S externes, ou ouvrez une nouvelle session de base de données.

!!! important
    Dans `after_delete_committed`, `obj` est détaché de toute session. Les attributs chargés avant la suppression restent lisibles, mais la lecture d'un attribut jamais chargé échoue, car la ligne n'existe plus.

!!! note "Backend support"
    Seuls les backends qui diffèrent le commit à la fin de la requête émettent ces hooks. À ce jour, il s'agit du backend SQLAlchemy.

!!! tip
    Pour une logique couvrant plusieurs vues, telle qu'un journal d'audit, utilisez plutôt [Events](../advanced/events.md).

### Personnalisation de l'interface

#### Organisation de la barre latérale {#sidebar-organization}

Regroupez des vues liées dans un dossier repliable avec `DropDown`. Un dossier peut mélanger des entrées `ModelView`, `CustomView` et `Link`.

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### Exportateurs et importateurs

Les attributs `exporters` et `importers` définissent les formats disponibles pour le transfert de données. Consultez le guide [Export & Import](export-import.md) pour connaître les options intégrées et apprendre à écrire les vôtres.

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Actions, formulaires intégrés et templates

`ModelView` propose trois autres ensembles de fonctionnalités pour les cas complexes, chacun disposant de son propre guide :

* **Actions et actions de ligne :** les attributs `actions` et `row_actions` ajoutent des opérations personnalisées par lot et par ligne au-delà du CRUD. Consultez [Actions](actions.md).
* **Formulaires intégrés :** l'attribut `inlines` imbrique les formulaires de création et de modification d'un modèle lié dans la vue parente. Consultez [Inline Forms](inline-forms.md).
* **Templates et assets :** remplacez les pages par défaut par vos propres templates Jinja via `list_template`, `detail_template`, `create_template` ou `edit_template`. Consultez [Templates](../advanced/templates.md).

## CustomView

Toutes les pages d'un admin ne correspondent pas à un modèle de base de données. `CustomView` crée une page autonome dans la barre latérale, construite à partir de widgets, de templates personnalisés ou de routes personnalisées.

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

Consultez [Custom Views](custom-views.md) pour le catalogue complet des widgets, les instructions relatives aux tableaux de bord et les routes personnalisées.

## Link

`Link` ajoute un hyperlien à la barre latérale, dirigeant les utilisateurs vers un site en production, une documentation externe ou un autre outil interne.

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** et **`icon`** : le texte et l'icône de l'entrée dans la barre latérale.
* **`url`** et **`target`** : la destination et l'attribut target de l'ancre.

`admin.add_link(link)` est un simple wrapper autour de `admin.add_view(link)`. Utilisez celui qui se lit le mieux dans votre codebase. Vous pouvez également imbriquer un `Link` dans un `DropDown`, comme montré dans [Organisation de la barre latérale](#sidebar-organization).

---

## Et ensuite ?

* **[Fields](fields.md)** : le catalogue complet des types de champs.
* **[Form Layouts](../advanced/form-layout.md)** : organisez vos formulaires de création et de modification avec des lignes, des panneaux, des fieldsets et des onglets.
* **[Custom Views](custom-views.md)** : construisez des tableaux de bord et des pages autonomes avec des widgets, des templates et des routes personnalisées.
* **[Actions & Row Actions](actions.md)** : ajoutez des opérations par lot et par ligne au-delà du CRUD.
* **[Inline Edit](inline-edit.md)** : permettez aux utilisateurs de modifier un seul champ d'une ligne depuis la page de liste.
* **[Inline Forms](inline-forms.md)** : imbriquez les formulaires de création et de modification d'un modèle lié dans une vue parente.
* **[Templates](../advanced/templates.md)** : remplacez les templates par vos propres templates Jinja et injectez des assets personnalisés.
