---
title: Intégration de SQLAlchemy
description: Apprenez à intégrer starlette-admin avec SQLAlchemy. Créez un tableau
  de bord d'administration pour vos modèles de base de données relationnelle dans
  FastAPI.
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

Le backend SQLAlchemy sert d'implémentation de référence pour `BaseModelView`. Il n'a été testé que sur les modèles `DeclarativeBase` de SQLAlchemy 2. Les autres backends (tels que Beanie, MongoEngine, Tortoise ORM ou votre propre implémentation) remplissent ce même contrat auprès de leurs magasins de données respectifs.

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]


class ProductView(ModelView):
    fields = ["id", "name", "price"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

## Installation

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2
    ```

Remplacez `aiosqlite` par `asyncpg` (PostgreSQL) ou `aiomysql`/`asyncmy` (MySQL) si vous préférez ne pas utiliser SQLite. Le pilote de base de données n'est pertinent que pour les moteurs asynchrones. Un moteur synchrone utilise le pilote DBAPI standard requis par le SQLAlchemy classique (comme `psycopg2` ou `pymysql`) et ne nécessite aucun paquet supplémentaire de la part de `starlette-admin`.

## Moteurs asynchrones et synchrones

`Admin` accepte aussi bien un `Engine` qu'un `AsyncEngine`. Passez l'instance que vous avez configurée :

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` inspecte le moteur une seule fois au moment de la requête et ouvre le type de session correspondant : une `AsyncSession` pour un `AsyncEngine` ou une simple `Session` pour un `Engine` synchrone. En interne, `ModelView` effectue une branche sur `isinstance(session, AsyncSession)`. Pour les sessions synchrones, il achemine l'appel bloquant via `anyio.to_thread.run_sync` afin d'éviter de bloquer la boucle d'événements.

## Passer un `sessionmaker` plutôt qu'un moteur

Le paramètre `session_provider` accepte également un `sessionmaker` ou un `async_sessionmaker`. Fournissez un générateur de sessions plutôt qu'un moteur seul lorsque vous devez configurer directement la session.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
Le middleware de session invoque `session_maker()` pour générer une nouvelle session à chaque requête plutôt que d'en construire une en interne.

## `sqla.Admin` et `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` accepte les mêmes arguments que `starlette_admin.BaseAdmin`, plus un argument positionnel obligatoire : `session_provider`. Ce fournisseur peut être un `Engine`, un `AsyncEngine`, un `sessionmaker` ou un `async_sessionmaker`. Lors de l'initialisation, le panneau d'administration configure un middleware de session lié au fournisseur choisi et l'insère au début de la pile des middlewares. Ce mécanisme garantit que `request.state.session` est renseigné automatiquement à chaque requête avant l'exécution du code de votre vue.

`sqla.ModelView` requiert un modèle SQLAlchemy. À l'initialisation, il inspecte le modèle pour détecter automatiquement les champs, gérer les clés primaires et configurer le registre de filtres directement à partir des métadonnées.

## Déclaration des modèles

Définissez vos modèles à l'aide des classes déclaratives standard de SQLAlchemy :

```python
from datetime import datetime
from enum import Enum

from sqlalchemy import Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus]
    views: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
```

Si vous ne définissez pas `fields` sur la vue, `ModelView` utilise chaque attribut déclaré sur le modèle dans leur ordre d'apparition. La clé primaire est détectée automatiquement et exclue des formulaires de création et de modification. Chaque autre colonne et relation est convertie en un type de champ approprié (comme `IntegerField`, `StringField`, `EnumField`, `HasOne` ou `HasMany`) automatiquement.

## Valeurs par défaut détectées automatiquement

La configuration Python `default=` d'une colonne est renseignée automatiquement la première fois que vous ouvrez le formulaire de création. Vous n'êtes pas obligé de répéter cette définition sur le champ lui-même :

```python
from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    views: Mapped[int] = mapped_column(default=0)  # form shows 0
    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )  # form shows now()
```

Une valeur par défaut scalaire (`default=0`) est copiée exactement telle quelle. Une valeur par défaut appelable (`default=datetime.utcnow` ou `default=uuid.uuid4`) est déclenchée une fois lors du rendu du formulaire, ce qui permet au lecteur de voir une valeur réelle plutôt que le format `repr` de la fonction.

!!! important
    Les colonnes de clé primaire ne reçoivent jamais de valeur par défaut pré-remplie, même si une valeur est définie. Elles sont supposées être générées côté serveur (via `autoincrement` ou une séquence) et sont entièrement exclues des formulaires de création et de modification. Les valeurs par défaut sous forme d'expressions SQL (telles que `server_default=func.now()` ou un `DEFAULT` côté base de données) sont également ignorées, car il n'existe aucune valeur au niveau Python à afficher. La base de données se charge de renseigner ces valeurs lors de l'insertion.

## Champs de relation

Une `relationship()` SQLAlchemy sur le modèle est convertie automatiquement en `HasOne` (plusieurs-à-un ou un-à-un) ou en `HasMany` (un-à-plusieurs ou plusieurs-à-plusieurs) selon l'attribut `RelationshipProperty.direction`. Vous n'avez pas besoin de déclarer explicitement le type de champ :

```python
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]

    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")
```

En définissant `PostView.fields = ["id", "title", "author"]`, `author` est rendu comme un menu déroulant Select2. Ce menu déroulant est alimenté via AJAX depuis l'endpoint `/_api/{key}/relation-lookup` de la vue associée (où `{key}` représente `author`, la clé de `AuthorView`). L'application ne charge jamais l'intégralité de la table des auteurs dans la page d'un coup. Ce comportement de chargement différé est essentiel pour la performance lorsque la table associée contient des milliers de lignes. De même, en définissant `AuthorView.fields = ["id", "name", "posts"]`, `posts` est rendu comme un contrôle multi-sélection utilisant le même endpoint de recherche.

## Clés primaires composites

Les modèles utilisant plusieurs colonnes `primary_key=True` pour former des clés primaires composites sont pris en charge sans aucune configuration supplémentaire. Cela inclut les scénarios où chaque colonne de clé primaire sert également de clé étrangère, comme dans un objet d'association plusieurs-à-plusieurs.

Veuillez consulter [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks) pour un exemple entièrement exécutable.

## Registre de filtres

Chaque type de champ reçoit un ensemble de filtres par défaut provenant de `SqlaFilterRegistry`. Ces filtres sont résolus en parcourant la hiérarchie de classes du champ, comme détaillé dans la documentation [Filtres](../user-guide/filters.md). Un détail crucial propre à SQLAlchemy concerne la manière dont chaque filtre se traduit en fragment de requête. Chaque méthode `apply()` de ce module renvoie une clause booléenne SQLAlchemy autonome (telle que `column == value` ou `column.between(a, b)`).

!!! note
    Le filtre `Is null` appliqué à une relation évalue `~column.has()` (pour les relations plusieurs-à-un) ou `~column.any()` (pour les relations un-à-plusieurs et plusieurs-à-plusieurs) au lieu de `column.is_(None)`. Comme un attribut de relation n'est pas une colonne standard contenant une valeur `NULL`, sa nullité dépend entièrement de l'existence ou non de lignes associées.

!!! note
    Le backend SQLAlchemy ne fournit pas `ArrayInFilter` ni `ArrayNotInFilter` (les filtres « is one of » pour les colonnes à valeurs de liste), contrairement à Beanie et MongoEngine. Vous devez écrire votre propre logique `apply()` si vous avez besoin d'un filtrage « is one of » sur une colonne JSON ou ARRAY adossée à un `TagsField`. Consultez la documentation [Filtres personnalisés](../advanced/custom-filters.md) pour plus de détails.

## Sessions et transactions

Le middleware de session ouvre exactement une session par requête et la stocke de manière sécurisée sur `request.state.session`. Cet objet sera une `AsyncSession` lorsque vous utilisez un moteur asynchrone (ou un `async_sessionmaker`), et une `Session` standard sinon. Chaque composant touché par la requête partage cette unique session. La requête de liste, les recherches de relations dans les formulaires et toute logique personnalisée exécutée dans un hook, une action ou un endpoint opèrent tous dans exactement la même transaction. Vous la récupérez de manière uniforme, quel que soit le type de moteur sous-jacent :

```python
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request
from starlette_admin import action
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    @action(name="publish", text="Publish selected")
    async def publish(self, request: Request, pks: list[Any]) -> str:
        session: AsyncSession = request.state.session
        for post in await self.find_by_pks(request, pks):
            post.status = "PUBLISHED"
            session.add(post)
        await session.flush()
        return f"{len(pks)} post(s) published."
```

Lorsque vous utilisez un moteur synchrone, `request.state.session` correspond à une `Session` standard et `session.flush()` est appelé sans `await`. Le reste de l'extrait de code précédent reste identique. Vous n'avez pas besoin d'importer une dépendance `get_session()` distincte. La session est attachée à la requête avant l'exécution de votre hook ou de votre action, car le middleware de session établit la connexion avant d'invoquer le gestionnaire de route.

**Un commit par requête.** Vous ne devez jamais invoquer `session.commit()` manuellement. Appeler `flush()` (ou ne rien faire si vous effectuez des requêtes en lecture seule) suffit. Le middleware de session valide la session exactement une fois après le retour du gestionnaire de route, à condition que la réponse indique un succès. Si une erreur survient, le middleware annule automatiquement l'intégralité de la transaction :

* Si le gestionnaire lève une exception, la session est annulée et l'application relève l'exception.
* Si le gestionnaire renvoie une réponse avec un `status_code >= 400` (par exemple un échec de validation de formulaire), la session est annulée et le serveur renvoie la réponse inchangée. Cette annulation est cruciale car la transaction peut contenir à ce stade un flush ayant échoué. La valider pourrait persister involontairement un enregistrement partiellement écrit.
* Si l'opération de commit elle-même lève une exception (telle qu'une violation de contrainte de base de données détectée au moment du flush), la session est annulée et l'exception est relevée.

