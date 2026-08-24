---
title: SQLModel-Integration
description: Erstellen Sie ein umfassendes Admin-Dashboard für Ihre FastAPI-SQLModel-Anwendungen
  mit starlette-admin.
source_hash: 96c8764bbc647c696f3ec02784bf0b7a9b05d3f1b051c40e8783b36bb49e612e
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/sqlmodel/)
<!-- translation-notice:end -->

# SQLModel-Integration

[SQLModel](https://sqlmodel.tiangolo.com/) kombiniert SQLAlchemy-Tabellen mit Pydantic-Validierung in einer einzigen Modellklasse. Da SQLModel-Modelle im Hintergrund SQLAlchemy-Modelle sind, dient das Modul `starlette_admin.contrib.sqlmodel` als dünne Hülle um das bestehende [SQLAlchemy-Backend](sqlalchemy.md).

Statt ein separates System zu implementieren, erbt diese Integration sämtliche Felderkennung, Verwaltung von Primärschlüsseln, Beziehungsbehandlung, Filterung und Session-Middleware direkt vom zentralen SQLAlchemy-Backend. Sie führt eine robuste Validierungsschicht ein, die übermittelte Formulardaten durch die nativen Pydantic-Validatoren Ihres Modells (wie `Field(min_length=...)` oder eigene `@field_validator`-Methoden) laufen lässt, bevor irgendein Datenbank-Schreibvorgang stattfindet. Entstehende `ValidationError`-Ausnahmen werden automatisch in feldbezogene Formularfehler in der Benutzeroberfläche übersetzt.

!!! note
    Alles, was auf der [SQLAlchemy-Seite](sqlalchemy.md) dokumentiert ist, gilt unverändert. Dies umfasst synchrone und asynchrone Engines, `sessionmaker`-Provider, den Session-Lebenszyklus mit einem Commit pro Request, Beziehungsfelder und die Filter-Registry.

## Installation

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel
    ```

## Minimalbeispiel

```python
from sqlalchemy import create_engine
from sqlmodel import Field, SQLModel
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine(
    "sqlite:///store.sqlite", connect_args={"check_same_thread": False}
)


class Product(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)
    price: float


class ProductView(ModelView):
    fields = ["id", "name", "price"]


SQLModel.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

Die Klasse `ModelView` akzeptiert die SQLModel-Tabellenklasse direkt und leitet die Feldliste, Formulare und Filter automatisch aus dem Schema des Modells ab.

## Zentrale Klassen

### `sqlmodel.Admin`

Die Klasse `sqlmodel.Admin` ist die re-exportierte Klasse `sqla.Admin`. Sie verwendet denselben Konstruktor und akzeptiert eine `Engine`, eine `AsyncEngine`, einen `sessionmaker` oder einen `async_sessionmaker` als erforderliches Argument `session_provider`. Außerdem fügt sie dieselbe Session-Middleware ein, die bei jedem Request `request.state.session` befüllt.

### `sqlmodel.ModelView`

Die Klasse `sqlmodel.ModelView` erbt alles von `sqla.ModelView` und ergänzt eine Validierungsschicht. Ihre Methode `validate()` ruft vor dem Schreiben des Datensatzes `self.model.model_validate(data)` auf und stellt so sicher, dass Formularübermittlungen durch die Pydantic-Validatoren des Modells geprüft werden, statt sich ausschließlich auf die Spalten-Constraints von SQLAlchemy zu verlassen. Datei- und Beziehungsfelder sind bewusst von diesem Validierungsaufruf ausgeschlossen, da sie außerhalb der Pydantic-Validierungsoberfläche des Modells liegen.

```python
from starlette_admin.contrib.sqlmodel import ModelView


class ArticleView(ModelView):
    fields = ["id", "title", "content", "author"]
    searchable_fields = ["title", "content"]
```

### `sqlmodel.InlineModelView`

Inline-Ansichten ermöglichen es Benutzern, verwandte Zeilen direkt innerhalb des übergeordneten Formulars zu bearbeiten. Die Klasse erbt die Erkennung von Fremdschlüsseln und die Session-Behandlung von der SQLAlchemy-Klasse `InlineModelView` und wendet dieselbe Pydantic-Validierung auf jede Inline-Zeile an.

```python
from starlette_admin.contrib.sqlmodel import InlineModelView, ModelView


class CommentInline(InlineModelView):
    model = Comment
    fields = ["id", "author_name", "body"]
    extra = 1


class ArticleView(ModelView):
    inlines = [CommentInline]
```

## Pydantic-Validierung

Am Modell deklarierte Constraints gelten automatisch für die Erstellen- und Bearbeiten-Formulare:

```python
from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, Relationship, SQLModel


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    full_name: str = Field(min_length=2, index=True)
    email: EmailStr
    created_at: datetime | None = Field(default=None)

    articles: list["Article"] = Relationship(back_populates="author")
```

Eine Eingabe wie ein `full_name` mit weniger als zwei Zeichen oder eine ungültige E-Mail-Adresse schlägt bei der Validierung fehl. Diese Fehler werden als feldbezogene Formularfehler zurückgegeben, bevor irgendeine `INSERT`- oder `UPDATE`-Operation die Datenbank erreicht.

!!! note
    Der Typ `EmailStr` benötigt das Paket `email-validator`, das sich über `pip install "pydantic[email]"` installieren lässt.

## Vollständiges lauffähiges Beispiel

Dieser Abschnitt enthält eine vollständige und ausführbare SQLModel-Integration mit `starlette-admin`.

### 1. Abhängigkeiten installieren

=== "pip"

    ```bash
    pip install starlette-admin sqlmodel "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlmodel "fastapi[standard]"
    ```

Das Paket `fastapi[standard]` enthält die FastAPI-CLI, mit deren Hilfe Sie den Entwicklungsserver durch Ausführen von `fastapi dev` starten können.

### 2. Anwendung erstellen

Speichern Sie den folgenden Code in einer Datei namens `main.py`.

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

from fastapi import FastAPI
from sqlalchemy import Column, Text, create_engine
from sqlmodel import Field, Relationship, SQLModel
from starlette_admin import SlugField
from starlette_admin.contrib.sqlmodel import Admin, ModelView

engine = create_engine("sqlite:///blog.db")


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    name: str = Field(min_length=2)

    posts: list["Post"] = Relationship(back_populates="author")


class Post(SQLModel, table=True):
    id: int | None = Field(primary_key=True, default=None)
    title: str = Field(min_length=3)
    slug: str = Field(unique=True)
    content: str = Field(sa_column=Column(Text))
    status: PostStatus = Field(default=PostStatus.DRAFT)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    author_id: int | None = Field(foreign_key="author.id", default=None)
    author: Author | None = Relationship(back_populates="posts")


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
    SQLModel.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Wenn Sie einen `title` mit weniger als drei Zeichen oder einen `name` mit weniger als zwei Zeichen übermitteln, wird das Formular erneut gerendert, wobei der Fehler am jeweiligen Feld angezeigt wird.

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

> **Erweitertes Beispiel:** [`examples/14-sqlmodel`](https://github.com/jowilf/starlette-admin/tree/main/examples/14-sqlmodel) im Repository enthält ein voll funktionsfähiges CMS-Beispiel mit Beziehungen, Inline-Ansichten, Actions, Filtern, Events und Exporten.

## Was sollten Sie als Nächstes lesen?

* **[SQLAlchemy](sqlalchemy.md):** Das Backend, auf dem diese Integration aufbaut – mit Engines, Sessions, Transaktionen und der Filter-Registry.
* **[Views](../user-guide/views.md):** Erkunden Sie die Konfigurationsoptionen von `BaseModelView` unabhängig vom Backend.
* **[Filters](../user-guide/filters.md):** Erfahren Sie mehr über den Filter-Builder und wie ORM-spezifische Filter eingebunden werden.
