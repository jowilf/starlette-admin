---
title: Intégration de MongoEngine
description: Apprenez à connecter des modèles MongoEngine avec starlette-admin pour
  gérer vos données MongoDB via un panneau d'administration.
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
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

# Intégration de MongoEngine

MongoEngine modélise les documents MongoDB sous forme de classes Python synchrones en utilisant une API de champs de style Django. Le module `starlette_admin.contrib.mongoengine` fournit des classes `Admin` et `ModelView` spécialisées qui construisent directement des vues d'administration à partir de vos définitions `mongoengine.Document`.

**Fonctionnalités principales :**

* Conversion automatique des types de champs, des relations et des documents intégrés.
* Prise en charge prête à l'emploi des téléversements `FileField` et `ImageField` basés sur GridFS.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## Exemple minimal

Vous devez établir la connexion MongoDB avant que toute requête n'atteigne l'interface d'administration. La meilleure approche pour garantir cette condition préalable consiste à encapsuler la logique de connexion dans le gestionnaire de contexte `lifespan` de votre application principale.

```python
from contextlib import asynccontextmanager

import mongoengine as me
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)

    meta = {"collection": "categories"}


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db="podcast_admin", host="mongodb://localhost:27017")
    yield
    me.disconnect()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Podcast Admin", secret_key="change-me-in-production")
admin.add_view(ModelView(Category, icon="fa fa-tags"))
admin.mount_to(app)
```

Le `ModelView` accepte directement la classe `mongoengine.Document`. Il dérive automatiquement la liste des champs, les formulaires et les filtres à partir des champs du document.

## Classes principales : Admin et ModelView

### La classe `mongoengine.Admin`

La classe `mongoengine.Admin` étend la classe `Admin` de base en ajoutant une route spécialisée : `/api/file/{db}/{col}/{pk}`. Cette route renvoie un fichier GridFS directement au navigateur.

Comme chaque téléversement via un champ `FileField` ou `ImageField` sur un modèle MongoEngine est stocké dans GridFS, cette route est nécessaire pour servir ces fichiers. Utilisez toujours `mongoengine.Admin` plutôt que la classe `Admin` de base.

### La classe `mongoengine.ModelView`

Contrairement à la classe de base, le constructeur du `mongoengine.ModelView` prend un argument positionnel `document` au lieu d'une classe de modèle déclarative :

```python
def __init__(
    self,
    document: type[me.Document],
    icon: str | None = None,
    display_name: str | None = None,
    menu_label: str | None = None,
    key: str | None = None,
    converter: BaseMongoEngineModelConverter | None = None,
):

```

Si vous ne définissez pas l'attribut `fields` sur votre sous-classe de `ModelView`, il inclut par défaut tous les champs du document dans leur ordre de déclaration.

Les attributs tels que `key`, `menu_label` et `display_name` suivent un ordre de repli strict :

1. L'argument du constructeur.
2. Un attribut défini au niveau de la classe sur la sous-classe.
3. Une valeur dérivée du nom de classe du document (`key` devient le nom slugifié, `menu_label` devient le nom embelli et mis au pluriel, et `display_name` devient le nom embelli au singulier).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Registre des filtres

Chaque type de champ inclut un ensemble fixe de filtres fourni par le `MongoEngineFilterRegistry`. Vous pouvez remplacer ces valeurs par défaut pour chaque champ à l'aide de l'argument `filters=[...]`.

| Type de champ | Filtres disponibles |
| --- | --- |
| `StringField` | contains, not contains, starts with, ends with, equals, not equals, is null, is not null |
| `TextAreaField` | contains, not contains, starts with, ends with, is null, is not null |
| `EnumField` | equals, not equals, in, not in, is null, is not null |
| `NumberField` | equals, not equals, greater than, less than, between, is null, is not null |
| `FloatField` | equals, not equals, greater than, less than, between, is null, is not null |
| `DateField` | equals, between, in the past, in the future, is null, is not null |
| `DateTimeField` | equals, between, in the past, in the future, is null, is not null |
| `BooleanField` | is true, is false, is null, is not null |
| `TagsField` | in, not in, is null, is not null |
| `RelationField` | is null, is not null |
| `ObjectIdField` | equals, not equals, in, not in, is null, is not null |

!!! note
    Le champ `ObjectIdField` représente l'identifiant `id` du document.

Sous le capot, la méthode `apply()` de chaque filtre renvoie un fragment `Q` de MongoEngine correspondant à sa condition spécifique. Les arbres imbriqués de `FilterGroup` combinent ensuite ces fragments à l'aide d'opérateurs bit à bit (`&` ou `|`) avant d'exécuter la requête. Pour plus de détails, consultez la documentation sur les [filtres](../user-guide/filters.md).

## Documents intégrés

Le champ `EmbeddedDocumentField` de MongoEngine est converti en un champ `CollectionField`. Ce processus convertit récursivement chaque champ du document intégré en son propre sous-champ :

```python
import mongoengine as me
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Address(me.EmbeddedDocument):
    street = me.StringField()
    city = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    address = me.EmbeddedDocumentField(Address)
    comments = me.EmbeddedDocumentListField(Comment)


class PostView(ModelView):
    fields = ["id", "name", "address", "comments"]


admin = Admin()
admin.add_view(PostView(Post))
```

Dans cet exemple :

* Le champ `address` s'affiche sous forme de sous-formulaire imbriqué lors de la création et de la modification, et sous forme de bloc imbriqué sur la page de détail.
* Le champ `comments` (un champ `EmbeddedDocumentListField`) est converti en un champ `ListField` de champs `CollectionField`. Il s'affiche sous forme de groupe répétable de sous-formulaires, avec un affichage par entrée de liste.

## Exemple complet fonctionnel

Cette section fournit une intégration MongoEngine complète et exécutable avec `starlette-admin`.

### 1. Installer les dépendances

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

Le paquet `fastapi[standard]` inclut la CLI FastAPI, ce qui vous permet de démarrer le serveur de développement en exécutant `fastapi dev`.

### 2. Créer l'application

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

import mongoengine as me
from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin import SlugField
from starlette_admin.contrib.mongoengine import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(me.Document):
    name = me.StringField(required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    meta = {"collection": "authors"}


class Post(me.Document):
    title = me.StringField(required=True)
    slug = me.StringField(required=True, unique=True)
    content = me.StringField(required=True)
    status = me.EnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = me.DateTimeField(default=lambda: datetime.now(timezone.utc))
    author = me.ReferenceField(Author, required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.title

    meta = {"collection": "posts"}


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
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    me.connect(db="blog", host=MONGO_URI)
    yield
    me.disconnect()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

### 3. Démarrer le serveur

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

> **Exemple avancé :** [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) dans le dépôt contient une application complète. Elle comprend des vues inline, des événements, des actions de ligne et groupées personnalisées, ainsi que des téléversements d'images et de fichiers GridFS.

---

## Pour aller plus loin

* **[Vues](../user-guide/views.md)** : explorez les options de configuration de `BaseModelView`, indépendantes du backend.
* **[Champs](../user-guide/fields.md) :** guide détaillé de chaque type de champ et de ses attributs, y compris le champ `CollectionField`.
* **[Filtres](../user-guide/filters.md) :** explorez l'interface du constructeur de filtres et apprenez à écrire un filtre personnalisé.
* **[Beanie](beanie.md) :** découvrez l'alternative asynchrone basée sur Pydantic pour MongoDB.