Dans tous les autres scénarios où le gestionnaire produit une réponse 2xx ou 3xx, le middleware valide la session et libère la connexion. Ce cycle de vie explique pourquoi l'action `publish` démontrée ci-dessus ne nécessite aucune instruction explicite de commit ou de fermeture. Le middleware de session ouvre la session avant l'exécution de votre code, puis prend en charge les opérations de commit ou d'annulation avant que la réponse ne quitte la vue.

## Validation Pydantic

Vous pouvez utiliser des modèles SQLAlchemy classiques tout en souhaitant valider les données du formulaire contre un schéma Pydantic avant l'enregistrement. Dans ce cas, `starlette_admin.contrib.sqla.ext.pydantic.ModelView` accepte un argument `pydantic_model` pour exécuter la validation contre ce schéma plutôt que contre les types de colonnes SQLAlchemy sous-jacents :

```python
from sqlalchemy import ForeignKey, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel, EmailStr, Field, HttpUrl, field_validator
from starlette_admin.contrib.sqla import Admin
from starlette_admin.contrib.sqla.ext.pydantic import ModelView

engine = create_engine(
    "sqlite:///users.sqlite", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.strip().split()) < 2:
            raise ValueError("Must include both first and last name (e.g. John Doe)")
        return v


admin = Admin(engine, title="Users Admin", secret_key="change-me")
admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))
```

