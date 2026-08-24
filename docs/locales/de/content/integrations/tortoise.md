---
title: Tortoise-ORM-Integration
description: Erstellen Sie mit starlette-admin ganz einfach ein Admin-Interface für
  Ihre Tortoise-ORM-Modelle in FastAPI.
source_hash: 1cf5d85b26decc7ad12c8dd48040809f644a91e9c46410d700a5e5a72f72c39f
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
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

Tortoise ORM ist ein asyncio-nativer Object-Relational Mapper, der von Django inspiriert ist. Das Modul `starlette_admin.contrib.tortoise` stellt spezialisierte `Admin`-, `ModelView`- und `InlineModelView`-Klassen bereit, die vorkonfiguriert sind, um sich direkt in Ihre Tortoise-Modelle zu integrieren.

**Wichtigste Funktionen:**

* **Automatische Feldkonvertierung:** Bildet Tortoise-Modellfelder direkt auf UI-Komponenten ab. Dies umfasst volle Unterstützung für Enums, JSON, Datumsangaben und automatische Zeitstempel.
* **Relationales Mapping:** Konvertiert Fremdschlüssel- und One-to-One-Beziehungen in `HasOne`-Felder und Many-to-Many-Beziehungen in `HasMany`-Felder. Rückwärtsbeziehungen werden automatisch als schreibgeschützt dargestellt.
* **Erweiterte Filterung:** Nutzt Tortoise-`Q`-Ausdrücke für den Filterbuilder und ermöglicht eine Groß-/Kleinschreibung ignorierende Volltextsuche über String-Felder hinweg.
* **Fehlerübersetzung:** Bildet Tortoise-Validierungsfehler direkt auf feldspezifische Formularfehler im UI ab.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin tortoise-orm
    ```

=== "uv"

    ```bash
    uv add starlette-admin tortoise-orm
    ```

## Minimalbeispiel

Tortoise verbindet sich innerhalb des `lifespan`-Context-Managers Ihrer Anwendung mit der Datenbank. Da Admin-Views typischerweise zur Importzeit instanziiert werden (bevor `Tortoise.init()` ausgeführt wird), müssen Sie Beziehungen frühzeitig auflösen.

Rufen Sie `Tortoise.init_models()` unmittelbar nach der Definition Ihrer Modelle auf, um sicherzustellen, dass die Beziehungen verfügbar sind, wenn die Admin-Views erstellt werden.

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

Die `ModelView` akzeptiert die Tortoise-`Model`-Klasse direkt und leitet automatisch die Feldliste, Formulare und Filter aus dem Schema des Datenbankmodells ab.

## Kernklassen

### `tortoise.Admin`

Die Klasse `tortoise.Admin` erbt von `BaseAdmin` und erfordert bei der Initialisierung keine datenbankspezifische Konfiguration. Das Verbindungsaufbau erfolgt vollständig innerhalb des Lifespans der Anwendung. Importieren Sie `Admin` immer aus `starlette_admin.contrib.tortoise`, um die Kompatibilität mit zukünftigen backend-spezifischen Erweiterungen sicherzustellen.

### `tortoise.ModelView`

Die Klasse `tortoise.ModelView` bildet die Integrationsschicht zwischen Ihrer Datenbank und dem User Interface. Sie übernimmt folgende Operationen automatisch:

* **Feldbefüllung:** Generiert Felder aus der Modelldefinition, sofern Sie diese nicht explizit angeben. Die rohen Schlüsselspalten, die To-One-Beziehungen unterliegen (wie `author_id` für eine Beziehung namens `author`), sowie Rückwärtsbeziehungen werden standardmäßig ausgelassen.
* **Beziehungsauslösung:** Lädt jede von der View angezeigte Beziehung vorab (Prefetch). Dadurch lösen Listen- und Detailseiten niemals Lazy Loads aus.
* **Auto-Zeitstempel:** Spalten mit `DatetimeField(auto_now=...)` oder `DatetimeField(auto_now_add=...)` werden schreibgeschützt dargestellt und nie als erforderlich markiert.
* **Fehlerbehandlung:** Übersetzt Tortoise-Validierungsfehler (`"<field>: <detail>"`) in feldspezifische Formularfehler, die Benutzerinnen und Benutzer direkt auf die fehlerhafte Eingabe hinweisen.

```python
from starlette_admin.contrib.tortoise import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

### `tortoise.InlineModelView`

