---
title: Stockage de fichiers
description: Gérez les téléversements de fichiers et d'images dans starlette-admin
  à l'aide du stockage LocalStorage ou d'un backend compatible S3.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Stockage de fichiers

`FileField` et `ImageField` stockent les fichiers téléversés via un backend de stockage que vous définissez avec le paramètre `storage` du champ.

Créez un backend de stockage une seule fois et réutilisez-le pour tous les champs qui conservent leurs fichiers au même emplacement.


## Exemple minimal

```python hl_lines="8 12 31"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///admin.sqlite")

local = LocalStorage(base_dir="uploads", name="local")


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=local, upload_folder="covers"),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Bookstore", secret_key="change-me")
admin.add_view(BookView(Book))
admin.mount_to(app)
```

Lorsqu'un utilisateur téléverse une couverture via l'interface d'administration, l'administrateur :

* enregistre le fichier dans `uploads/covers/`
* stocke un objet de métadonnées JSON dans la colonne `cover`

La base de données ne contient jamais le fichier lui-même, ni un chemin d'accès au système de fichiers, ni des données binaires.


## Contenu stocké dans la base de données

L'administrateur représente un fichier téléversé sous la forme d'un objet [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo) sérialisé dans le champ du modèle.

```json
{
  "filename": "product-photo.jpg",
  "content_type": "image/jpeg",
  "size": 204800,
  "storage": "s3",
  "key": "uploads/products/a1b2c3_product-photo.jpg",
  "url": "https://..."
}
```

* `filename` : nom de fichier original assaini, utilisé pour l'affichage
* `content_type` : type MIME détecté lors du téléversement
* `size` : taille du fichier en octets
* `storage` : nom du backend enregistré, utilisé pour localiser le fichier afin de générer les URL et effectuer les suppressions
* `key` : chemin relatif au stockage ou clé d'objet
* `url` : URL publique mise en cache

`LocalStorage` stocke une valeur `url` vide, car les URL dépendent de la requête active. `S3Storage` stocke une URL publique ou pré-signée, selon votre configuration.

Quel que soit le backend, `FileField` régénère l'URL au moment du rendu avec `storage.url()` plutôt que de se fier à la valeur stockée.

`ImageField` ajoute `width` et `height`.

L'administrateur assainit chaque nom de fichier avec `secure_filename` avant de le stocker : il supprime les composants de chemin et remplace les caractères hors de `[A-Za-z0-9_.-]` par `_`. Consultez [Sécurité](security.md).


## Backends de stockage

### Stockage local

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | obligatoire | Répertoire racine des fichiers stockés. Créé automatiquement s'il n'existe pas. |
| `name` | `str | None` | `"local"` | Nom d'enregistrement identifiant le backend. Doit être unique si vous utilisez plusieurs instances. |

L'administrateur sert les fichiers via cette route :

```
/_files/{storage}/{path}
```

Aucune configuration supplémentaire de fichiers statiques n'est nécessaire.

`LocalStorage.url()` construit les URL à partir du contexte de requête courant ; le champ `url` stocké reste donc vide et est recalculé à la demande.

!!! note
    Consultez [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) pour un exemple de code.

### Stockage Amazon S3

```python
from starlette_admin.storage import S3Storage

s3 = S3Storage(
    bucket="my-bucket",
    prefix="admin/",
    region="eu-west-1",
    public=False,
)
```

Installez les dépendances optionnelles :

```bash
pip install starlette-admin[s3]
```

Ceci installe `aiobotocore`.

| Paramètre | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `bucket` | `str` | obligatoire | Nom du bucket S3. |
| `prefix` | `str` | `"uploads/"` | Préfixe de clé appliqué à chaque objet stocké. |
| `region` | `str` | `"us-east-1"` | Région AWS utilisée pour la signature et la génération des URL. |
| `access_key` et `secret_key` | `str | None` | `None` | Identifiants optionnels. À défaut, la chaîne d'identifiants AWS par défaut est utilisée. |
| `public` | `bool` | `True` | Lorsque `True`, renvoie une URL publique. Lorsque `False`, génère des URL pré-signées. |
| `expires` | `int` | `3600` | Durée d'expiration des URL pré-signées, en secondes. |
| `endpoint_url` | `str | None` | `None` | Endpoint personnalisé compatible S3, tel que MinIO, R2 ou B2. |
| `name` | `str | None` | `"s3"` | Nom d'enregistrement identifiant le backend. |

Lorsque vous fournissez `endpoint_url`, l'administrateur construit les URL comme suit :

```
{endpoint_url}/{bucket}/{key}
```

au lieu d'utiliser le format virtual-hosted d'AWS.


!!! important
    Les champs de fichiers doivent correspondre à une colonne de base de données capable de stocker du JSON. La base de données ne contient que les métadonnées. Le backend de stockage conserve le fichier lui-même.


## Fichiers multiples (`multiple=True`)

