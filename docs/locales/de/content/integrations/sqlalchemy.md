---
title: SQLAlchemy-Integration
description: Erfahren Sie, wie Sie starlette-admin mit SQLAlchemy integrieren. Erstellen
  Sie ein Admin-Dashboard für Ihre relationalen Datenbankmodelle in FastAPI.
source_hash: 3d7e8c4a12dca33d3b7e7cbafbf51f9d60a612a418d6d8edf5fda985c1b1af68
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/sqlalchemy/)
<!-- translation-notice:end -->

# SQLAlchemy

Das SQLAlchemy-Backend dient als Referenzimplementierung für `BaseModelView`. Es wurde nur gegen SQLAlchemy-2-`DeclarativeBase`-Modelle getestet. Andere Backends (wie Beanie, MongoEngine, Tortoise ORM oder Ihre eigene Implementierung) erfüllen denselben Contract gegenüber ihren jeweiligen Datenspeichern.

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

Ersetzen Sie `aiosqlite` durch `asyncpg` (PostgreSQL) oder `aiomysql`/`asyncmy` (MySQL), wenn Sie SQLite nicht verwenden möchten. Der Datenbanktreiber ist nur für asynchrone Engines relevant. Eine synchrone Engine verwendet den Standard-DBAPI-Treiber, den plain SQLAlchemy benötigt (wie `psycopg2` oder `pymysql`), und erfordert keine zusätzlichen Pakete von `starlette-admin`.

## Async vs. sync Engines

`Admin` akzeptiert entweder eine `Engine` oder eine `AsyncEngine`. Übergeben Sie die Instanz, die Sie konfiguriert haben:

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine

sync_engine = create_engine("postgresql+psycopg2://user:pass@localhost/store")
async_engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
```

`starlette_admin.contrib.sqla.middleware.DBSessionMiddleware` untersucht die Engine einmal zur Request-Zeit und öffnet den passenden Session-Typ: eine `AsyncSession` für eine `AsyncEngine` oder eine plain `Session` für eine synchrone `Engine`. Intern verzweigt `ModelView` auf Basis von `isinstance(session, AsyncSession)`. Bei synchronen Sessions leitet es den blockierenden Aufruf über `anyio.to_thread.run_sync`, um den Event Loop nicht zu blockieren.

## Einen `sessionmaker` statt einer Engine übergeben

Der Parameter `session_provider` akzeptiert auch einen `sessionmaker` oder `async_sessionmaker`. Übergeben Sie einen Session-Maker statt einer bloßen Engine, wenn Sie die Session direkt konfigurieren müssen.

```python
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette_admin.contrib.sqla import Admin

engine = create_async_engine("postgresql+asyncpg://user:pass@localhost/store")
session_maker = async_sessionmaker(engine, autoflush=False)