Inline-Views ermöglichen es Benutzern, verwandte Zeilen innerhalb des übergeordneten Formulars zu bearbeiten. Der Fremdschlüssel wird automatisch erkannt, wenn das Kindmodell genau eine Beziehung zum Elternmodell besitzt. Wenn mehrere Beziehungen existieren, müssen Sie `fk_attr` explizit festlegen, entweder mit dem Namen der Beziehung oder mit ihrer rohen Schlüsselspalte.

```python
from starlette_admin.contrib.tortoise import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author", "body"]
    extra = 2


class PostView(ModelView):
    inlines = [CommentInline]
```

## Umgang mit Beziehungen

Die Integration bildet Datenbankbeziehungen anhand des Feldtyps auf Admin-Felder ab. Sie müssen für jedes verwandte Modell eine `ModelView` registrieren, damit Beziehungsfelder ihre fremden Views erfolgreich auflösen können.

| Beziehungstyp | Tortoise-Konfiguration | Admin-Verhalten |
| --- | --- | --- |
| **Forward (To-One)** | `ForeignKeyField`, `OneToOneField` | Wird zu `HasOne` konvertiert. |
| **Forward (To-Many)** | `ManyToManyField` | Wird zu `HasMany` konvertiert. |
| **Backward** | `related_name`-Properties | Wird schreibgeschützt dargestellt. Muss explizit zu `fields` hinzugefügt werden, um angezeigt zu werden. |

**Filtern und Sortieren über Beziehungen:**
To-One-Beziehungen bieten die Filter „Is null“ und „Is not null“, die auf die rohe Schlüsselspalte abzielen. Um eine Beziehung im Filterbuilder verfügbar zu machen, fügen Sie den Beziehungsnamen zu `searchable_fields` hinzu. Um die Sortierung nach der rohen Schlüsselspalte zu ermöglichen, fügen Sie den Beziehungsnamen zu `sortable_fields` hinzu.

## Suche und Filterung

### Filterregistry

Jeder Feldtyp erhält einen Standardsatz von Filtern aus der `TortoiseFilterRegistry`, implementiert mit Tortoise-`Q`-Ausdrücken:

* **String-Matching:** Contains-, Starts/Ends-With- und Equality-Filter verwenden Lookups ohne Berücksichtigung der Groß-/Kleinschreibung (`__icontains`, `__istartswith`, `__iendswith`, `__iexact`).
* **Enums:** Rohe Filterwerte werden vor der Query sowohl für `CharEnumField`- als auch für `IntEnumField`-Spalten zurück in Enum-Member umgewandelt.
* **Zeitspalten:** `TimeField`-Spalten bieten nur Null-Prüfungen. Diese Einschränkung besteht, weil Parameter vom Typ Time nicht portabel über alle Database-Backends hinweg gebunden werden können.

### Volltextsuche

Das Suchfeld der Listenseite erstellt eine Groß-/Kleinschreibung ignorierende `contains`-Übereinstimmung (`OR`-kombinierte `Q`-Ausdrücke) über alle durchsuchbaren String-artigen Felder hinweg. Sie können dieses Verhalten anpassen, indem Sie die Methode `get_search_query()` Ihrer View überschreiben.

## Vollständiges lauffähiges Beispiel

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

Das Paket `fastapi[standard]` enthält die FastAPI CLI, mit der Sie den Entwicklungsserver durch Ausführung von `fastapi dev` starten können.

### 2. Die Anwendung erstellen

Speichern Sie den folgenden Code in einer Datei namens `main.py`.

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

Da `created_at` `auto_now_add` verwendet, stellt das Admin-Interface es automatisch schreibgeschützt dar. Eine Konfiguration mit `exclude_fields_from_create` oder `exclude_fields_from_edit` ist nicht erforderlich.

### 3. Den Server starten

Starten Sie den FastAPI-Entwicklungsserver:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Navigieren Sie in Ihrem Browser zu [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), um das Dashboard anzuzeigen und damit zu interagieren.

> **Fortgeschrittenes Beispiel:** [`examples/17-tortoise`](https://github.com/jowilf/starlette-admin/tree/main/examples/17-tortoise) im Repository enthält ein voll funktionsfähiges Beispiel, das Beziehungen, Inline-Views, Enums und JSON-Felder auf Basis von SQLite umfasst.

## Was Sie als Nächstes lesen sollten

* **[Views](../user-guide/views.md):** Erkunden Sie die Konfigurationsoptionen von `BaseModelView`, unabhängig vom Backend.
* **[Filters](../user-guide/filters.md):** Erfahren Sie mehr über den Filterbuilder und wie ORM-spezifische Filter eingebunden werden.
* **[SQLAlchemy](sqlalchemy.md):** Dokumentation für das andere relationale Backend, das in starlette-admin integriert ist.
