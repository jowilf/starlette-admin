---
title: Integration eines benutzerdefinierten Backends
description: Erfahren Sie, wie Sie einen benutzerdefinierten Backend-Adapter für starlette-admin
  bauen, um Ihr eigenes ORM oder Ihren API-Datenspeicher mit dem Admin-UI zu verbinden.
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/custom-backend/)
<!-- translation-notice:end -->

# Benutzerdefinierte Backends

`starlette-admin` bietet integrierte Backends für SQLAlchemy, SQLModel, Beanie, MongoEngine und Tortoise ORM an, aber das Admin-Panel ist vollständig storage-agnostisch. Jedes Backend ist einfach eine Unterklasse von `BaseModelView`. Diese Klasse übersetzt Standard-CRUD-Operationen in Befehle, die Ihre jeweilige Datenquelle versteht. Ob Sie eine REST-API, Redis, eine Legacy-Datenbank ohne ORM oder einen leichtgewichtigen Dokumentenspeicher wie TinyDB verwenden, der Implementierungsprozess bleibt identisch.

## Erforderliche Methoden

`BaseModelView` erfordert von Ihnen die Implementierung von sechs abstrakten Methoden. Indem Sie diese sechs Methoden bereitstellen, erben Sie automatisch den vollen Funktionsumfang des Admins: Auflisten, Suchen, Sortieren, Filtern, Paginierung, Erstellen, Bearbeiten, Importieren, Exportieren und Löschen.

```python
from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.filters import FilterGroup
from starlette_admin.views import BaseModelView


class MyBackendView(BaseModelView):
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        ...

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        ...

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        ...

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        ...

    async def create(self, request: Request, data: dict) -> Any:
        ...

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        ...

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ...

```

| Methode | Aufgerufen bei | Rückgabewert |
| --- | --- | --- |
| **`find_all`** | Listenseite, Export | Eine Seite mit Datensätzen, die `q`, `sorts` und `filters` entsprechen |
| **`count`** | Paginierung der Listenseite, Prüfung des Export-Limits | Gesamtzahl der Datensätze, die `q` und `filters` entsprechen |
| **`find_by_pk`** | Detailseite, Bearbeitung, einzelnes Löschen, Zeilenaktionen | Ein einzelner Datensatz oder `None`, falls nicht gefunden |
| **`find_by_pks`** | Massenaktionen, Massenlöschung, Export ausgewählter Datensätze | Eine Sequenz von Datensätzen mit den angegebenen Primärschlüsseln |
| **`create`** | Absenden des Erstellen-Formulars, Import | Der neu erstellte Datensatz |
| **`edit`** | Absenden des Bearbeiten-Formulars | Der aktualisierte Datensatz |
| **`delete`** | Massenlöschung, Löschen einer Zeile | Die Anzahl der gelöschten Datensätze oder `None` |

Das Admin-Panel übernimmt intern das Parsen des Querystrings des Requests (z. B. `?page=2&sort=views__desc&q=fire`). Sie müssen niemals rohe Request-Parameter parsen. Wenn `find_all` oder `count` aufgerufen wird, hat das Admin-Panel die Eingaben bereits verarbeitet:

* **Paginierung** wird in `skip` und `limit` umgewandelt (`skip = (page - 1) * page_size`).
* **Suche** wird als einfacher String `q` bereitgestellt.
* **Sortierung** ist formatiert als priorisierte Liste von `(field_name, direction)`-Tupeln.
* **Filter** werden in einen strukturierten `FilterGroup`-Baum geparst.

Ihre einzige Aufgabe besteht darin, diese strukturierten Argumente in die native Query-Sprache Ihres Backends zu übersetzen.

## View-Key, Anzeigename und Felder

Vor dem Rendern benötigt ein `ModelView` vier Kernattribute, um die Datenstruktur und das Routing zu verstehen:

| Attribut | Zweck |
| --- | --- |
| **`key`** | Eindeutiger URL-Slug (z. B. `/admin/post/list`) und der interne Schlüssel für Event-Abonnements. |
| **`display_name`** / **`menu_label`** | Anzeigenamen für das UI. `display_name` steht im Singular für Formulartitel, während `menu_label` im Plural für Navigation und Listenseiten steht. |
| **`pk_attr`** | Der konkrete Feldname, der einen Datensatz eindeutig identifiziert. |
| **`fields`** | Eine Liste von `BaseField`-Instanzen, die die anzuzeigenden und bearbeitbaren Spalten definiert. |

