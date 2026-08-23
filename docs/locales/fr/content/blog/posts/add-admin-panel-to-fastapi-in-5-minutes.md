---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

# Ajouter un panneau d'administration à FastAPI en 5 minutes avec starlette-admin

_2026-07-13_

Vous avez livré votre API. Désormais, quelqu'un dans votre équipe doit modifier les données qui se trouvent derrière : corriger une faute de frappe dans un enregistrement, dépublier un article ou vérifier ce qu'un utilisateur a réellement soumis. Les options habituelles sont généralement coûteuses :

| Option                   | L'inconvénient                                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Frontend CRUD personnalisé** | Demande des semaines de temps de développement pour être construit et maintenu.                            |
| **Accès direct à la base de données** | Crée un risque majeur pour la sécurité et l'intégrité des données.                                         |
| **Django Admin / Flask Admin**         | Impose une réécriture du framework ou repose sur du WSGI synchrone, ce qui bloque votre application ASGI asynchrone. |
| **starlette-admin**      | **Se monte instantanément dans votre application, sans aucun code frontend.**                              |

`starlette-admin` fonctionne avec toute application basée sur Starlette, ce qui est exactement le cas de FastAPI.

Ce guide vous conduit d'un fichier vide à un back office fonctionnel en cinq minutes. Vous allez construire des listes paginées, une fonctionnalité de recherche, des colonnes triables, des formulaires de création et de modification validés par vos schémas Pydantic existants, des confirmations de suppression et des exportations CSV, le tout généré directement à partir d'un modèle SQLAlchemy.

