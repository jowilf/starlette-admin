---
title: Intégration de Beanie
description: Intégrez Beanie ODM avec starlette-admin pour créer une interface d'administration
  extensible pour vos collections MongoDB dans FastAPI.
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Intégration de Beanie

Beanie modélise les documents MongoDB sous forme de modèles Pydantic asynchrones. Le module `starlette_admin.contrib.beanie` fournit des classes `Admin` et `ModelView` spécialisées, configurées pour interagir directement avec ces documents.

**Fonctionnalités principales :**

- Prise en charge native des opérateurs de requête et du filtrage MongoDB.
- Traduction automatique des erreurs de validation Pydantic en erreurs de formulaire spécifiques à chaque champ.
- Intégration intégrée de la recherche plein texte MongoDB.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## Exemple minimal

Vous devez initialiser Beanie avant que toute requête n'atteigne l'interface d'administration. La meilleure approche pour garantir cette condition préalable consiste à encapsuler la logique de connexion dans le gestionnaire de contexte `lifespan` de votre application principale.

```python
from contextlib import asynccontextmanager

import uvicorn
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView


class Genre(Document):
    name: str
    description: str | None = None

    class Settings:
        name = "genres"


mongo_client = AsyncMongoClient("mongodb://localhost:27017")


@asynccontextmanager
async def lifespan(app: Starlette):
    await init_beanie(
        database=mongo_client.get_database("library"), document_models=[Genre]
    )
    yield


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

La classe `ModelView` accepte directement la classe `Document` de Beanie. Elle dérive automatiquement la liste des champs, les formulaires et les filtres à partir des champs du document.

## Classes principales

### La classe `beanie.Admin`

La classe `beanie.Admin` hérite de `BaseAdmin` et ne nécessite aucune configuration spécifique à la base de données lors de l'initialisation. La configuration de la connexion s'effectue entièrement dans le lifespan de l'application. Importez toujours `Admin` depuis `starlette_admin.contrib.beanie` afin de garantir la compatibilité avec les futures améliorations propres au backend.

### La classe `beanie.ModelView`

La classe `beanie.ModelView` fournit la couche d'intégration entre votre base de données et l'interface utilisateur. Elle gère automatiquement plusieurs opérations :

- **Remplissage des champs :** génère automatiquement les champs à partir de la définition du document si vous ne les spécifiez pas explicitement.
- **Filtrage des champs internes :** exclut par défaut le champ interne `revision_id` de Beanie des listes et des formulaires.
- **Résolution des relations :** exécute les lectures en base de données avec `fetch_links=True` et `nesting_depth=1`, ce qui garantit que les références `Link` sont résolues vers leurs objets associés plutôt que de renvoyer des références brutes de la base de données.
- **Gestion des erreurs :** traduit les erreurs de validation Pydantic en erreurs de formulaire spécifiques à chaque champ, en indiquant directement aux utilisateurs l'entrée incorrecte.

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## Le champ `BeanieObjectIdField`

Beanie utilise `PydanticObjectId` comme clé primaire. Le panneau d'administration représente automatiquement ces clés, ainsi que toute référence brute d'ObjectId, à l'aide d'un champ dédié `BeanieObjectIdField`.

Bien qu'il s'affiche et se valide exactement comme un champ `StringField` standard, il dispose de son propre emplacement dans le registre des filtres. Cette séparation garantit que les filtres spécifiques aux ObjectId ne s'appliquent qu'aux champs ObjectId, plutôt qu'à tous les champs texte standards de votre application. Ces filtres spécialisés analysent sans risque les chaînes de caractères pour les convertir en objets `PydanticObjectId` valides avant d'interroger la base de données.

## Registre des filtres

Chaque type de champ reçoit un ensemble de filtres par défaut provenant du `BeanieFilterRegistry`.

- **Correspondance de chaînes :** le filtre d'égalité utilise des expressions régulières insensibles à la casse afin de rester cohérent avec les autres recherches textuelles telles que « Contient » ou « Commence par ».
- **Opérations sur les tableaux :** le registre fournit une prise en charge intégrée du filtrage basé sur les tableaux, permettant aux opérations « Est l'un de » sur les champs à valeur de liste (comme `TagsField`) de fonctionner immédiatement.
- **Clés primaires :** le champ `id` est automatiquement remappé vers le champ natif `_id` de MongoDB lors de la construction des fragments de requête.

## Recherche plein texte

Lorsque les utilisateurs interagissent avec la zone de recherche sur une page de liste, le panneau d'administration vérifie si la collection MongoDB possède un index de texte existant et adapte sa stratégie de requête en conséquence :

- **Index de texte présent :** la requête utilise l'opérateur natif `$text` de MongoDB. Cela offre de véritables capacités de recherche plein texte, notamment la tokenisation, la racinisation et le classement par pertinence.
- **Aucun index de texte :** le système revient à une recherche par expression régulière insensible à la casse sur tous les champs marqués comme `searchable`. Bien que cela ne nécessite aucune configuration, il est impossible de classer les résultats par pertinence ni d'utiliser les index standards.

Le panneau d'administration détecte les index de texte existants mais ne les crée pas. Vous devez définir l'index sur votre document Beanie pour activer la recherche plein texte native. Par exemple, vous pouvez y parvenir en ajoutant `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]` à votre modèle.

!!! note
Si vous activez un index de texte, vous pouvez définir `full_text_override_order_by = True` sur votre sous-classe de `ModelView` pour trier les résultats de recherche selon le score de pertinence de MongoDB au lieu du tri par colonne par défaut.

## Exemple complet fonctionnel

Cette section fournit une intégration Beanie complète et exécutable avec `starlette-admin`.

### 1. Installer les dépendances

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

Le paquet `fastapi[standard]` inclut la CLI FastAPI, qui vous permet de démarrer le serveur de développement en exécutant `fastapi dev`.

### 2. Créer l'application

Enregistrez le code suivant dans un fichier nommé `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Link, init_beanie
from fastapi import FastAPI
from pydantic import Field
from pymongo import AsyncMongoClient
from starlette_admin import SlugField
from starlette_admin.contrib.beanie import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"
mongo_client = AsyncMongoClient(MONGO_URI)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Document):
    name: str

    async def __admin_repr__(self, request) -> str:
        return self.name

    class Settings:
        name = "authors"


class Post(Document):
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Link[Author]

    async def __admin_repr__(self, request) -> str:
        return self.title

    class Settings:
        name = "posts"


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
    await init_beanie(
        database=mongo_client.get_database("blog"), document_models=[Author, Post]
    )
    yield


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

Accédez à [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) dans votre navigateur pour afficher le tableau de bord d'administration et interagir avec lui.

> **Exemple avancé :** [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) dans le dépôt contient un exemple complet incluant des vues en ligne, des événements et des actions groupées personnalisées.

## Pour aller plus loin

- **[Vues](../user-guide/views.md)** : explorez les options de configuration de `BaseModelView`, indépendamment du backend.
- **[Filtres](../user-guide/filters.md) :** le constructeur de filtres et la manière dont les filtres spécifiques à l'ORM s'intègrent.
- **[MongoEngine](mongoengine.md) :** un autre backend MongoDB intégré à starlette-admin.
- **[SQLAlchemy](sqlalchemy.md) :** le backend relationnel intégré à starlette-admin.
