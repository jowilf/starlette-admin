---
title: Tortoise-ORM-Integration
description: Erstellen Sie mit starlette-admin ganz einfach eine Admin-Oberfläche
  für Ihre Tortoise-ORM-Modelle in FastAPI.
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/tortoise/)
<!-- translation-notice:end -->

# Tortoise-ORM-Integration

Tortoise ORM ist ein asyncio-nativer Object-Relational Mapper, der von Django inspiriert ist. Das Modul `starlette_admin.contrib.tortoise` stellt spezialisierte Klassen `Admin`, `ModelView` und `InlineModelView` bereit, die vorkonfiguriert sind und sich direkt in Ihre Tortoise-Modelle integrieren lassen.

**Wichtigste Funktionen:**

* **Automatische Feldkonvertierung:** Bildet Tortoise-Modellfelder direkt auf UI-Komponenten ab. Dies umfasst vollständige Unterstützung für Enums, JSON, Datumsangaben und automatische Zeitstempel.
* **Relationale Abbildung:** Konvertiert Foreign-Key- und One-to-One-Relationen in `HasOne`-Felder sowie Many-to-Many-Relationen in `HasMany`-Felder. Rückwärtsrelationen werden automatisch schreibgeschützt dargestellt.
* **Erweiterte Filterung:** Nutzt Tortoise-`Q`-Ausdrücke für den Filter-Builder und ermöglicht eine case-insensitive Volltextsuche über String-Felder.
* **Fehlerübersetzung:** Ordnet Tortoise-Validierungsfehler direkt feldspezifischen Formularfehlern in der Benutzeroberfläche zu.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## Minimales Beispiel

Tortoise verbindet sich innerhalb des `lifespan`-Context-Managers Ihrer Anwendung mit der Datenbank. Da Admin-Views typischerweise zur Importzeit instanziiert werden (also bevor `Tortoise.init()` ausgeführt wird), müssen Sie Relationen frühzeitig auflösen.

Rufen Sie `Tortoise.init_models()` unmittelbar nach der Definition Ihrer Modelle auf, um sicherzustellen, dass die Relationen verfügbar sind, wenn die Admin-Views aufgebaut werden.

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


# Resolve relations at import time before the admin views are built.
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

Die Klasse `ModelView` akzeptiert die Tortoise-Klasse `Model` direkt und leitet die Feldliste, Formulare und Filter automatisch aus dem Schema des Modells ab.

## Zentrale Klassen

### `tortoise.Admin`

Die Klasse `tortoise.Admin` erbt von `BaseAdmin` und benötigt bei der Initialisierung keine datenbankspezifische Konfiguration. Der Verbindungsaufbau erfolgt vollständig innerhalb des Lifespans der Anwendung. Importieren Sie `Admin` immer aus `starlette_admin.contrib.tortoise`, um die Kompatibilität mit zukünftigen backend-spezifischen Erweiterungen sicherzustellen.

### `tortoise.ModelView`

Die Klasse `tortoise.ModelView` bildet die Integrationsschicht zwischen Ihrer Datenbank und der Benutzeroberfläche. Sie übernimmt folgende Operationen automatisch:

* **Feldbefüllung:** Generiert Felder aus der Modelldefinition, sofern Sie diese nicht explizit angeben. Die rohen Schlüsselspalten, die To-one-Relationen zugrunde liegen (z. B. `author_id` für eine Relation namens `author`), sowie Rückwärtsrelationen werden standardmäßig ausgelassen.
* **Relationsauflösung:** Lädt jede Relation vorab (Prefetching), die von dem View angezeigt wird. Dadurch lösen Listen- und Detailseiten niemals Lazy Loads aus.
* **Automatische Zeitstempel:** Spalten mit `DatetimeField(auto_now=...)` oder `DatetimeField(auto_now_add=...)` werden schreibgeschützt dargestellt und niemals als Pflichtfeld markiert.
* **Fehlerbehandlung:** Übersetzt Tortoise-Validierungsfehler (`"<field>: <detail>"`) in feldspezifische Formularfehler, die Benutzerinnen und Benutzer direkt auf die fehlerhafte Eingabe hinweisen.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Inline-Views ermöglichen es, zugehörige Zeilen innerhalb des übergeordneten Formulars zu bearbeiten. Der Foreign Key wird automatisch erkannt, wenn das untergeordnete Modell genau eine Relation besitzt, die auf das übergeordnete Modell zeigt. Existieren mehrere Relationen, müssen Sie `fk_attr` explizit festlegen – entweder über den Relationsnamen oder dessen rohe Schlüsselspalte.

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## Umgang mit Relationen

