---
title: Intégration de SQLModel
description: Créez un tableau de bord d'administration complet pour vos applications
  FastAPI SQLModel à l'aide de starlette-admin.
source_hash: 96c8764bbc647c696f3ec02784bf0b7a9b05d3f1b051c40e8783b36bb49e612e
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/integrations/sqlmodel/)
<!-- translation-notice:end -->

# Intégration de SQLModel

[SQLModel](https://sqlmodel.tiangolo.com/) combine les tables SQLAlchemy avec la validation Pydantic dans une seule classe de modèle. Comme les modèles SQLModel sont des modèles SQLAlchemy sous le capot, le module `starlette_admin.contrib.sqlmodel` sert de fine couche d'encapsulation autour du [backend SQLAlchemy](sqlalchemy.md) existant.

Plutôt que d'implémenter un système séparé, cette intégration hérite directement du backend SQLAlchemy principal de toute la détection automatique des champs, de la gestion des clés primaires, du traitement des relations, du filtrage et du middleware de session. Elle introduit une couche de validation robuste qui fait passer les données soumises via le formulaire par les validateurs Pydantic natifs de votre modèle (tels que `Field(min_length=...)` ou des méthodes personnalisées `@field_validator`) avant toute écriture en base de données. Les exceptions `ValidationError` qui en résultent sont automatiquement traduites en erreurs de formulaire par champ dans l'interface utilisateur.

!!! note
    Tout ce qui est documenté sur la [page SQLAlchemy](sqlalchemy.md) s'applique sans modification. Cela inclut les moteurs synchrones et asynchrones, les fournisseurs `sessionmaker`, le cycle de vie de session avec un commit par requête, les champs de relation et le registre des filtres.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## Exemple minimal

```python
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)
    price: float


class ProductView(ModelView):
    fields = ["id", "name", "price"]


SQLModel.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

La classe `ModelView` accepte directement la classe de table SQLModel et dérive automatiquement la liste des champs, les formulaires et les filtres à partir du schéma du modèle.

## Classes principales

### `sqlmodel.Admin`

La classe `sqlmodel.Admin` est la classe `sqla.Admin` réexportée. Elle utilise le même constructeur, acceptant un `Engine`, un `AsyncEngine`, un `sessionmaker` ou un `async_sessionmaker` comme argument obligatoire `session_provider`. Elle insère également le même middleware de session qui alimente `request.state.session` à chaque requête.

### `sqlmodel.ModelView`

La classe `sqlmodel.ModelView` hérite de tout ce que fournit `sqla.ModelView` et ajoute une couche de validation. Sa méthode `validate()` appelle `self.model.model_validate(data)` avant d'écrire l'enregistrement, ce qui garantit que les soumissions de formulaire sont vérifiées par les validateurs Pydantic du modèle au lieu de reposer strictement sur les contraintes de colonnes SQLAlchemy. Les champs de fichier et les champs de relation sont volontairement exclus de cet appel de validation, car ils se situent en dehors de la surface de validation Pydantic du modèle.

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

Les vues intégrées permettent aux utilisateurs de modifier des lignes liées directement dans le formulaire parent. La classe hérite de la détection des clés étrangères et de la gestion de session de la classe `InlineModelView` SQLAlchemy et applique la même validation Pydantic à chaque ligne intégrée.

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Validation Pydantic

Les contraintes déclarées sur le modèle s'appliquent automatiquement aux formulaires de création et de modification :

```python
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr
    created_at: datetime | None = Field(default=None)

    articles: list["Article"] = Relationship(back_populates="author")
```

Une entrée telle qu'un `full_name` de moins de deux caractères ou une adresse e-mail invalide échouera à la validation. Ces échecs sont renvoyés sous forme d'erreurs de formulaire par champ avant qu'une opération `INSERT` ou `UPDATE` n'atteigne la base de données.

!!! note
    Le type `EmailStr` nécessite le paquet `email-validator`, installable via `pip install "pydantic[email]"`.

## Exemple complet fonctionnel

Cette section fournit une intégration SQLModel complète et exécutable avec `starlette-admin`.

### 1. Installer les dépendances

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

Le paquet `fastapi[standard]` inclut la CLI FastAPI, ce qui vous permet de démarrer le serveur de développement en exécutant `fastapi dev`.

### 2. Créer l'application

Enregistrez le code suivant dans un fichier nommé `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import Column, Text, create_engine
from sqlmodel import Field, Relationship, SQLModel
from starlette_admin import SlugField
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)

    posts: list["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3)
    slug: str = Field(unique=True)
    content: str = Field(sa_column=Column(Text))
    status: PostStatus = Field(default=PostStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Author | None = Relationship(back_populates="posts")


class AuthorView(ModelView):
    fields = ["id", "name", "posts"]


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
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Soumettre un `title` de moins de trois caractères ou un `name` de moins de deux caractères entraîne le réaffichage du formulaire avec l'erreur attachée au champ concerné.

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

> **Exemple avancé :** [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) dans le dépôt contient un exemple de CMS complet qui inclut des relations, des vues intégrées, des actions, des filtres, des événements et des exportations.

## Pour aller plus loin

* **[SQLAlchemy](sqlalchemy.md) :** le backend sur lequel repose cette intégration, couvrant les moteurs, les sessions, les transactions et le registre des filtres.
* **[Vues](../user-guide/views.md) :** explorez les options de configuration de `BaseModelView`, indépendamment du backend.
* **[Filtres](../user-guide/filters.md) :** découvrez le générateur de filtres et la manière dont les filtres spécifiques aux ORM s'y intègrent.