admin = Admin(
    session_provider=session_maker, title="Store Admin", secret_key="change-me"
)
```
Die Session-Middleware ruft `session_maker()` auf, um für jeden Request eine neue Session zu erzeugen, anstatt eine intern zu erstellen.

## `sqla.Admin` und `sqla.ModelView`

```python
from starlette_admin.contrib.sqla import Admin, ModelView
```

`sqla.Admin` akzeptiert dieselben Argumente wie `starlette_admin.BaseAdmin` sowie ein erforderliches positionales Argument: `session_provider`. Dieser Provider kann eine `Engine`, eine `AsyncEngine`, ein `sessionmaker` oder ein `async_sessionmaker` sein. Während der Initialisierung konfiguriert das Admin-Panel eine an Ihren gewählten Provider gebundene Session-Middleware und fügt sie am Anfang des Middleware-Stacks ein. Dieser Mechanismus garantiert, dass `request.state.session` bei jedem Request automatisch befüllt wird, bevor Ihr View-Code ausgeführt wird.

`sqla.ModelView` benötigt ein SQLAlchemy-Modell. Bei der Initialisierung untersucht es das Modell, um automatisch Felder zu erkennen, Primärschlüssel zu verwalten und die Filter-Registry direkt aus den Metadaten zu konfigurieren.

## Modelldeklaration

Definieren Sie Ihre Modelle mit standardmäßigen SQLAlchemy-deklarativen Klassen:

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

Wenn Sie `fields` auf der View nicht setzen, verwendet `ModelView` jedes auf dem Modell deklarierte Attribut in der Reihenfolge, in der es erscheint. Der Primärschlüssel wird automatisch erkannt und aus den Create- und Edit-Formularen ausgeschlossen. Jede andere Spalte und Beziehung wird automatisch in einen passenden Feldtyp umgewandelt (z. B. `IntegerField`, `StringField`, `EnumField`, `HasOne` oder `HasMany`).

## Automatisch erkannte Defaultwerte

Die Python-seitige `default=`-Konfiguration einer Spalte wird automatisch befüllt, sobald Sie das Create-Formular zum ersten Mal öffnen. Sie müssen diese Definition nicht auf dem Feld selbst wiederholen:

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

Ein skalarer Defaultwert (`default=0`) wird exakt wie definiert übernommen. Ein aufrufbarer Defaultwert (`default=datetime.utcnow` oder `default=uuid.uuid4`) wird einmal beim Rendern des Formulars ausgelöst, sodass der Leser einen echten Wert sieht statt dem `repr`-Format der Funktion.

!!! important
    Primärschlüsselspalten erhalten niemals einen vorausgefüllten Defaultwert, selbst wenn einer definiert ist. Es wird davon ausgegangen, dass sie serverseitig generiert werden (über `autoincrement` oder eine Sequence), und sie werden vollständig aus den Create- und Edit-Formularen ausgeschlossen. SQL-Ausdrucks-Defaultwerte (wie `server_default=func.now()` oder ein Datenbank-seitiges `DEFAULT`) werden ebenfalls übersprungen, da es keinen Python-seitigen Wert zum Anzeigen gibt. Die Datenbank kümmert sich beim Einfügen um das Befüllen dieser Werte.

## Beziehungsfelder

Eine SQLAlchemy-`relationship()` auf dem Modell wird automatisch in `HasOne` (many-to-one oder one-to-one) oder `HasMany` (one-to-many oder many-to-many) basierend auf dem Attribut `RelationshipProperty.direction` umgewandelt. Sie müssen den Feldtyp nicht explizit deklarieren:

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

Das Setzen von `PostView.fields = ["id", "title", "author"]` rendert `author` als Select2-Dropdown-Menü. Dieses Dropdown-Menü wird per AJAX über den Endpoint `/_api/{key}/relation-lookup` der zugehörigen View befüllt (wobei `{key}` für `author` steht, den Schlüssel von `AuthorView`). Die Anwendung lädt nie die gesamte Tabelle der Autoren auf einmal in die Seite. Dieses Lazy-Loading-Verhalten ist entscheidend für die Leistung, wenn die verwandte Tabelle tausende Zeilen enthält. Ebenso rendert das Setzen von `AuthorView.fields = ["id", "name", "posts"]` `posts` als Multi-Select-Steuerelement, das denselben Lookup-Endpoint nutzt.

## Zusammengesetzte Primärschlüssel

Modelle, die mehrere `primary_key=True`-Spalten für zusammengesetzte Primärschlüssel verwenden, werden ohne zusätzliche Konfiguration unterstützt. Dies umfasst Szenarien, in denen jede Primärschlüsselspalte zugleich als Fremdschlüssel dient, etwa bei einem many-to-many Association Object.

Ein vollständig lauffähiges Beispiel finden Sie unter [examples/12-sqla-composite-pks](https://github.com/jowilf/starlette-admin/tree/main/examples/12-sqla-composite-pks).

## Filter-Registry

Jeder Feldtyp erhält einen Default-Satz an Filtern aus der `SqlaFilterRegistry`. Diese werden aufgelöst, indem die Klassenhierarchie des Feldes durchlaufen wird, wie in der Dokumentation zu [Filtern](../user-guide/filters.md) beschrieben. Ein entscheidendes SQLAlchemy-spezifisches Detail ist, wie jeder Filter in ein Query-Fragment übersetzt wird. Jede `apply()`-Methode in diesem Modul gibt eine eigenständige boolesche SQLAlchemy-Klausel zurück (wie `column == value` oder `column.between(a, b)`).

!!! note
    Der Filter `Is null` auf einer Beziehung wertet `~column.has()` (für many-to-one-Beziehungen) oder `~column.any()` (für one-to-many- und many-to-many-Beziehungen) aus statt `column.is_(None)`. Da ein Beziehungsattribut keine Standardspalte ist, die einen `NULL`-Wert enthält, hängt seine Nullbarkeit vollständig davon ab, ob verwandte Zeilen existieren.

!!! note
    Das SQLAlchemy-Backend stellt im Gegensatz zu Beanie und MongoEngine keine `ArrayInFilter`- oder `ArrayNotInFilter`-Filter bereit (die „is one of“-Filter für spaltenwertige Listen). Sie müssen Ihre eigene `apply()`-Logik schreiben, wenn Sie eine „is one of“-Filterung auf einer JSON- oder ARRAY-Spalte mit einem `TagsField` benötigen. Weitere Details finden Sie in der Dokumentation zu [Benutzerdefinierten Filtern](../advanced/custom-filters.md).

## Sessions und Transaktionen

Die Session-Middleware öffnet genau eine Session pro Request und speichert sie sicher auf `request.state.session`. Dieses Objekt ist eine `AsyncSession`, wenn Sie eine asynchrone Engine (oder einen `async_sessionmaker`) verwenden, andernfalls eine standardmäßige `Session`. Jede vom Request berührte Komponente teilt sich diese einzige Session. Die Listen-Query, die Beziehungs-Lookups innerhalb von Formularen und jegliche benutzerdefinierte Logik, die in einem Hook, einer Aktion oder einem Endpoint läuft, operieren alle innerhalb derselben Transaktion. Sie greifen darauf einheitlich zu, unabhängig vom zugrunde liegenden Engine-Typ:

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

Bei Verwendung einer synchronen Engine ergibt `request.state.session` eine standardmäßige `Session`, und `session.flush()` wird ohne `await` aufgerufen. Der Rest des vorherigen Codeausschnitts bleibt identisch. Sie müssen keine separate `get_session()`-Abhängigkeit importieren. Die Session wird an den Request angehängt, bevor Ihr Hook oder Ihre Aktion ausgeführt wird, da die Session-Middleware die Verbindung herstellt, bevor der Route-Handler aufgerufen wird.

**Ein Commit pro Request.** Sie sollten niemals manuell `session.commit()` aufrufen. Der Aufruf von `flush()` genügt (oder Sie tun nichts, wenn Sie nur Leseabfragen ausführen). Die Session-Middleware committet die Session genau einmal, nachdem der Route-Handler zurückgekehrt ist, sofern die Response Erfolg anzeigt. Tritt ein Fehler auf, macht die Middleware die gesamte Transaktion automatisch rückgängig:

* Wenn der Handler eine Exception auslöst, macht die Session die Änderungen rückgängig und die Anwendung löst die Exception erneut aus.
* Wenn der Handler eine Response mit einem `status_code >= 400` zurückgibt (z. B. bei fehlgeschlagener Formularvalidierung), macht die Session die Änderungen rückgängig, und der Server gibt die Response unverändert zurück. Dieser Rollback ist entscheidend, weil die Transaktion in diesem Stadium möglicherweise einen fehlgeschlagenen Flush enthält. Ihn zu committen könnte versehentlich einen teilweise geschriebenen Datensatz persistieren.
* Wenn der Commit-Vorgang selbst eine Exception auslöst (etwa eine Datenbank-Constraint-Verletzung, die beim Flush entdeckt wird), macht die Session die Änderungen rückgängig und löst die Exception erneut aus.

In allen anderen Szenarien, in denen der Handler eine 2xx- oder 3xx-Response liefert, committet die Middleware die Session und gibt die Verbindung frei. Dieser Lifecycle erklärt, warum die oben gezeigte `publish`-Aktion keine expliziten Commit- oder Close-Anweisungen benötigt. Die Session-Middleware öffnet die Session, bevor Ihr Code ausgeführt wird, und behandelt anschließend die Commit- bzw. Rollback-Operationen, bevor die Response die View verlässt.

## Pydantic-Validierung

Möglicherweise verwenden Sie plain SQLAlchemy-Modelle, möchten aber dennoch Formulardaten gegen ein Pydantic-Schema validieren, bevor Sie sie speichern. In diesem Fall akzeptiert `starlette_admin.contrib.sqla.ext.pydantic.ModelView` ein Argument `pydantic_model`, um die Validierung gegen dieses Schema auszuführen statt gegen die zugrunde liegenden SQLAlchemy-Spaltentypen:

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

Das Absenden von `full_name="Madonna"` (ein einzelnes Wort) lässt die Methode `validate_full_name` fehlschlagen. Das Create- bzw. Edit-Formular wird dann neu gerendert, wobei der Fehler explizit am Feld `full_name` angehängt ist. Die zugrunde liegende SQLAlchemy-Spalte `String(100)` hat keine solche Regel. Die Einschränkung liegt vollständig im Pydantic-Modell `UserIn`. Das vollständige Beispiel finden Sie unter [examples/11-sqla-pydantic-fastapi](https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi); es enthält auch eine sekundäre View (`PostIn`), die an dasselbe Admin-Panel angehängt ist.

## Vollständiges Arbeitsbeispiel

Hier ist ein vollständiges SQLAlchemy-Beispiel mit starlette-admin. Die lauffähige Version finden Sie unter [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

### 1. Abhängigkeiten installieren

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin sqlalchemy>=2 "fastapi[standard]"
    ```

