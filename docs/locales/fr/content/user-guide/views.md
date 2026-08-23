---
title: Vues
description: Apprenez à configurer les vues de liste et les pages de détail dans starlette-admin,
  y compris la recherche, le tri et la pagination.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
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

# Vues

`starlette-admin` construit sa barre latérale à partir de trois types de vue : `ModelView` expose un modèle de base de données, `CustomView` affiche une page autonome et `Link` ajoute un lien hypertexte.

## ModelView

Une sous-classe de `ModelView` est le moyen d'exposer un modèle de base de données dans l'admin. Les attributs de classe et les surcharges de méthodes de cette vue définissent son apparence, son comportement et sa gestion des données.

Chaque exemple de cette section utilise la configuration SQLAlchemy suivante :

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

Pour exposer le modèle `Post`, héritez de `ModelView` et configurez ses attributs.

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

Consultez [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) pour un panneau d'administration exécutable construit de la même manière, sur un modèle `Post`.

L'enregistrement d'une vue génère des interfaces paginées, triables et recherchables pour lister, consulter, créer, modifier et supprimer des enregistrements. Vous n'avez aucune route ni aucun template à écrire.

!!! note
    Vous importez `ModelView` depuis le package contrib de votre backend, tel que `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` ou `.tortoise`. **Tous les attributs décrits ci-dessous sont identiques quel que soit le backend**, si bien que vous pouvez remplacer plus tard un modèle SQLAlchemy par un document MongoEngine sans modifier la logique de votre vue.

### Configuration principale

#### Dénomination et routage

Par défaut, l'admin dérive le routage des URL et les libellés de l'interface du nom de classe du modèle. Pour le modèle `Post`, il utilise :

* **Clé :** `post` (URL : `/admin/post/list`)
* **Libellé de menu :** `Posts` (entrée de la barre latérale)
* **Nom d'affichage :** `Post` (boutons de l'interface tels que **New Post**)

Lorsque ces valeurs dérivées sont incorrectes, remplacez-les lors de l'enregistrement ou dans le constructeur.

| Attribut | Description | Exemple de surcharge | Interface ou URL résultante |
| --- | --- | --- | --- |
| **`key`** | Le slug interne et la route URL de base. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | Le nom au pluriel utilisé dans la barre latérale. | `menu_label="Blog Posts"` | **Barre latérale :** Blog Posts |
| **`display_name`** | Le nom au singulier utilisé dans les actions et les formulaires. | `display_name="Article"` | **Boutons :** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Sélection et personnalisation des champs

La liste `fields` définit quels attributs du modèle apparaissent sur la vue de liste, la page de détail et les formulaires. Omettez-la pour exposer tous les attributs du modèle.

Mixez des noms sous forme de chaînes et des instances explicites de `BaseField` pour contrôler les widgets, la validation et les libellés :

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

Des champs appartiennent souvent à la liste ou à la page de détail mais pas à un formulaire de création, comme les horodatages et les statuts gérés par le système. Utilisez les attributs `exclude_fields_from_*` pour masquer un champ sur des surfaces spécifiques :

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Les attributs d'exclusion disponibles se terminent par `_create`, `_edit`, `_list`, `_detail`, `_export` et `_import`.

!!! important
    Pour permettre aux utilisateurs de définir la clé primaire lorsqu'ils créent un enregistrement, ce qui est désactivé par défaut, définissez `show_pk_in_forms = True`.

#### Mise en page du formulaire

Par défaut, `fields` affiche vos formulaires de création et de modification sous forme de liste verticale plate. Pour réorganiser l'interface sans toucher à vos définitions de données, utilisez l'attribut `form_layout`.

**Le raccourci tuple**

Pour une grille simple, vous n'avez pas besoin d'importer de classes de widget. Regroupez les noms de champs dans un tuple pour les afficher côte à côte sur une même ligne.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Widgets de mise en page avancés**

À mesure que vos formulaires grandissent, structurez-les avec des widgets de mise en page. Le raccourci tuple fonctionne à l'intérieur :

* **`PanelWidget` ou `FieldsetWidget` :** regroupez des champs liés sous un titre, ou rendez une section repliable.
* **`TabsWidget` :** séparez des catégories de données distinctes, telles que les informations d'expédition et les métadonnées SEO, qui n'ont pas besoin d'être visibles simultanément.

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

Consultez [Mise en page des formulaires](../advanced/form-layout.md) pour des lignes multi-colonnes avec largeurs explicites, onglets, contenu statique et comportements de contrôle d'accès.

### Fonctionnalités du tableau de données

#### Recherche et tri