Die Integration bildet Datenbankrelationen anhand des Feldtyps auf Admin-Felder ab. Sie müssen für jedes referenzierte Modell einen `ModelView` registrieren, damit Relationsfelder ihre fremden Views erfolgreich auflösen können.

| Relationstyp | Tortoise-Konfiguration | Verhalten im Admin |
| --- | --- | --- |
| **Forward (To-One)** | `ForeignKeyField`, `OneToOneField` | Wird zu `HasOne` konvertiert. |
| **Forward (To-Many)** | `ManyToManyField` | Wird zu `HasMany` konvertiert. |
| **Backward** | `related_name`-Properties | Wird schreibgeschützt dargestellt. Muss explizit zu `fields` hinzugefügt werden, um angezeigt zu werden. |

**Filterung und Sortierung über Relationen:**
To-one-Relationen bieten die Filter „Is null" und „Is not null", die auf die rohe Schlüsselspalte abzielen. Um eine Relation im Filter-Builder verfügbar zu machen, fügen Sie den Relationsnamen zu `searchable_fields` hinzu. Um die Sortierung nach der rohen Schlüsselspalte zu ermöglichen, fügen Sie den Relationsnamen zu `sortable_fields` hinzu.

## Suche und Filterung

### Filter-Registry {#filter-registry}

Jeder Feldtyp erhält einen Standardsatz von Filtern aus der `TortoiseFilterRegistry`, die mithilfe von Tortoise-`Q`-Ausdrücken implementiert ist:

* **String-Matching:** Contains-, Starts/Ends-with- und Equality-Filter verwenden case-insensitive Lookups (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Enums:** Rohe Filterwerte werden vor der Abfrage sowohl bei `CharEnumField`- als auch bei `IntEnumField`-Spalten zurück in Enum-Member konvertiert.
* **Zeitspalten:** `TimeField`-Spalten bieten ausschließlich Null-Prüfungen. Diese Einschränkung besteht, weil Parameter vom Typ Time nicht portabel über alle Datenbank-Backends gebunden werden können.

### Volltextsuche

Das Suchfeld der Listenseite erstellt einen case-insensitiven `contains`-Vergleich (mit `OR` kombinierte `Q`-Ausdrücke) über alle durchsuchbaren string-artigen Felder. Sie können dieses Verhalten anpassen, indem Sie die Methode `get_search_query()` Ihres Views überschreiben.

## Vollständiges Beispiel

Dieser Abschnitt enthält eine vollständige, lauffähige Tortoise-ORM-Integration mit `starlette-admin`.

### 1. Abhängigkeiten installieren

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm "fastapi[standard]"
    ```

Das Paket `fastapi[standard]` enthält die FastAPI CLI, mit der Sie den Entwicklungsserver durch Ausführen von `fastapi dev` starten können.

### 2. Anwendung erstellen

Speichern Sie den folgenden Code in einer Datei mit dem Namen `main.py`.

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


# Resolve relations at import time before the admin views are built.
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

Da `created_at` `auto_now_add` verwendet, stellt der Admin dieses Feld automatisch schreibgeschützt dar. Eine Konfiguration über `exclude_fields_from_create` oder `exclude_fields_from_edit` ist nicht erforderlich.

### 3. Server starten

Starten Sie den FastAPI-Entwicklungsserver:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Rufen Sie [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) in Ihrem Browser auf, um das Admin-Dashboard anzuzeigen und damit zu interagieren.

> **Fortgeschrittenes Beispiel:** [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) im Repository enthält ein vollständiges Beispiel mit Relationen, Inline-Views, Enums und JSON-Feldern auf Basis von SQLite.

## Weiterführende Lektüre

* **[Views](../user-guide/views.md):** Erkunden Sie die Konfigurationsoptionen von `BaseModelView`, unabhängig vom Backend.
* **[Filters](../user-guide/filters.md):** Erfahren Sie mehr über den Filter-Builder und wie ORM-spezifische Filter eingebunden werden.
* **[SQLAlchemy](sqlalchemy.md):** Dokumentation zum anderen relationalen Backend, das in starlette-admin integriert ist.