Le code complet et exécutable est disponible dans [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Minute 1 : Installez

Vous avez besoin de trois paquets : le framework d'administration, l'ORM et FastAPI lui-même.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic est fourni avec FastAPI, ce qui devient important plus tard : le panneau d'administration peut réutiliser exactement les mêmes schémas que votre API utilise pour la validation.

## Minutes 2 et 3 : L'application complète

Créez `main.py`. Voici l'intégralité de l'application :

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///blog.db", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)

```

Remarquez ce qui est absent. Il n'y a ni templates, ni gestionnaires de routes pour les pages d'administration, ni sérialiseurs, ni configuration de champs. `starlette-admin` lit les métadonnées des colonnes SQLAlchemy et déduit toute l'interface automatiquement : des champs texte limités pour les deux colonnes `String`, une zone de texte pour le contenu `Text` et un sélecteur de date et heure pour `published_at`.

Les trois lignes surlignées constituent vos seuls points d'intégration. `Admin` lie le moteur de base de données, `add_view` enregistre le modèle dans la barre latérale et `mount_to` attache le tout à votre application FastAPI existante sous le chemin `/admin`. Vos routes API restent intactes ; le panneau d'administration fonctionne simplement comme une sous-application montée.

## Minute 4 : Exécutez-la

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Ouvrez [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) et cliquez sur **Post** dans la barre latérale. Dès l'installation, vous obtenez :

- Une vue de liste paginée et triable de tous les articles.
- Des formulaires de création et de modification équipés du widget de saisie approprié pour chaque type de colonne.
- Une page de détail pour chaque enregistrement.
- Des capacités de suppression groupée avec une boîte de dialogue de confirmation.
- Des exportations CSV et Excel pour la liste en cours.

Votre API continue de servir le trafic normalement. Consultez [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) pour vérifier que tout est intact.

## Minute 5 : Donnez-lui une apparence faite main

La vue par défaut fournit une interface CRUD complète, mais un véritable back office mérite d'être adapté : votre ordre de champs, votre disposition de formulaire et votre comportement de recherche. La spécialisation de `ModelView` est là où `starlette-admin` révèle tout son potentiel. Remplacez l'appel à `add_view` par une vue configurée :

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

```

Quatre améliorations puissantes interviennent dans cette seule classe :

- **`SlugField(populate_from="title")`** : génère le slug automatiquement pendant que l'opérateur saisit le titre, sans aucun JavaScript personnalisé de votre part.
- **`ComputedField`** : affiche une valeur qui n'existe pas dans la base de données. Le nombre de mots est calculé via une simple fonction Python au moment du rendu.
- **`form_layout`** : organise le formulaire en lignes logiques : titre et slug côte à côte, contenu sur toute la largeur et date de publication en dessous.
- **`search_auto_submit`** : filtre la liste dynamiquement pendant que l'opérateur saisit du texte, sur toutes les colonnes définies dans `searchable_fields`.

## Rejeter les données invalides : utilisez le schéma que vous avez déjà

Les opérateurs font des erreurs, ce qui signifie que le panneau d'administration doit appliquer vos règles côté serveur. L'avantage, c'est que vous avez déjà écrit ces règles. Chaque projet FastAPI valide ses corps de requête avec des modèles Pydantic ; quelque part dans votre code se trouve donc un schéma semblable à celui-ci :

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v

```

Plutôt que d'écrire deux fois la logique de validation, confiez au panneau d'administration votre modèle existant. L'extension `ext.pydantic` fournit un `ModelView` qui traite chaque soumission de formulaire via un modèle Pydantic avant qu'elle n'atteigne la base de données. Orientez votre import de `ModelView` vers l'extension, conservez `Admin` tel quel et transmettez le schéma :

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

Le corps de `PostView` reste exactement identique ; seule sa classe de base change grâce au nouvel import.

L'intégration est transparente. Chaque contrainte s'applique lors de la création et de la modification : les bornes de longueur, l'expression régulière du slug et le `field_validator` personnalisé. Chaque erreur Pydantic est reliée directement à son champ de formulaire correspondant et s'affiche en ligne, reproduisant parfaitement un formulaire fait main. Veillez à garder `id` optionnel dans le schéma afin que les formulaires de création, qui ne comportent pas d'ID initialement, puissent toujours être validés.

Vous établissez ainsi une source unique de vérité. Lorsque votre schéma API reçoit une nouvelle règle, le panneau d'administration l'applique dès la requête suivante, sans nécessiter aucune modification de code côté administration.

## Une minute de plus ? Donnez un auteur à vos articles

Les données réelles reposent sur des relations, et le panneau d'administration les gère selon la même approche sans configuration. Ajoutez un modèle `User` et liez-le à `Post` :

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

```

Enregistrez le modèle utilisateur en suivant le même principe piloté par le schéma. `EmailStr` et `HttpUrl` fournissent automatiquement la validation de format, et `email-validator` est déjà inclus avec `fastapi[standard]` :

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Comme il n'y a rien à configurer cette fois, le `ModelView` de l'extension est utilisé directement, sans spécialisation.

Enfin, rendez l'auteur obligatoire en ajoutant deux lignes à `PostIn` :

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` n'a pas de valeur par défaut, ce qui signifie qu'un article sans auteur est rejeté comme n'importe quelle autre erreur de validation. Le type est la classe `User` de SQLAlchemy elle-même, car le panneau d'administration résout l'identifiant sélectionné en une instance ORM avant que la validation ne s'exécute. C'est précisément pourquoi `arbitrary_types_allowed` est requis (`ConfigDict` est importé depuis `pydantic`).

Ajoutez ensuite `"user"` à `PostView.fields` et à `form_layout` afin que l'auteur apparaisse dans le formulaire d'article. Ce champ n'est pas un menu déroulant standard. Il s'agit d'une liste de sélection dotée d'une autocomplétion côté serveur qui recherche vos utilisateurs pendant la saisie de l'opérateur, et la page de détail de l'utilisateur renvoie vers chaque article associé.

!!! note
`create_all` ne modifie pas les tables existantes ; vous devrez donc supprimer `blog.db` avant de redémarrer pour prendre en compte la nouvelle colonne `user_id`.

## Avant le déploiement

!!! warning
Le paramètre `secret_key` signe le cookie de session utilisé pour la protection CSRF et les messages flash. Remplacez la valeur provisoire par une valeur longue et aléatoire issue de vos paramètres avant le déploiement, et veillez à la charger depuis vos variables d'environnement plutôt qu'à la coder en dur dans le code source.

!!! note
`Base.metadata.create_all(engine)` dans le lifespan est une commodité pour le démarrage rapide. Dans un projet de production, vos tables sont gérées par des migrations (comme Alembic). Supprimez cet appel et pointez `Admin` directement vers votre moteur existant. `starlette-admin` ne modifie jamais votre schéma ; il se contente de lire et d'écrire des lignes.

## Cette approche passe à l'échelle au-delà de la démonstration

Tout ce qui précède utilise deux modèles, mais ces mêmes mécanismes de `ModelView` peuvent prendre en charge un back office de grande envergure. Vous pouvez facilement mettre en œuvre le téléversement de fichiers et d'images, [l'authentification avec accès basé sur les rôles](../../user-guide/auth.md), [des filtres personnalisés](../../user-guide/filters.md), [des actions de ligne et des actions groupées](../../user-guide/actions.md) et une [i18n](../../user-guide/i18n.md) complète. Chaque fois que le comportement intégré s'avère insuffisant, chaque requête et chaque étape du cycle de vie offre un hook de substitution. C'est exactement ainsi que sont construits des schémas comme [la suppression logique avec une vue corbeille](soft-deletes-trash-view.md).

---

## Prochaines étapes

- **[Concepts](../../getting-started/concepts.md) :** le vocabulaire derrière ce que vous venez de construire, pour que la suite de la documentation se lise aisément.
- **[Vues](../../user-guide/views.md) :** une exploration approfondie de chaque option de `ModelView`, y compris les hooks de permission.
- **[Suppressions logiques et vue corbeille pour FastAPI](soft-deletes-trash-view.md) :** la première recette avancée, construite directement sur les hooks de substitution présentés ici.