Contrôlez la façon dont les utilisateurs trouvent et ordonnent les données avec `searchable_fields` et `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`** : active le constructeur de filtres et la zone de recherche globale. La recherche globale effectue une requête plein texte sur ces champs.
* **`sortable_fields`** : restreint les en-têtes de colonnes sur lesquels les utilisateurs peuvent trier. Une requête de tri portant sur un autre champ, transmise via des paramètres d'URL, est ignorée.
* **`fields_default_sort`** : définit l'état initial du tableau. Passez une simple chaîne pour un tri croissant, un tuple avec `True` pour un tri décroissant, ou un tuple avec `False` pour un tri croissant explicite. Chaînez plusieurs éléments pour un tri multi-colonnes.

#### Pagination et contrôles de l'interface

Ajustez finement la disposition de la page de liste avec ces attributs :

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
* **`show_goto_page`** : ajoute un champ « Aller à la page » pour les grands jeux de données.
* **`search_auto_submit`** : filtre pendant la saisie de l'utilisateur.
* **`show_detail_search`** : ajoute une zone de recherche sur la page de détail pour filtrer en ligne les tables de relations.
* **`row_click_navigate`** : ouvre la page de détail lorsque l'utilisateur sélectionne n'importe où sur une ligne du tableau. C'est activé par défaut. Définissez-le à `False` pour rendre les lignes inertes, afin que les utilisateurs naviguent plutôt via les actions de ligne. Les lignes ne sont jamais cliquables pour les utilisateurs dont la vérification `can_view_detail` échoue.

#### Édition en ligne

Vous pouvez permettre aux utilisateurs de modifier certains champs directement depuis la vue de liste, sans ouvrir le formulaire de modification complet.

Utilisez l'attribut `inline_editable_fields` pour déclarer quelles colonnes prennent en charge cette fonctionnalité. La sélection d'une cellule activée ouvre alors un popover permettant une mise à jour rapide.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "Sécurité et accès"
    L'édition en ligne est désactivée par défaut. Lorsque vous l'activez, la permission `can_edit` existante de la vue continue de la régir.

Pour les détails de configuration, le comportement de validation et la matrice complète des types de champs pris en charge, consultez le guide [Édition en ligne](inline-edit.md).

### Données relationnelles

L'admin gère les relations de données pour vous. Pour la relation plusieurs-à-un entre `Post` et `Author`, ajoutez l'attribut de relation à votre liste `fields`. Tant que les deux modèles ont des vues enregistrées, l'interface affiche les widgets appropriés.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Déclaration manuelle des relations

Déclarez vous-même des champs `HasOne` ou `HasMany` uniquement lorsque la vue cible est enregistrée sous une `key` personnalisée.

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

Lorsque l'admin doit afficher un enregistrement sous forme de valeur unique, il utilise la clé primaire par défaut. Un `Post` lié à `Author #3` s'affiche alors comme « 3 » dans les colonnes de relations, ce qui n'apprend presque rien à l'utilisateur. Deux méthodes facultatives, définies sur le **modèle** plutôt que sur la vue, remplacent ce comportement par défaut par quelque chose de significatif. Toutes deux acceptent la `Request` courante et peuvent être synchrones ou asynchrones.

#### `__admin_repr__`

Renvoie une simple chaîne, utilisée partout où l'enregistrement apparaît sous forme de texte : colonnes de relations sur les pages de liste et de détail, fils d'Ariane et messages de confirmation d'action.

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

Renvoie un fragment HTML qui restitue les options dans les menus déroulants `select2` utilisés par les champs de formulaire de relation, ce qui permet d'enrichir les choix avec des images, des badges ou du texte secondaire. Sans cette méthode, l'admin utilise la sortie échappée de `__admin_repr__`. Sans aucune des deux méthodes, il utilise un résumé généré des champs hors relation de l'enregistrement.

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
    Échappez les valeurs issues de la base de données pour prévenir les attaques par cross-site scripting (XSS). Restituez le fragment avec Jinja2 et `autoescape=True`, comme montré ci-dessus, ou échappez chaque valeur vous-même avec `html.escape`. Pour plus d'informations, consultez la [documentation OWASP](https://owasp.org/www-community/attacks/xss/).

### Sécurité et autorisations

Restreignez l'accès en redéfinissant les méthodes de permission sur votre `ModelView`. Chacune renvoie un booléen, et les implémentations de base renvoient toutes `True`.

Ce modèle se branche directement sur votre `AuthProvider`. Dans l'exemple ci-dessous, chaque vérification lit une liste `roles` depuis l'objet `admin_user` de la session :

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

