---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# Ajouter un panneau d'administration à FastAPI en 5 minutes avec starlette-admin

_2026-07-13_

Vous avez livré l'API. Maintenant, quelqu'un dans votre équipe doit modifier les données qui se trouvent derrière : corriger une coquille dans un enregistrement, dépublier un article, ou vérifier ce qu'un utilisateur a réellement soumis. Les options habituelles sont généralement coûteuses :

| Option                   | L'inconvénient                                                                                             |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Frontend CRUD personnalisé** | Demande des semaines de temps de développement pour être construit et maintenu.                            |
| **Accès direct à la base de données** | Crée un risque majeur en matière de sécurité et d'intégrité des données.                                   |
| **Django Admin / Flask Admin**         | Impose une réécriture du framework ou repose sur WSGI synchrone, ce qui bloque votre application ASGI asynchrone. |
| **starlette-admin**      | **Se monte sur votre application instantanément, sans aucun code frontend.**                               |

`starlette-admin` fonctionne avec toute application basée sur Starlette, ce qui est précisément le cas de FastAPI.

Ce guide vous conduit d'un fichier vide à un back office fonctionnel en cinq minutes. Vous allez construire des listes paginées, une fonctionnalité de recherche, des colonnes triables, des formulaires de création et d'édition validés par vos schémas Pydantic existants, des confirmations de suppression et des exports CSV, le tout généré directement à partir d'un modèle SQLAlchemy.

