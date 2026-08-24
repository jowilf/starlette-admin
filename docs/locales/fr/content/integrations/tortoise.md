---
title: Intégration de Tortoise ORM
description: Créez facilement une interface d'administration pour vos modèles Tortoise
  ORM dans FastAPI à l'aide de starlette-admin.
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Intégration de Tortoise ORM

Tortoise ORM est un mappeur objet-relationnel natif asyncio, inspiré par Django. Le module `starlette_admin.contrib.tortoise` fournit des classes spécialisées `Admin`, `ModelView` et `InlineModelView` qui sont préconfigurées pour s'intégrer directement avec vos modèles Tortoise.

**Fonctionnalités clés :**

* **Conversion automatique des champs :** Mappe les champs des modèles Tortoise directement aux composants d'interface. Cela inclut la prise en charge complète des enums, du JSON, des dates et des timestamps automatiques.
* **Mapping des relations :** Convertit les relations de type clé étrangère et one-to-one en champs `HasOne`, et les relations many-to-many en champs `HasMany`. Les relations inverses sont automatiquement affichées en lecture seule.
* **Filtrage avancé :** Exploite les expressions `Q` de Tortoise pour le constructeur de filtres et active une recherche plein texte insensible à la casse sur les champs de type chaîne.
* **Traduction des erreurs :** Mappe les erreurs de validation de Tortoise directement vers des erreurs de formulaire spécifiques à chaque champ dans l'interface.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## Exemple minimal

Tortoise se connecte à la base de données dans le gestionnaire de contexte `lifespan` de votre application. Comme les vues d'administration sont généralement instanciées au moment de l'import (avant l'exécution de `Tortoise.init()`), vous devez résoudre les relations en amont.

Appelez `Tortoise.init_models()` immédiatement après la définition de vos modèles afin de garantir que les relations soient disponibles lors de la construction des vues d'administration.

```python
from contextlib import asynccontextmanager

import uvicorn
from starlette.applications import Starlette
from tortoise import Tortoise, fields
from tortoise.models import Model
from starlette_admin.contrib.tortoise import Admin, ModelView


class Genre(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField(null=True)


# Résolvez les relations au moment de l'import avant la construction des vues d'administration.
Tortoise.init_models(["app"], "models")


@asynccontextmanager
async def lifespan(app: Starlette):
    await Tortoise.init(
        db_url="sqlite://library.sqlite3", modules={"models": ["app"]}
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

La classe `ModelView` accepte directement la classe `Model` de Tortoise et dérive automatiquement la liste des champs, les formulaires et les filtres à partir du schéma du modèle.

## Classes principales

### `tortoise.Admin`

La classe `tortoise.Admin` hérite de `BaseAdmin` et ne nécessite aucune configuration spécifique à la base de données lors de son initialisation. L'établissement de la connexion s'effectue entièrement dans le `lifespan` de l'application. Importez toujours `Admin` depuis `starlette_admin.contrib.tortoise` afin de garantir la compatibilité avec les futures améliorations spécifiques au backend.

### `tortoise.ModelView`

La classe `tortoise.ModelView` constitue la couche d'intégration entre votre base de données et l'interface utilisateur. Elle gère automatiquement les opérations suivantes :

* **Remplissage des champs :** Génère les champs à partir de la définition du modèle si vous ne les spécifiez pas explicitement. Les colonnes brutes des clés sous-tendant les relations to-one (comme `author_id` pour une relation nommée `author`) ainsi que les relations inverses sont omises par défaut.
* **Résolution des relations :** Précharge chaque relation affichée par la vue. Cela garantit que les listes et les pages de détail ne déclenchent jamais de lazy loads.
* **Timestamps automatiques :** Les colonnes utilisant `DatetimeField(auto_now=...)` ou `DatetimeField(auto_now_add=...)` sont affichées en lecture seule et ne sont jamais marquées comme obligatoires.
* **Gestion des erreurs :** Traduit les erreurs de validation de Tortoise (`"<champ> : <détail>"`) en erreurs de formulaire spécifiques à chaque champ, orientant directement l'utilisateur vers la saisie incorrecte.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Les vues inline permettent aux utilisateurs de modifier les lignes liées directement dans le formulaire parent. La clé étrangère est détectée automatiquement lorsque le modèle enfant possède exactement une relation pointant vers le modèle parent. Si plusieurs relations existent, vous devez définir `fk_attr` explicitement, soit par le nom de la relation, soit par sa colonne de clé brute.

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## Gestion des relations

L'intégration mappe les relations de la base de données aux champs d'administration selon le type de champ. Vous devez enregistrer un `ModelView` pour chaque modèle lié afin que les champs relationnels puissent résoudre correctement leurs vues étrangères.

| Type de relation | Configuration Tortoise | Comportement côté admin |
| --- | --- | --- |
| **Directe (To-One)** | `ForeignKeyField`, `OneToOneField` | Convertie en `HasOne`. |
| **Directe (To-Many)** | `ManyToManyField` | Convertie en `HasMany`. |
| **Inverse** | propriétés `related_name` | Affichée en lecture seule. Doit être ajoutée explicitement à `fields` pour être visible. |

**Filtrage et tri sur les relations :**
Les relations to-one proposent les filtres « Is null » et « Is not null » ciblant la colonne de clé brute. Pour exposer une relation dans le constructeur de filtres, ajoutez le nom de la relation à `searchable_fields`. Pour activer le tri sur la colonne de clé brute, ajoutez le nom de la relation à `sortable_fields`.

## Recherche et filtrage

### Registre de filtres {#filter-registry}

Chaque type de champ reçoit un ensemble de filtres par défaut provenant du `TortoiseFilterRegistry`, implémentés à l'aide des expressions `Q` de Tortoise :

* **Correspondance de chaînes :** Les filtres contient, commence/termine par et égalité utilisent des recherches insensibles à la casse (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Enums :** Les valeurs brutes des filtres sont converties en membres d'enum avant la requête, pour les colonnes `CharEnumField` et `IntEnumField`.
* **Colonnes temporelles :** Les colonnes `TimeField` n'offrent que les vérifications de valeur nulle. Cette limitation existe car les paramètres de type time ne peuvent pas être liés de manière portable sur tous les backends de base de données.

### Recherche plein texte

La zone de recherche de la page de liste construit une correspondance insensible à la casse de type `contains` (expressions `Q` combinées par `OR`) sur tous les champs de type chaîne marqués comme recherchables. Vous pouvez personnaliser ce comportement en redéfinissant la méthode `get_search_query()` de votre vue.

## Exemple complet fonctionnel

Cette section fournit une intégration complète et exécutable de Tortoise ORM avec `starlette-admin`.

### 1. Installer les dépendances

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

Le paquet `fastapi[standard]` inclut la CLI de FastAPI, ce qui vous permet de démarrer le serveur de développement en exécutant `fastapi dev`.

### 2. Créer l'application

Enregistrez le code suivant dans un fichier nommé `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from enum import Enum

from fastapi import FastAPI
from starlette_admin import SlugField
from starlette_admin.contrib.tortoise import Admin, ModelView
from tortoise import Tortoise, fields
from tortoise.models import Model

DB_URL = "sqlite://blog.sqlite3"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=100)

    def __admin_repr__(self, request) -> str:
        return self.name