Integrierte Backends befüllen diese Attribute automatisch durch Introspektion Ihrer Datenbankmodelle. Zum Beispiel liest der SQLAlchemy-`ModelView` die Spalten und den Primärschlüssel des Mappers. Diese Introspektion wird von einer `BaseModelConverter`-Unterklasse übernommen. Diese Konverter verwenden `@converts(...)`-Dekoratoren, um native Spaltentypen auf ihre entsprechenden `BaseField`-Äquivalente abzubilden.

Wenn Sie ein Backend ohne introspektierbares Modell bauen, etwa eine REST-API oder einen einfachen Dictionary-Speicher, müssen Sie diese vier Attribute explizit als Klassenattribute setzen:

```python
class PostView(BaseModelView):
    key = "post"
    display_name = "Post"
    menu_label = "Blog Posts"
    pk_attr = "id"
    fields = [
        IntegerField("id", filters=[]),
        StringField("title"),
        TextAreaField("body"),
        IntegerField("views"),
    ]

```

Das explizite Auflisten der Felder ist der einfachste Ansatz für einmalige Views. Wenn Sie jedoch eine wiederverwendbare `ModelView`-Basisklasse bauen, die für mehrere Datenbankmodelle auf einem benutzerdefinierten Backend gedacht ist, sollten Sie stattdessen einen benutzerdefinierten `BaseModelConverter` schreiben. Implementieren Sie die Methoden `convert()` und `convert_fields_list()`, dekorieren Sie Ihre Typ-Handler mit `@converts(...)` und rufen Sie den Konverter während der Initialisierung auf. So können konkrete Views die Felddefinitionen automatisch erben, entsprechend dem Verhalten der integrierten Backends.

## Filterbäume verarbeiten

Filter werden Ihren Methoden als `FilterGroup` übergeben. Diese Struktur ist ein Baum aus logischen AND/OR-Knoten, der `FilterRule`-Blattobjekte enthält:

```python
@dataclass
class FilterRule:
    field: str
    filter: str         # The slug of the BaseFilter to apply (e.g., "contains", "gte")
    value: Any = None
    value2: Any = None  # Only populated for filters with has_value2 (e.g., "between")

@dataclass
class FilterGroup:
    logic: str = "and"  # Accepts "and" or "or"
    rules: list["FilterGroup | FilterRule"] = field(default_factory=list)

```

Um diesen Baum in eine Datenbankquery zu konvertieren, müssen Sie ihn rekursiv durchlaufen. Für jede `FilterRule` holen Sie die passende konkrete Filterklasse aus Ihrem `FilterRegistry` und rufen deren `apply()`-Methode auf. Bei verschachtelten `FilterGroup`-Knoten gehen Sie rekursiv vor und kombinieren die resultierenden Fragmente mit dem passenden logischen Operator.

Dies ist das `build_query`-Muster, das vom TinyDB-Referenzbeispiel verwendet wird:

```python
def build_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            fragment = build_query(rule, fields_by_name, registry)
        else:
            fragment = _build_rule_fragment(rule, fields_by_name, registry)
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None

    combined = fragments[0]
    for fragment in fragments[1:]:
        combined = (combined | fragment) if group.logic == "or" else (combined & fragment)
    return combined


def _build_rule_fragment(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None, field_name=rule.field, value=rule.value, value2=rule.value2
    )
    return filter_cls().apply(ctx)

```

Die `apply(ctx)`-Methode jedes konkreten Filters erhält ein `FilterApplyContext`-Objekt, das die Query, den Feldnamen und die Werte enthält. Sie gibt ein Query-Fragment zurück, das spezifisch für die Sprache Ihres Backends ist. Da dieser Prozess das Verändern von gemeinsam genutztem Zustand vermeidet, können Sie die resultierenden Regeln sauber kombinieren, unabhängig von Ihrer zugrunde liegenden Datenbankarchitektur.

