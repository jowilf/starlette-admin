---
title: MongoEngine-Integration
description: Erfahren Sie, wie Sie MongoEngine-Modelle mit starlette-admin verbinden,
  um Ihre MongoDB-Daten über ein Admin-Panel zu verwalten.
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# MongoEngine-Integration

MongoEngine bildet MongoDB-Dokumente als synchrone Python-Klassen ab und verwendet dabei eine Field-API im Django-Stil. Das Modul `starlette_admin.contrib.mongoengine` stellt spezialisierte `Admin`- und `ModelView`-Klassen bereit, die administrative Ansichten direkt aus Ihren `mongoengine.Document`-Definitionen erzeugen.

**Wichtigste Funktionen:**

* Automatische Konvertierung von Feldtypen, Beziehungen und eingebetteten Dokumenten.
* Unterstützung für GridFS-basierte `FileField`- und `ImageField`-Uploads ohne zusätzliche Konfiguration.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## Minimalbeispiel

Sie müssen die MongoDB-Verbindung herstellen, bevor eine Anfrage die Admin-Oberfläche erreicht. Am besten kapseln Sie die Verbindungslogik im `lifespan`-Context-Manager Ihrer Hauptanwendung, um sicherzustellen, dass diese Voraussetzung erfüllt ist.

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

Der `ModelView` akzeptiert die `mongoengine.Document`-Klasse direkt. Er leitet die Feldliste, Formulare und Filter automatisch aus den Feldern des Dokuments ab.

## Kernklassen: Admin und ModelView

### Die Klasse `mongoengine.Admin`

Die Klasse `mongoengine.Admin` erweitert die Basisklasse `Admin` um eine spezialisierte Route: `/api/file/{db}/{col}/{pk}`. Diese Route streamt eine GridFS-Datei direkt an den Browser zurück.

Da jeder `FileField`- und `ImageField`-Upload eines MongoEngine-Modells in GridFS gespeichert wird, ist diese Route erforderlich, um diese Dateien bereitzustellen. Verwenden Sie daher immer `mongoengine.Admin` anstelle der Basisklasse `Admin`.

### Die Klasse `mongoengine.ModelView`

Anders als die Basisklasse nimmt der Konstruktor von `mongoengine.ModelView` ein positionales Argument `document` entgegen statt einer deklarativen Modellklasse:

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

Wenn Sie das Attribut `fields` in Ihrer `ModelView`-Unterklasse nicht setzen, enthält es standardmäßig jedes Feld des Dokuments in der Reihenfolge seiner Deklaration.

Attribute wie `key`, `menu_label` und `display_name` folgen einer festen Fallback-Reihenfolge:

1. Das Konstruktorargument.
2. Ein auf Klassenebene gesetztes Attribut der Unterklasse.
3. Ein aus dem Klassennamen des Dokuments abgeleiteter Wert (`key` wird zum slugifizierten Namen, `menu_label` zum pluralisierten, verschönerten Namen und `display_name` zum singularisierten, verschönerten Namen).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Filter-Registry {#filter-registry}

Jeder Feldtyp umfasst einen festen Satz von Filtern, der von der `MongoEngineFilterRegistry` bereitgestellt wird. Sie können diese Standardwerte pro Feld mit dem Argument `filters=[...]` überschreiben.

| Feldtyp | Verfügbare Filter |
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
    Das `ObjectIdField` repräsentiert die `id` des Dokuments.

Im Hintergrund gibt die Methode `apply()` jedes Filters ein MongoEngine-`Q`-Fragment für seine jeweilige Bedingung zurück. Verschachtelte `FilterGroup`-Bäume kombinieren diese Fragmente anschließend mithilfe bitweiser Operatoren (`&` oder `|`), bevor die Abfrage ausgeführt wird. Weitere Details finden Sie in der [Filters](../user-guide/filters.md)-Dokumentation.

## Eingebettete Dokumente

Das `EmbeddedDocumentField` von MongoEngine wird in ein `CollectionField` konvertiert. Dabei wird rekursiv jedes Feld des eingebetteten Dokuments in sein eigenes Unterfeld konvertiert:

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

In diesem Beispiel:

* Das Feld `address` wird beim Erstellen und Bearbeiten als verschachteltes Unterformular gerendert und auf der Detailseite als verschachtelter Block dargestellt.
* Das Feld `comments` (ein `EmbeddedDocumentListField`) wird in ein `ListField` von `CollectionField`-Objekten konvertiert. Es wird als wiederholbare Gruppe von Unterformularen gerendert, wobei pro Listeneintrag eines angezeigt wird.

## Vollständiges lauffähiges Beispiel

Dieser Abschnitt enthält eine vollständige, lauffähige MongoEngine-Integration mit `starlette-admin`.

### 1. Abhängigkeiten installieren

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

Das Paket `fastapi[standard]` enthält die FastAPI CLI, mit der Sie den Entwicklungsserver durch Ausführen von `fastapi dev` starten können.

### 2. Anwendung erstellen

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

> **Erweitertes Beispiel:** [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) im Repository enthält eine voll ausgestattete Anwendung. Sie umfasst Inline-Ansichten, Events sowie benutzerdefinierte Zeilen- und Batch-Aktionen sowie GridFS-Bild- und Datei-Uploads.

---

## Weiterführende Literatur

* **[Views](../user-guide/views.md)**: Erkunden Sie die Konfigurationsoptionen von `BaseModelView`, unabhängig vom verwendeten Backend.
* **[Fields](../user-guide/fields.md):** Detaillierte Anleitung zu jedem Feldtyp und seinen Attributen, einschließlich des `CollectionField`.
* **[Filters](../user-guide/filters.md):** Erkunden Sie die Benutzeroberfläche des Filter-Builders und erfahren Sie, wie Sie einen benutzerdefinierten Filter schreiben.
* **[Beanie](beanie.md):** Entdecken Sie die asynchrone, Pydantic-basierte Alternative für MongoDB.
