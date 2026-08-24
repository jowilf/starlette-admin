---
title: Beanie-Integration
description: Integrieren Sie Beanie ODM mit starlette-admin, um ein erweiterbares
  Admin-Interface für Ihre MongoDB-Collections in FastAPI zu erstellen.
source_hash: 1b2f0bd151bdc41a3d8d605af17c01b6f8fa4c68e1d5397f15bdd134a391fb10
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/beanie/)
<!-- translation-notice:end -->

# Beanie-Integration

Beanie modelliert MongoDB-Dokumente als asynchrone Pydantic-Modelle. Das Modul `starlette_admin.contrib.beanie` bietet spezialisierte `Admin`- und `ModelView`-Klassen, die so konfiguriert sind, dass sie direkt mit diesen Dokumenten interagieren.

**Hauptfunktionen:**

- Native Unterstützung für MongoDB-Queryoperatoren und Filterung.
- Automatische Übersetzung von Pydantic-Validierungsfehlern in feldspezifische UI-Formularfehler.
- Integrierte Unterstützung für die MongoDB-Volltextsuche.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin beanie
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie
    ```

## Minimalbeispiel

Sie müssen Beanie initialisieren, bevor ein Request das Admin-Interface erreicht. Es ist der beste Ansatz, die Verbindungslogik in den `lifespan`-Context-Manager Ihrer Hauptanwendung zu wrappen, um sicherzustellen, dass diese Voraussetzung erfüllt ist.

```python
from contextlib import asynccontextmanager

import uvicorn
from beanie import Document, init_beanie
from pymongo import AsyncMongoClient
from starlette.applications import Starlette
from starlette_admin.contrib.beanie import Admin, ModelView


class Genre(Document):
    name: str
    description: str | None = None

    class Settings:
        name = "genres"


mongo_client = AsyncMongoClient("mongodb://localhost:27017")


@asynccontextmanager
async def lifespan(app: Starlette):
    await init_beanie(
        database=mongo_client.get_database("library"), document_models=[Genre]
    )
    yield


app = Starlette(lifespan=lifespan)

admin = Admin(title="Library Admin", secret_key="a-long-random-string")
admin.add_view(ModelView(Genre, icon="fa fa-tags"))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

Die `ModelView` akzeptiert die Beanie-Klasse `Document` direkt. Sie leitet automatisch die Feldliste, die Formulare und die Filter aus den Feldern des Dokuments ab.

## Kernklassen

### Die Klasse `beanie.Admin`

Die Klasse `beanie.Admin` erbt von `BaseAdmin` und benötigt bei der Initialisierung keine datenbankspezifische Konfiguration. Das Einrichten der Verbindung erfolgt vollständig innerhalb des Lifespan der Anwendung. Importieren Sie `Admin` immer aus `starlette_admin.contrib.beanie`, um die Kompatibilität mit zukünftigen backend-spezifischen Erweiterungen sicherzustellen.

### Die Klasse `beanie.ModelView`

Die Klasse `beanie.ModelView` stellt die Integrationsschicht zwischen Ihrer Datenbank und dem UI bereit. Sie übernimmt mehrere Operationen automatisch:

- **Feldpopulation:** Generiert automatisch Felder aus der Dokumentdefinition, wenn Sie diese nicht explizit angeben.
- **Filterung interner Felder:** Schließt standardmäßig Beanies internes Feld `revision_id` aus Listen und Formularen aus.
- **Auflösung von Beziehungen:** Führt Datenbank-Lesungen mit `fetch_links=True` und `nesting_depth=1` durch, sodass `Link`-Referenzen zu ihren verwandten Objekten aufgelöst werden, anstatt rohe Datenbankreferenzen zurückzugeben.
- **Fehlerbehandlung:** Übersetzt Pydantic-Validierungsfehler in feldspezifische Formularfehler und verweist Benutzer direkt auf die fehlerhafte Eingabe.

```python
from starlette_admin.contrib.beanie import ModelView


class BookView(ModelView):
    fields = ["id", "title", "isbn", "genres"]
    searchable_fields = ["title", "isbn"]
    sortable_fields = ["title"]
```

## Das `BeanieObjectIdField`

Beanie verwendet `PydanticObjectId` als Primärschlüssel. Das Admin-Panel stellt diese Schlüssel sowie alle rohen ObjectId-Referenzen automatisch mithilfe eines dedizierten `BeanieObjectIdField`s dar.

Es wird zwar genau wie ein Standard-`StringField` gerendert und validiert, hat aber einen eigenen Slot in der Filterregistrierung. Diese Trennung stellt sicher, dass ObjectId-spezifische Filter nur auf ObjectId-Felder angewendet werden, nicht auf jedes Standard-Textfeld in Ihrer Anwendung. Diese spezialisierten Filter parsen Strings sicher in gültige `PydanticObjectId`-Objekte, bevor sie die Datenbank abfragen.