## Das TinyDB-Referenzbeispiel

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) enthält ein voll lauffähiges Admin-Panel auf Basis von [TinyDB](https://github.com/msiemens/tinydb). TinyDB ist ein Dokumentenspeicher, der Daten in einer lokalen JSON-Datei ablegt. TinyDB eignet sich als ausgezeichneter Referenzpunkt, da es kein ORM besitzt, sodass jede Methode direkt mit dem Datenspeicher interagiert.

### Modelldefinition (`models.py`)

Das Datenmodell ist eine Standard-Python-Dataclass ohne jegliche admin-spezifische Logik:

```python
@dataclass
class Post:
    title: str
    body: str
    tags: list[str]
    views: int = 0
    comments: list[Comment] = field(default_factory=list)
    cover: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "id"}

    @classmethod
    def from_document(cls, doc: Document) -> "Post":
        return cls(**doc, id=doc.doc_id)

    @classmethod
    def search_query(cls, term: str):
        q = Query()
        return (
            q.title.search(term, flags=re.IGNORECASE)
            | q.body.search(term, flags=re.IGNORECASE)
            | q.tags.test(lambda tags: any(re.match(term, tag, re.IGNORECASE) for tag in tags))
        )

```

Die `search_query`-Methode behandelt den Parameter `q`, indem sie eine Volltextsuche über die relevanten Felder generiert.

### Implementierung der View (`view.py`)

Die `PostView`-Implementierung verwendet `_build_query`, um die Suchquery mit dem Filterbaum zu verschmelzen. Sowohl `find_all` als auch `count` stützen sich auf diesen Helper, bevor sie die TinyDB-Suche ausführen:

```python
async def _build_query(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> QueryInstance | None:
    query = None
    if q is not None:
        query = Post.search_query(q)
    if filters is not None and not filters.is_empty():
        fields_by_name = {field.name: field for field in self.get_fields_list(request)}
        filter_query = build_query(filters, fields_by_name, self.get_filter_registry())
        if filter_query is not None:
            query = filter_query if query is None else (query & filter_query)
    return query

async def find_all(
    self,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    sorts: list[tuple[str, str]] | None = None,
    filters: FilterGroup | None = None,
) -> Sequence[Any]:
    query = await self._build_query(request, q, filters)
    docs = self.db.search(query) if query is not None else self.db.all()
    values = [Post.from_document(doc) for doc in docs]
    for sort_by, sort_dir in reversed(sorts or []):
        values.sort(
            key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
            reverse=(sort_dir == "desc"),
        )
    if limit > 0:
        return values[skip : skip + limit]
    return values[skip:]

async def count(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> int:
    query = await self._build_query(request, q, filters)
    return len(self.db.search(query)) if query is not None else len(self.db.all())

```

Da TinyDB keine nativen Sortierfähigkeiten besitzt, wird die Sortierlogik in Python ausgeführt. Das Anwenden der Sortierungen in umgekehrter Reihenfolge erzeugt eine zuverlässige Multi-Key-Sortierung.

Schreiboperationen (`create`, `edit`, `delete`) verändern die Datenbank direkt. Entscheidend ist, dass sie auch die Event-Hooks der View auslösen, wodurch sichergestellt wird, dass Lifecycle-Events korrekt ausgelöst werden:

```python
async def create(self, request: Request, data: dict) -> Any:
    await self.validate_data(data)
    obj = Post(**data)
    await self._emit_before_create(request, data, obj)
    new_id = self.db.insert(obj.to_dict())
    obj = await self.find_by_pk(request, new_id)
    await self._emit_after_create(request, obj)
    return obj

async def delete(self, request: Request, pks: list[Any]) -> int | None:
    ids = list(map(int, pks))
    objs = [Post.from_document(self.db.get(doc_id=i)) for i in ids if self.db.contains(doc_id=i)]
    for obj in objs:
        await self._emit_before_delete(request, await self.get_pk_value(request, obj), obj)
    removed = self.db.remove(doc_ids=ids)
    for obj in objs:
        await self._emit_after_delete(request, await self.get_pk_value(request, obj), obj)
    return len(removed)

```

### Verdrahtung der Anwendung (`app.py`)

Sie benötigen keine spezialisierte `Admin`-Unterklasse. Das Basis-`Admin` funktioniert universell, weil `BaseModelView` alle Backend-Details abstrahiert:

```python
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin
from tinydb import TinyDB
from view import PostView

db = TinyDB(Path(__file__).parent / "db.json")

app = Starlette()
admin = Admin(debug=True, secret_key="123456")
admin.add_view(PostView(db))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

Um diese Implementierung zu testen, führen Sie `uv run app.py` im Beispielverzeichnis aus und navigieren Sie zu `http://localhost:8000/admin/`.

## Benutzerdefinierte Feldfilter

Filter sind eng an die Syntax Ihres jeweiligen Backends gebunden. Eine „contains“-Operation erfordert völlig unterschiedlichen Code in TinyDB, SQL und MongoDB. Jedes benutzerdefinierte Backend muss seine eigenen `BaseFilter`-Unterklassen in einem `FilterRegistry` registrieren und diese über `get_filter_registry()` zurückgeben.

Um einen Filter zu erstellen, leiten Sie von einem Basistyp wie `EqualFilter` oder `ContainsFilter` ab und implementieren die `apply`-Methode:

```python
import re

from starlette_admin.filters import FilterApplyContext
from starlette_admin.filters.string import ContainsFilter
from tinydb import Query
from tinydb.queries import QueryInstance


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return Query()[ctx.field_name].search(re.escape(ctx.value), flags=re.IGNORECASE)

```

Die bewährte Praxis beim Aufbau des Registrys ist es, von `FilterRegistry` zu erben und feldspezifische Methoden mit `@filters(...)` zu dekorieren. Dies ist genau das Muster, das von den mitgelieferten Backends verwendet wird:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterRegistry, filters
from starlette_admin.filters.generic import IsNotNullFilter, IsNullFilter
from starlette_admin.filters.numeric import EqualFilter, GreaterThanFilter, LessThanFilter


class TinyDBFilterRegistry(FilterRegistry):
    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type]:
        # Ensures every field is filterable by null-ness, even without specific registrations.
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type]:
        return [TinyDBContainsFilter, EqualFilter, IsNullFilter, IsNotNullFilter]

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type]:
        return [EqualFilter, GreaterThanFilter, LessThanFilter, IsNullFilter, IsNotNullFilter]