Das Paket `fastapi[standard]` enthält die FastAPI-CLI, mit der Sie den Entwicklungsserver starten können, indem Sie `fastapi dev` ausführen.

### 2. Die Anwendung erstellen

Speichern Sie den folgenden Code als `main.py`. Dieses Skript verwendet zu Demonstrationszwecken eine lokale SQLite-Datenbank (`blog.db`). Starlette-Admin unterstützt jedoch sowohl synchrone als auch asynchrone Engines für PostgreSQL, MySQL und SQLite.

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

Sie können nun in Ihrem Browser zu [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) navigieren, um das Admin-Dashboard anzusehen und damit zu interagieren.

---

## Was Sie als Nächstes lesen können

* **[Views](../user-guide/views.md)**: Erkunden Sie die Konfigurationsoptionen von `BaseModelView` unabhängig vom Backend.
* [Filter](../user-guide/filters.md): Details zum Filter-Builder und zum URL-Format, das von der Filter-Registry bereitgestellt wird.
* [Views](../user-guide/views.md): Eine umfassende Liste aller `ModelView`-Konfigurationsoptionen (backend-unabhängig).
* [SQLModel](sqlmodel.md): Ein schlanker Wrapper um dieses Backend, der Formularen Pydantic-Validierung hinzufügt.
* [Beanie](beanie.md): Eine Anleitung zur Verwendung derselben `ModelView`-API gegen eine MongoDB-Datenbank.
* [Tortoise ORM](tortoise.md): Das andere relationale Backend, das in starlette-admin integriert ist.