class Post(Model):
    id = fields.IntField(primary_key=True)
    title = fields.CharField(max_length=200)
    slug = fields.CharField(max_length=200, unique=True)
    content = fields.TextField()
    status = fields.CharEnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = fields.DatetimeField(auto_now_add=True)
    author = fields.ForeignKeyField("models.Author", related_name="posts")

    def __admin_repr__(self, request) -> str:
        return self.title


# Résolvez les relations au moment de l'import avant la construction des vues d'administration.
Tortoise.init_models(["main"], "models")


class AuthorView(ModelView):
    fields = ["id", "name"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        "content",
        "status",
        "created_at",
        "author",
    ]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    await Tortoise.init(db_url=DB_URL, modules={"models": ["main"]})
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Comme `created_at` utilise `auto_now_add`, l'interface d'administration l'affiche automatiquement en lecture seule. Aucune configuration `exclude_fields_from_create` ou `exclude_fields_from_edit` n'est nécessaire.

### 3. Lancer le serveur

Démarrez le serveur de développement FastAPI :

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Accédez à [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) dans votre navigateur pour consulter le tableau de bord d'administration et interagir avec lui.

> **Exemple avancé :** [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) dans le dépôt contient un exemple complet incluant des relations, des vues inline, des enums et des champs JSON reposant sur SQLite.

## Pour aller plus loin

* **[Vues](../user-guide/views.md) :** Explorez les options de configuration de `BaseModelView` indépendantes du backend.
* **[Filtres](../user-guide/filters.md) :** Découvrez le constructeur de filtres et comment les filtres spécifiques à un ORM s'y intègrent.
* **[SQLAlchemy](sqlalchemy.md) :** Documentation de l'autre backend relationnel intégré à starlette-admin.