Définissez `multiple=True` sur un `FileField` ou un `ImageField` pour accepter plusieurs téléversements dans un même champ.

```python
from starlette_admin import FileField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/attachments", name="attachments")


class TicketView(ModelView):
    fields = [
        "id",
        "subject",
        FileField(
            "attachments",
            storage=local,
            upload_folder="tickets/",
            multiple=True,
        ),
    ]
```

La base de données stocke une liste JSON d'objets `FileInfo`, et l'administrateur traite chaque fichier indépendamment, de la validation jusqu'au stockage.


!!! warning
    L'enregistrement du formulaire remplace l'intégralité de la liste de fichiers par ceux soumis. Il est impossible d'ajouter ou de supprimer un fichier individuellement. Pour gérer le cycle de vie de chaque fichier, utilisez un modèle inline avec son propre `FileField`.

!!! important
    `ListField(FileField(...))` n'est pas pris en charge. Utilisez `multiple=True` pour des collections simples et des modèles inline pour des données de fichiers structurées.

## Validation

La validation s'exécute dans cet ordre :

1. `accept`
2. `max_size`
3. `validators` personnalisés

Un validateur personnalisé est un callable qui reçoit la requête, le champ, un `UploadFile` et l'ensemble des valeurs soumises via le formulaire. Il doit renvoyer `None` ou lever une exception `ValueError`.

L'exemple suivant valide le contenu réel du fichier avec la bibliothèque `filetype` :

```python
import filetype
from starlette.datastructures import UploadFile
from starlette.requests import Request
from starlette_admin.fields import BaseField

ALLOWED_DOCUMENT_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def validate_document_type(
    request: Request, field: BaseField, upload: UploadFile, form_values: dict
) -> None:
    upload.file.seek(0)
    try:
        header = upload.file.read(2048)
        kind = filetype.guess(header)
        detected = kind.mime if kind else "application/octet-stream"
    finally:
        upload.file.seek(0)

    if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
        raise ValueError(
            f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
        )
```

!!! important "Réinitialiser le pointeur de fichier"
    Réinitialisez toujours le pointeur de fichier avec `seek(0)` avant et après l'inspection, afin que la couche de stockage puisse lire le fichier complet.

!!! note
    Les validateurs s'exécutent par fichier : avec `multiple=True`, chaque fichier est validé indépendamment. `ImageField` applique sa propre validation d'image avant tout validateur personnalisé.


!!! tip "Bonnes pratiques"
    Utilisez `accept` et `max_size` pour une validation légère.

    Recourez à des validateurs personnalisés lorsque vous devez inspecter le contenu des fichiers ou appliquer des règles propres à votre application.

    Ne vous fiez ni aux extensions de fichiers ni aux en-têtes `Content-Type` pour une validation sensible en matière de sécurité. Inspectez plutôt le contenu, à l'aide d'une bibliothèque telle que `filetype` ou `python-magic`.


## Limitations du nettoyage des fichiers

`starlette-admin` téléverse les fichiers vers le backend de stockage et écrit les métadonnées `FileInfo` dans la base de données, mais il ne nettoie pas les fichiers après un échec ou une suppression. Deux comportements découlent de ce choix :

* **Transactions échouées :** Si une transaction de base de données est annulée (rollback) après la fin d'un téléversement, le fichier demeure dans le backend de stockage. Les écritures dans le stockage ne disposent d'aucun mécanisme de rollback.
* **Suppressions et mises à jour :** Supprimer une ligne ou remplacer un fichier retire la référence `FileInfo` de la base de données, mais l'ancien fichier reste dans `LocalStorage` ou `S3Storage`.

Cette conception maintient la couche de stockage simple et empêche les erreurs applicatives de déclencher des opérations destructrices. La contrepartie est que les fichiers orphelins s'accumulent. Pour éviter que le stockage ne croisse sans limite, rapprochez-les vous-même régulièrement. Un motif courant consiste à mettre en place une tâche de fond périodique qui compare les clés présentes dans votre backend de stockage aux références `FileInfo` actives dans votre base de données.

### Alternative transactionnelle

Si votre application exige que les opérations de stockage de fichiers soient transactionnelles avec les écritures en base de données, utilisez une bibliothèque qui lie le stockage de fichiers à l'unité de travail SQLAlchemy.

À la place du paramètre `storage=` du champ, utilisez [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Cette bibliothèque stocke les fichiers dans le cadre du cycle flush/rollback de l'ORM : ainsi, une transaction échouée ou la suppression d'une ligne annule l'écriture du fichier correspondant. Pour un exemple fonctionnel, consultez [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Et ensuite

* **[Fields](fields.md) :** référence de `FileField` et `ImageField`.
* **[Export & Import](export-import.md) :** comment les fichiers sont inclus dans les paquets d'export.
* **[Sécurité](security.md) :** comportement d'assainissement et de validation automatiques.
