---
title: Démarrage rapide
description: Créez une interface d'administration CRUD entièrement fonctionnelle pour
  FastAPI et Starlette en quelques minutes grâce à notre guide de démarrage rapide
  complet.
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# Démarrage rapide

Créez une interface d'administration CRUD entièrement fonctionnelle pour un blog en quelques minutes, avec des formulaires, des listes, une recherche, un import et un export générés automatiquement directement à partir de vos modèles de données.

## Installation

Installez les paquets nécessaires à l'aide de votre gestionnaire de paquets préféré :

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    Le paquet `fastapi[standard]` inclut la CLI de FastAPI, qui vous permet de démarrer le serveur de développement en exécutant `fastapi dev`.

## L'exemple complet

Créez un fichier nommé `main.py` et ajoutez-y le code suivant :

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## Exécution de l'application

Démarrez le serveur de développement :

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Ouvrez un navigateur et rendez-vous sur [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

Dans la barre latérale, sélectionnez **Posts**, puis sélectionnez **Create**. Vous avez désormais accès aux pages de liste paginée, de détail, de création, de modification et de suppression. Le système génère automatiquement toutes ces interfaces à partir de la définition de votre modèle.

## Fonctionnement

Les sections suivantes expliquent les composants essentiels de l'application.

### Le modèle

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

Ce code utilise SQLAlchemy 2.0 standard. Le paquet starlette-admin lit les métadonnées de colonnes associées à ces attributs pour déterminer le champ HTML exact à générer. Par exemple, il crée un champ texte pour `str`, une case à cocher pour `bool` et un sélecteur de date et heure pour `datetime`.

### La vue

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` constitue l'objet central pour cette ressource. L'attribut `fields` détermine quelles colonnes apparaissent dans la liste et dans le formulaire, tandis que `searchable_fields` active la barre de recherche. Toutes les configurations relatives à l'apparence et au comportement de `Post` dans le tableau de bord d'administration résident dans cette unique classe.

!!! note
    L'exemple importe `ModelView` depuis `starlette-admin.contrib.sqla` car il s'appuie sur SQLAlchemy. Si vous utilisez un autre backend, tel que Beanie, MongoEngine ou Tortoise ORM, vous devez importer `ModelView` depuis le paquet contrib correspondant. L'API de configuration reste identique pour tous les backends pris en charge.

### L'administration

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

La classe `Admin` relie le moteur de base de données à l'interface utilisateur.

* `add_view` enregistre votre vue dans la barre latérale. Le paramètre facultatif `icon` accepte n'importe quelle classe [Font Awesome](https://fontawesome.com/icons) valide.
* `mount_to` attache l'application d'administration à votre application FastAPI ou Starlette sous le chemin `/admin`.

!!! warning
    Le paramètre `secret_key` signe les cookies contenant les données de session, y compris les messages flash et la protection CSRF. Dans les environnements de production, vous devez remplacer la valeur d'exemple par une chaîne longue, aléatoire et générée de manière sécurisée. N'utilisez jamais une valeur fictive dans un déploiement en production.

## Ajouter un second modèle

Vous pouvez enregistrer un nombre illimité de modèles. Par exemple, pour ajouter un modèle `Tag` ainsi que sa vue correspondante, définissez les classes puis appelez à nouveau `add_view` :

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

Actualisez la fenêtre du navigateur pour voir **Posts** et **Tags** apparaître dans la barre latérale. Chaque ressource dispose désormais de ses propres pages de liste, de création, de modification et de suppression entièrement fonctionnelles.

---

## Prochaines étapes

* **[Concepts](concepts.md) :** Apprenez la terminologie des concepts présentés ici afin de mieux vous repérer dans le guide de l'utilisateur.
* **[Admin](../user-guide/admin.md) :** Découvrez toutes les options de `Admin(...)`, notamment le branding, les thèmes, l'authentification, la sécurité et l'internationalisation.
* **[Views](../user-guide/views.md) :** Explorez l'intégralité des options de configuration de `ModelView` disponibles pour personnaliser la présentation de vos données.