class PostView(BaseModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return TinyDBFilterRegistry()

```

Hat ein Feld keinen passenden Registry-Eintrag und besitzt kein explizites `filters=[]`-Override, ist es nicht filterbar. Das TinyDB-Beispiel lässt das Feld `id` absichtlich mithilfe der `filters=[]`-Override-Technik unfilterbar.

Für dynamische Schemas, bei denen die filterbaren Typen erst zur Laufzeit bekannt sind, stellt `FilterRegistry` eine imperative Methode `register(field_type, *filter_classes)` bereit.

## Lifecycle-Events verwalten

Ihr benutzerdefiniertes Backend besitzt die Methoden `create`, `edit` und `delete` vollständig. Da die `BaseModelView` Ihre Datenquelle nie direkt berührt, müssen Sie sie explizit benachrichtigen, wenn ein Schreibvorgang stattfindet. Unterlassen Sie dies, werden stillschweigend zwei Kernsysteme beschädigt:

1. **Method-Hooks:** `before_create`- und `after_create`-Overrides auf Ihrem `ModelView`.
2. **Event-Subscriber:** Handler, die auf `view.events` oder `admin.events` registriert sind.

Die Benachrichtigung erfolgt durch den Aufruf paarweiser Helper-Methoden, die auf `BaseModelView` definiert sind. Jeder Helper ruft den entsprechenden Method-Hook auf und emittiert ein `AdminEvent`.

| Methode | Pre-Write-Helper | Post-Write-Helper |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

Der Pre-Write-Aufruf akzeptiert das im Speicher befindliche Objekt, das aus den übermittelten Daten konstruiert wurde. Dies bietet Handlern eine letzte Gelegenheit, den Schreibvorgang durch Auslösen einer Exception abzulehnen. Der Post-Write-Aufruf benötigt das persistierte Objekt, wie es aus der Datenbank zurückgelesen wurde. Das erklärt, warum die TinyDB-`create`-Methode den Datensatz erneut abruft, statt das ursprüngliche In-Memory-Objekt zurückzugeben.

Zwei weitere Helper, `_emit_after_create_committed` und `_emit_after_edit_committed`, unterstützen Backends mit Two-Phase-Commits oder Session-Semantik. Überspringen Sie diese vollständig, sofern Ihre Datenbank keine strikte Transaktionsgrenze erzwingt.

Export- und Importoperationen erfordern keine manuelle Event-Verkabelung. Die Klasse `BaseAdmin` behandelt diese Lifecycle-Events automatisch.

---

### Weitere Ressourcen

* **[Views](../user-guide/views.md)**: Erkunden Sie die `BaseModelView`-Konfigurationsoptionen unabhängig vom Backend.
* **[Benutzerdefinierte Filter](https://jowilf.github.io/starlette-admin/advanced/custom-filters/)**: Erfahren Sie, wie Sie benutzerdefinierte Filter von Grund auf schreiben und registrieren.
* **[Events](../advanced/events.md)**: Verstehen Sie die vollständige Event-Subscription-API, einschließlich Method-Hooks, Event-Bus und Ausführungsprioritäten.