Soumettre `full_name="Madonna"` (un seul mot) fait échouer la méthode `validate_full_name`. Le formulaire de création ou de modification est alors re-rendu avec l'erreur explicitement attachée au champ `full_name`. La colonne SQLAlchemy sous-jacente `String(100)` n'a pas une telle règle. La contrainte réside entièrement dans le modèle Pydantic `UserIn`. Reportez-vous à [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi) pour l'exemple complet, qui inclut également une vue secondaire (`PostIn`) attachée au même panneau d'administration.

## Exemple complet fonctionnel


Voici un exemple complet avec SQLAlchemy et starlette-admin. Consultez [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) pour la version exécutable.

### 1. Installer les dépendances

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

Le paquet `fastapi[standard]` inclut la CLI FastAPI, ce qui vous permet de démarrer le serveur de développement en exécutant `fastapi dev`.

### 2. Créer l'application

Enregistrez le code suivant dans un fichier `main.py`. Ce script utilise une base de données SQLite locale (`blog.db`) à des fins de démonstration, mais Starlette-Admin prend en charge aussi bien les moteurs synchrones qu'asynchrones pour PostgreSQL, MySQL et SQLite.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import ForeignKey, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from starlette_admin import SlugField
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class Base(DeclarativeBase):
    pass


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Base):
    __tablename__ = "authors"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    posts: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    slug: Mapped[str]
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[PostStatus] = mapped_column(default=PostStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )

    author_id: Mapped[int] = mapped_column(ForeignKey("authors.id"))
    author: Mapped["Author"] = relationship(back_populates="posts")


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
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
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

Vous pouvez maintenant accéder à [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) dans votre navigateur pour visualiser le tableau de bord d'administration et interagir avec lui.

---

## Pour aller plus loin

* **[Vues](../user-guide/views.md)** : explorez les options de configuration de `BaseModelView` indépendamment du backend.
* [Filtres](../user-guide/filters.md) : détails sur le constructeur de filtres et le format d'URL propulsé par le registre de filtres.
* [Vues](../user-guide/views.md) : une liste exhaustive de toutes les options de configuration de `ModelView` (indépendantes du backend).
* [SQLModel](sqlmodel.md) : une fine couche d'abstraction autour de ce backend qui ajoute la validation Pydantic aux formulaires.
* [Beanie](beanie.md) : un guide pour utiliser la même API `ModelView` sur une base de données MongoDB.
* [Tortoise ORM](tortoise.md) : l'autre backend relationnel intégré à starlette-admin.