Pour en savoir plus sur la configuration de votre `AuthProvider` et le remplissage de l'objet `admin_user`, consultez [Authentification](auth.md).

!!! note
    Ne redéfinissez que les méthodes que vous souhaitez restreindre. Celles que vous laissez intactes continuent d'autoriser l'accès.

### Hooks de cycle de vie

Utilisez les hooks de cycle de vie pour exécuter des effets de bord ou muter des données juste avant ou après une transaction de base de données.

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

#### Hooks après commit

`after_create_committed`, `after_edit_committed` et `after_delete_committed` ne s'exécutent qu'après le commit de la transaction de base de données. Utilisez-les pour des effets de bord qui ne doivent pas se produire lorsqu'une écriture est annulée, comme l'envoi d'un e-mail ou la mise en file d'attente de tâches en arrière-plan :

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    Au moment où ces hooks s'exécutent, la session de la requête est déjà validée et fermée. N'écrivez pas dans la base de données via `request.state.session` à l'intérieur. Utilisez des entrées/sorties externes, ou ouvrez une nouvelle session de base de données.

!!! important
    Dans `after_delete_committed`, `obj` est détaché de toute session. Les attributs chargés avant la suppression restent lisibles, mais la lecture d'un attribut jamais chargé échoue, car la ligne n'existe plus.

!!! note "Prise en charge des backends"
    Seuls les backends qui diffèrent le commit jusqu'à la fin de la requête émettent ces hooks. Aujourd'hui, il s'agit du backend SQLAlchemy.

!!! tip
    Pour une logique couvrant plusieurs vues, telle qu'un journal d'audit, utilisez plutôt [Événements](../advanced/events.md).

### Personnalisation de l'interface

#### Organisation de la barre latérale

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

Les attributs `exporters` et `importers` définissent les formats disponibles pour le transfert de données. Consultez le guide [Exportation et importation](export-import.md) pour découvrir les options intégrées et apprendre à écrire les vôtres.

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Actions, formulaires intégrés et templates

`ModelView` offre trois autres ensembles de fonctionnalités pour les cas complexes, chacun doté de son propre guide :

* **Actions et actions de ligne :** les attributs `actions` et `row_actions` ajoutent des opérations groupées et par ligne personnalisées au-delà du CRUD. Consultez [Actions](actions.md).
* **Formulaires intégrés :** l'attribut `inlines` imbrique les formulaires de création et de modification d'un modèle lié dans la vue parente. Consultez [Formulaires intégrés](inline-forms.md).
* **Templates et assets :** remplacez les pages par défaut par vos propres templates Jinja via `list_template`, `detail_template`, `create_template` ou `edit_template`. Consultez [Templates](../advanced/templates.md).

## CustomView

Toutes les pages d'administration ne correspondent pas à un modèle de base de données. `CustomView` crée une page autonome dans la barre latérale, construite à partir de widgets, de templates personnalisés ou de routes personnalisées.

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

Consultez [Vues personnalisées](custom-views.md) pour le catalogue complet de widgets, les instructions relatives aux tableaux de bord et les routes personnalisées.

## Link

`Link` ajoute un lien hypertexte à la barre latérale, pointant vers un site en ligne, une documentation externe ou un autre outil interne.

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

* **`label`** et **`icon`** : le texte et l'icône de l'entrée de la barre latérale.
* **`url`** et **`target`** : la destination et l'attribut `target` du lien.

`admin.add_link(link)` est une simple enveloppe autour de `admin.add_view(link)`. Utilisez celle qui se lit le mieux dans votre base de code. Vous pouvez aussi imbriquer un `Link` dans un `DropDown`, comme montré dans [Organisation de la barre latérale](#sidebar-organization).

---

## Pour aller plus loin

* **[Champs](fields.md)** : le catalogue complet des types de champs.
* **[Mise en page des formulaires](../advanced/form-layout.md)** : organisez les formulaires de création et de modification avec des lignes, des panneaux, des groupes de champs et des onglets.
* **[Vues personnalisées](custom-views.md)** : construisez des tableaux de bord et des pages autonomes avec des widgets, des templates et des routes personnalisées.
* **[Actions et actions de ligne](actions.md)** : ajoutez des opérations groupées et par ligne au-delà du CRUD.
* **[Édition en ligne](inline-edit.md)** : permettez aux utilisateurs de modifier un champ unique d'une ligne depuis la page de liste.
* **[Formulaires intégrés](inline-forms.md)** : imbriquez les formulaires de création et de modification d'un modèle lié dans une vue parente.
* **[Templates](../advanced/templates.md)** : utilisez vos propres templates Jinja et injectez des assets personnalisés.