Le code complet et exécutable est disponible dans [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Minute 1 : Installation

Vous avez besoin de trois paquets : le framework d'administration, l'ORM et FastAPI lui-même.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic est fourni avec FastAPI, ce qui deviendra important par la suite : le panneau d'administration peut réutiliser exactement les mêmes schémas que ceux que votre API utilise pour la validation.

## Minutes 2 et 3 : l'application complète

Créez `main.py`. Voici l'application dans son intégralité :

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

Remarquez ce qui est absent. Il n'y a aucun template, aucun gestionnaire de routes pour les pages d'administration, aucun sérialiseur ni aucune configuration de champs. `starlette-admin` lit les métadonnées des colonnes SQLAlchemy et dérive toute l'interface automatiquement : des champs texte bornés pour les deux colonnes `String`, une zone de texte pour le contenu `Text`, et un sélecteur de date et heure pour `published_at`.

Les trois lignes surlignées constituent vos seuls points d'intégration. `Admin` lie le moteur de base de données, `add_view` enregistre le modèle dans la barre latérale, et `mount_to` attache le tout à votre application FastAPI existante sous le chemin `/admin`. Vos routes d'API restent intactes ; le panneau d'administration fonctionne simplement comme une sous-application montée.

## Minute 4 : Exécuter le tout

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
- Des formulaires de création et d'édition équipés du widget de saisie approprié pour chaque type de colonne.
- Une page de vue détaillée pour chaque enregistrement.
- Des capacités de suppression par lot avec boîte de dialogue de confirmation.
- Des exports CSV et Excel pour la liste courante.

Votre API continue de servir le trafic normalement. Vérifiez [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) pour vous assurer que tout est intact.

## Minute 5 : Donner l'impression d'un développement sur mesure

La vue par défaut offre une interface CRUD complète, mais un véritable back office mérite d'être personnalisé : votre ordre de champs, votre disposition de formulaire et votre comportement de recherche. Le fait de dériver de `ModelView` est là où `starlette-admin` révèle tout son potentiel. Remplacez l'appel à `add_view` par une vue configurée :

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

- **`SlugField(populate_from="title")`** : génère le slug automatiquement pendant que l'opérateur saisit le titre, sans nécessiter la moindre ligne de JavaScript personnalisé de votre part.
- **`ComputedField`** : affiche une valeur qui n'existe pas dans la base de données. Le nombre de mots est calculé au moment du rendu via une simple fonction Python.
- **`form_layout`** : organise le formulaire en rangées logiques : titre et slug côte à côte, contenu sur toute la largeur, et date de publication en dessous.
- **`search_auto_submit`** : filtre la liste dynamiquement pendant que l'opérateur saisit du texte, sur toutes les colonnes définies dans `searchable_fields`.

## Rejeter les données invalides : utilisez le schéma que vous possédez déjà

Les opérateurs font des erreurs, ce qui signifie que le panneau d'administration doit appliquer vos règles côté serveur. L'avantage, c'est que vous les avez déjà écrites. Chaque projet FastAPI valide ses corps de requêtes avec des modèles Pydantic ; il existe donc quelque part dans votre codebase un schéma qui ressemble à ceci :

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

Plutôt que d'écrire la logique de validation deux fois, confiez au panneau d'administration votre modèle existant. L'extension `ext.pydantic` fournit un `ModelView` qui traite chaque soumission de formulaire à travers un modèle Pydantic avant qu'elle n'atteigne la base de données. Orientez votre import de `ModelView` vers l'extension, conservez `Admin` tel quel, et passez le schéma :

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

Le corps de `PostView` reste strictement identique ; seule sa classe de base change grâce au nouvel import.

L'intégration est transparente. Chaque contrainte s'applique lors de la création comme de l'édition : les bornes de longueur, l'expression régulière du slug et le `field_validator` personnalisé. Chaque erreur Pydantic est renvoyée directement vers son champ de formulaire correspondant et s'affiche en incrustation, reproduisant fidèlement le comportement d'un formulaire développé à la main. Veillez à garder `id` optionnel dans le schéma afin que les formulaires de création, qui n'ont pas d'ID initialement, puissent continuer à être validés.

Vous établissez ainsi une source unique de vérité. Lorsque votre schéma d'API reçoit une nouvelle règle, le panneau d'administration l'applique dès la requête suivante, sans nécessiter aucune modification de code côté administration.

## Une minute à perdre ? Ajoutez un auteur aux articles

Les données réelles reposent sur des relations, et le panneau d'administration les gère selon la même approche sans configuration. Ajoutez un modèle `User` et reliez-le à `Post` :

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

Enregistrez le modèle utilisateur en suivant le même schéma piloté par validation. `EmailStr` et `HttpUrl` fournissent automatiquement la validation de format, et `email-validator` est déjà inclus avec `fastapi[standard]` :

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Comme il n'y a rien à configurer cette fois-ci, l'extension `ModelView` est utilisée directement, sans dérivation.

Enfin, rendez l'auteur obligatoire en ajoutant deux lignes à `PostIn` :

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

`user: User` ne possède pas de valeur par défaut, ce qui signifie qu'un article sans auteur est rejeté comme n'importe quelle autre erreur de validation. Le type est la classe SQLAlchemy `User` elle-même car le panneau d'administration résout l'ID sélectionné en une instance ORM avant que la validation ne s'exécute. C'est précisément pourquoi `arbitrary_types_allowed` est requis (`ConfigDict` est importé depuis `pydantic`).

Ajoutez ensuite `"user"` à `PostView.fields` ainsi qu'à `form_layout` afin que l'auteur apparaisse dans le formulaire d'article. Ce champ n'est pas une simple liste déroulante standard. Il s'agit d'un champ de sélection doté d'une autocomplétion côté serveur qui recherche vos utilisateurs pendant la saisie, et la page de détail de chaque utilisateur renvoie vers tous ses articles associés.

!!! note
`create_all` ne modifie pas les tables existantes : vous devrez donc supprimer `blog.db` avant de redémarrer pour prendre en compte la nouvelle colonne `user_id`.

## Avant de déployer

!!! warning
Le paramètre `secret_key` signe le cookie de session utilisé pour la protection CSRF et les messages flash. Remplacez la valeur provisoire par une longue valeur aléatoire issue de vos paramètres avant le déploiement, et veillez à la charger depuis vos variables d'environnement plutôt qu'à la coder en dur dans le code source.

!!! note
`Base.metadata.create_all(engine)` dans le lifespan est une commodité propre au démarrage rapide. Dans un projet de production, vos tables sont gérées par des migrations (comme Alembic). Supprimez cet appel et pointez `Admin` directement vers votre moteur existant. `starlette-admin` ne modifie jamais votre schéma ; il se contente de lire et d'écrire des lignes.

## Cela dépasse largement la démonstration

Tout ce qui précède n'utilise que deux modèles, mais ces mêmes mécanismes de `ModelView` peuvent soutenir un back office de grande ampleur. Vous pouvez facilement mettre en œuvre l'upload de fichiers et d'images, [l'authentification avec contrôle d'accès par rôles](../../user-guide/auth.md), [les filtres personnalisés](../../user-guide/filters.md), [les actions sur ligne et par lot](../../user-guide/actions.md) et une [internationalisation i18n](../../user-guide/i18n.md) complète. Chaque fois que le comportement intégré s'avère insuffisant, chaque requête et chaque étape du cycle de vie propose un hook de substitution. C'est exactement de cette manière que sont construits des motifs comme [les suppressions douces avec vue corbeille](soft-deletes-trash-view.md).

---

## Pour aller plus loin

- **[Concepts](../../getting-started/concepts.md) :** le vocabulaire sous-jacent à ce que vous venez de construire, pour que la suite de la documentation se lise aisément.
- **[Views](../../user-guide/views.md) :** un examen approfondi de toutes les options de `ModelView`, y compris les hooks de permissions.
- **[Soft Deletes and a Trash View for FastAPI](soft-deletes-trash-view.md) :** la première recette avancée, construite directement sur les hooks de substitution présentés ici.
