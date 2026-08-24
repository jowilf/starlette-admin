---
title: MongoEngine-Integration
description: Erfahren Sie, wie Sie MongoEngine-Modelle mit starlette-admin verbinden,
  um Ihre MongoDB-Daten über ein Admin-Panel zu verwalten.
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# MongoEngine-Integration

MongoEngine modelliert MongoDB-Dokumente als synchrone Python-Klassen mit einer Field-API im Django-Stil. Das Modul `starlette_admin.contrib.mongoengine` stellt spezialisierte Klassen `Admin` und `ModelView` bereit, die administrative Views direkt aus Ihren `mongoengine.Document`-Definitionen erstellen.

**Wichtigste Funktionen:**

* Automatische Konvertierung von Feldtypen, Beziehungen und eingebetteten Dokumenten.
* Out-of-the-box-Unterstützung für GridFS-basierte Uploads über `FileField` und `ImageField`.

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

Sie müssen die MongoDB-Verbindung herstellen, bevor ein Request das Admin-Interface erreicht. Am besten wrappen Sie die Verbindungslogik im `lifespan`-Contextmanager Ihrer Hauptanwendung, um sicherzustellen, dass diese Voraussetzung erfüllt ist.

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

Die `ModelView` akzeptiert die Klasse `mongoengine.Document` direkt. Sie leitet die Feldliste, die Formulare und die Filter automatisch aus den Feldern des Dokuments ab.

## Kernklassen: Admin und ModelView

### Die Klasse `mongoengine.Admin`

Die Klasse `mongoengine.Admin` erweitert die Basisklasse `Admin` um eine spezialisierte Route: `/api/file/{db}/{col}/{pk}`. Diese Route streamt eine GridFS-Datei direkt zurück an den Browser.

Da jeder Upload über `FileField` und `ImageField` auf einem MongoEngine-Modell in GridFS gespeichert wird, ist diese Route erforderlich, um diese Dateien auszuliefern. Verwenden Sie immer `mongoengine.Admin` statt der Basisklasse `Admin`.

### Die Klasse `mongoengine.ModelView`

Anders als bei der Basisklasse nimmt der Konstruktor der `mongoengine.ModelView` statt einer deklarativen Modellklasse ein positionales Argument `document` entgegen:

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

Wenn Sie das Attribut `fields` in Ihrer `ModelView`-Subklasse nicht setzen, enthält es standardmäßig jedes Feld des Dokuments in der Reihenfolge seiner Deklaration.

Attribute wie `key`, `menu_label` und `display_name` folgen einer strikten Fallback-Reihenfolge:

1. Das Konstruktorargument.
2. Ein auf Klassenebene gesetztes Attribut der Subklasse.
3. Ein Wert, der aus dem Klassennamen des Dokuments abgeleitet wird (`key` wird zur Slug-Version des Namens, `menu_label` wird zum pluralisierten, schön formatierten Namen und `display_name` wird zum singularisierten, schön formatierten Namen).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Filter-Registry

Jeder Feldtyp enthält einen festen Satz an Filtern, der vom `MongoEngineFilterRegistry` bereitgestellt wird. Sie können diese Defaults pro Feld mit dem Argument `filters=[...]` überschreiben.

| Feldtyp | Verfügbare Filter |
| --- | --- |
| `StringField` | enthält, enthält nicht, beginnt mit, endet mit, gleich, nicht gleich, ist null, ist nicht null |
| `TextAreaField` | enthält, enthält nicht, beginnt mit, endet mit, ist null, ist nicht null |
| `EnumField` | gleich, nicht gleich, in, nicht in, ist null, ist nicht null |
| `NumberField` | gleich, nicht gleich, größer als, kleiner als, zwischen, ist null, ist nicht null |
| `FloatField` | gleich, nicht gleich, größer als, kleiner als, zwischen, ist null, ist nicht null |
| `DateField` | gleich, zwischen, in der Vergangenheit, in der Zukunft, ist null, ist nicht null |
| `DateTimeField` | gleich, zwischen, in der Vergangenheit, in der Zukunft, ist null, ist nicht null |
| `BooleanField` | ist wahr, ist falsch, ist null, ist nicht null |
| `TagsField` | in, nicht in, ist null, ist nicht null |
| `RelationField` | ist null, ist nicht null |
| `ObjectIdField` | gleich, nicht gleich, in, nicht in, ist null, ist nicht null |

!!! note
    Das `ObjectIdField` repräsentiert die `id` des Dokuments.

Unter der Haube gibt die Methode `apply()` jedes Filters für seine jeweilige Bedingung ein MongoEngine-`Q`-Fragment zurück. Verschachtelte `FilterGroup`-Bäume kombinieren diese Fragmente anschließend mithilfe bitweiser Operatoren (`&` oder `|`), bevor die Query ausgeführt wird. Weitere Details finden Sie in der Dokumentation zu [Filtern](../user-guide/filters.md).

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

* Das Feld `address` wird beim Erstellen und Bearbeiten als verschachteltes Teilformular dargestellt und auf der Detailseite als verschachtelter Block.
* Das Feld `comments` (ein `EmbeddedDocumentListField`) wird in ein `ListField` von `CollectionField` konvertiert. Es wird als wiederholbare Gruppe von Teilformularen dargestellt, eines pro Listeneintrag.

## Vollständiges, lauffähiges Beispiel

Dieser Abschnitt bietet eine vollständige, lauffähige MongoEngine-Integration mit `starlette-admin`.

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

### 2. Die Anwendung erstellen

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

Navigieren Sie in Ihrem Browser zu [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), um das Admin-Dashboard anzuzeigen und damit zu interagieren.

> **Erweitertes Beispiel:** [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) im Repository enthält eine voll ausgestattete Anwendung. Sie umfasst Inline-Views, Events sowie benutzerdefinierte Zeilen- und Massenaktionen und Uploads von GridFS-Bildern und -Dateien.

---

## Was Sie als Nächstes lesen können

* **[Views](../user-guide/views.md)**: Erkunden Sie die Konfigurationsoptionen von `BaseModelView`, unabhängig vom Backend.
* **[Felder](../user-guide/fields.md):** Detaillierter Leitfaden zu jedem Feldtyp und seinen Attributen, einschließlich des `CollectionField`.
* **[Filter](../user-guide/filters.md):** Erkunden Sie die Benutzeroberfläche des Filter-Builders und erfahren Sie, wie Sie einen benutzerdefinierten Filter schreiben.
* **[Beanie](beanie.md):** Entdecken Sie die asynchrone, auf Pydantic basierende Alternative für MongoDB.