## Filterregistrierung

Jeder Feldtyp erhält einen Default-Satz an Filtern aus der `BeanieFilterRegistry`.

- **String-Matching:** Der Gleichheitsfilter verwendet case-insensitive reguläre Ausdrücke, um Konsistenz mit anderen Textsuchen wie „Contains“ oder „Starts with“ zu wahren.
- **Array-Operationen:** Die Registry bietet integrierte Unterstützung für arraybasierte Filterung, sodass Operationen wie „Is one of“ auf Listenfelder (wie `TagsField`) sofort funktionieren.
- **Primärschlüssel:** Das Feld `id` wird beim Erstellen von Queryfragmenten automatisch auf MongoDBs natives `_id` umgemappt.

## Volltextsuche

Wenn Benutzer mit dem Suchfeld auf einer Listenseite interagieren, prüft das Admin-Panel, ob in der MongoDB-Collection ein vorhandener Textindex existiert, und passt seine Querystrategie entsprechend an:

- **Textindex vorhanden:** Die Query nutzt MongoDBs nativen `$text`-Operator. Dies bietet echte Volltextsuchfunktionen, einschließlich Tokenisierung, Stemming und Relevanz-Ranking.
- **Kein Textindex vorhanden:** Das System fällt auf eine case-insensitive Suche mit regulären Ausdrücken über alle Felder zurück, die als `searchable` markiert sind. Dies erfordert zwar keine Einrichtung, kann Ergebnisse jedoch nicht nach Relevanz ordnen und keine Standardindizes nutzen.

Das Admin-Panel erkennt vorhandene Textindizes, erstellt aber keine. Sie müssen den Index in Ihrem Beanie-Dokument definieren, um die native Textsuche zu aktivieren. Sie können dies zum Beispiel erreichen, indem Sie `class Settings: indexes = [[("title", "text"), ("synopsis", "text")]]` zu Ihrem Modell hinzufügen.

!!! note
Wenn Sie einen Textindex aktivieren, können Sie `full_text_override_order_by = True` in Ihrer `ModelView`-Unterklasse setzen, um Suchergebnisse nach MongoDBs Relevanzscore statt nach der Standardspaltensortierung zu sortieren.

## Vollständiges Arbeitsbeispiel

Dieser Abschnitt bietet eine vollständige, lauffähige Beanie-Integration mit `starlette-admin`.

### 1. Abhängigkeiten installieren

=== "pip"

    ```bash
    pip install starlette-admin beanie "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin beanie "fastapi[standard]"
    ```

Das Paket `fastapi[standard]` enthält die FastAPI CLI, mit der Sie den Entwicklungsserver durch Ausführen von `fastapi dev` starten können.

### 2. Anwendung erstellen

Speichern Sie den folgenden Code in einer Datei namens `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from beanie import Document, Link, init_beanie
from fastapi import FastAPI
from pydantic import Field
from pymongo import AsyncMongoClient
from starlette_admin import SlugField
from starlette_admin.contrib.beanie import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"
mongo_client = AsyncMongoClient(MONGO_URI)


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(Document):
    name: str

    async def __admin_repr__(self, request) -> str:
        return self.name

    class Settings:
        name = "authors"


class Post(Document):
    title: str
    slug: str
    content: str
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    author: Link[Author]

    async def __admin_repr__(self, request) -> str:
        return self.title

    class Settings:
        name = "posts"


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
    await init_beanie(
        database=mongo_client.get_database("blog"), document_models=[Author, Post]
    )
    yield


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

Rufen Sie [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) in Ihrem Browser auf, um das Dashboard anzusehen und mit dem Dashboard zu interagieren.

> **Erweitertes Beispiel:** [`examples/15-beanie`](https://github.com/jowilf/starlette-admin/tree/main/examples/15-beanie) im Repository enthält ein vollständiges Beispiel mit Inline-Views, Events und benutzerdefinierten Massenaktionen.

## Was Sie als Nächstes lesen sollten

- **[Views](../user-guide/views.md)**: Erkunden Sie die Konfigurationsoptionen von `BaseModelView` unabhängig vom Backend.
- **[Filters](../user-guide/filters.md):** Den Filter-Builder und wie ORM-spezifische Filter eingebunden werden.
- **[MongoEngine](mongoengine.md):** Ein weiteres MongoDB-Backend, das in starlette-admin eingebaut ist.
- **[SQLAlchemy](sqlalchemy.md):** Das relationale Backend, das in starlette-admin eingebaut ist.
