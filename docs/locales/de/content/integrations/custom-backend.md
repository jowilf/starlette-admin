---
title: Eigene Backend-Integration
description: Erfahren Sie, wie Sie einen eigenen Backend-Adapter für starlette-admin
  erstellen, um Ihren eigenen ORM- oder API-Datenspeicher mit der Admin-Oberfläche
  zu verbinden.
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/integrations/custom-backend/)
<!-- translation-notice:end -->

# Eigene Backends

`starlette-admin` bietet integrierte Backends für SQLAlchemy, SQLModel, Beanie, MongoEngine und Tortoise ORM an, doch das Admin-Panel ist vollständig speicheragnostisch. Jedes Backend ist im Kern eine Unterklasse von `BaseModelView`. Diese Klasse übersetzt Standard-CRUD-Operationen in Befehle, die Ihre jeweilige Datenquelle versteht. Ob Sie eine REST-API, Redis, eine Legacy-Datenbank ohne ORM oder einen leichtgewichtigen Dokumentenspeicher wie TinyDB verwenden – der Implementierungsprozess bleibt identisch.

## Erforderliche Methoden

`BaseModelView` verlangt von Ihnen die Implementierung von sechs abstrakten Methoden. Mit diesen sechs Methoden erben Sie automatisch den vollen Funktionsumfang des Admin-Bereichs: Auflisten, Suchen, Sortieren, Filtern, Paginierung, Erstellen, Bearbeiten, Importieren, Exportieren und Löschen.

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

| Methode | Aufgerufen für | Rückgabe |
| --- | --- | --- |
| **`find_all`** | Listenseite, Export | Eine Seite mit Datensätzen, die `q`, `sorts` und `filters` entsprechen |
| **`count`** | Paginierung der Listenseite, Export-Limit-Prüfung | Gesamtzahl der Datensätze, die `q` und `filters` entsprechen |
| **`find_by_pk`** | Detailansicht, Bearbeitung, Einzel-Löschung, Zeilen-Aktionen | Ein einzelner Datensatz oder `None`, falls nicht gefunden |
| **`find_by_pks`** | Massenaktionen, Sammel-Löschung, Export ausgewählter Datensätze | Eine Sequenz von Datensätzen zu den angegebenen Primärschlüsseln |
| **`create`** | Absenden des Erstellungsformulars, Import | Der neu erstellte Datensatz |
| **`edit`** | Absenden des Bearbeitungsformulars | Der aktualisierte Datensatz |
| **`delete`** | Sammel-Löschung, Zeilen-Löschung | Die Anzahl der gelöschten Datensätze oder `None` |

Das Admin-Panel übernimmt intern das Parsen des Query-Strings der Anfrage (z. B. `?page=2&sort=views__desc&q=fire`). Sie müssen niemals rohe Anfrageparameter auswerten. Sobald `find_all` oder `count` aufgerufen wird, hat das Admin-Panel die Eingaben bereits verarbeitet:

* **Paginierung** ist in `skip` und `limit` umgewandelt (`skip = (page - 1) * page_size`).
* **Suche** wird als einfacher String `q` übergeben.
* **Sortierung** ist als priorisierte Liste von `(field_name, direction)`-Tupeln formatiert.
* **Filter** sind in einen strukturierten `FilterGroup`-Baum geparst.

Ihre einzige Aufgabe besteht darin, diese strukturierten Argumente in die native Abfragesprache Ihres Backends zu übersetzen.

## View-Key, Anzeigename und Felder

Vor dem Rendern benötigt ein `ModelView` vier zentrale Attribute, um die Datenstruktur und das Routing zu verstehen:

| Attribut | Zweck |
| --- | --- |
| **`key`** | Eindeutiger URL-Slug (z. B. `/admin/post/list`) und interner Schlüssel für Event-Abonnements. |
| **`display_name`** / **`menu_label`** | Anzeigenamen für die Oberfläche. `display_name` steht in der Singularform für Formulartitel, während `menu_label` in der Pluralform für Navigation und Listenseiten verwendet wird. |
| **`pk_attr`** | Der konkrete Feldname, der einen Datensatz eindeutig identifiziert. |
| **`fields`** | Eine Liste von `BaseField`-Instanzen, die die anzuzeigenden und bearbeitbaren Spalten definiert. |

Die integrierten Backends befüllen diese Attribute automatisch durch Introspektion Ihrer Modelle. Beispielsweise liest das SQLAlchemy-`ModelView` die Spalten und den Primärschlüssel aus dem Mapper aus. Diese Introspektion übernimmt eine `BaseModelConverter`-Unterklasse. Diese Konverter verwenden `@converts(...)`-Decorators, um native Spaltentypen auf ihre entsprechenden `BaseField`-Äquivalente abzubilden.

Beim Bau eines Backends ohne introspektierbares Modell – etwa einer REST-API oder einem einfachen Dictionary-Speicher – müssen Sie diese vier Attribute explizit als Klassenattribute setzen:

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

Das explizite Auflisten der Felder ist der einfachste Ansatz für einmalige Views. Wenn Sie jedoch eine wiederverwendbare `ModelView`-Basisklasse entwickeln, die für mehrere Modelle auf einem eigenen Backend gedacht ist, sollten Sie stattdessen einen eigenen `BaseModelConverter` schreiben. Implementieren Sie die Methoden `convert()` und `convert_fields_list()`, dekorieren Sie Ihre Typ-Handler mit `@converts(...)` und rufen Sie den Konverter während der Initialisierung auf. So erben konkrete Views die Felddefinitionen automatisch – analog zum Verhalten der integrierten Backends.

## Verarbeitung von Filterbäumen

Filter werden Ihren Methoden als `FilterGroup` übergeben. Diese Struktur ist ein Baum aus logischen AND/OR-Knoten, die `FilterRule`-Blattobjekte enthalten:

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

Um diesen Baum in eine Datenbankabfrage umzuwandeln, müssen Sie ihn rekursiv durchlaufen. Für jede `FilterRule` holen Sie die passende konkrete Filterklasse aus Ihrem `FilterRegistry` und rufen deren `apply()`-Methode auf. Bei verschachtelten `FilterGroup`-Knoten rekursieren Sie und kombinieren die resultierenden Fragmente mit dem jeweiligen logischen Operator.

Dies ist das `build_query`-Muster aus dem TinyDB-Referenzbeispiel:

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

Die `apply(ctx)`-Methode jedes konkreten Filters erhält ein `FilterApplyContext`-Objekt mit dem `query`, dem `field name` und den `values`. Sie gibt ein Abfragefragment zurück, das spezifisch für die Abfragesprache Ihres Backends ist. Da dieser Prozess ohne Mutation gemeinsamer Zustände auskommt, lassen sich die resultierenden Regeln unabhängig von Ihrer zugrunde liegenden Datenbankarchitektur sauber kombinieren.

## Das TinyDB-Referenzbeispiel

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) enthält ein vollständig lauffähiges Admin-Panel auf Basis von [TinyDB](https://github.com/msiemens/tinydb). TinyDB ist ein Dokumentenspeicher, der Daten in einer lokalen JSON-Datei ablegt. Es eignet sich hervorragend als Referenz, da es kein ORM besitzt – jede Methode interagiert daher direkt mit dem Datenspeicher.

### Modelldefinition (`models.py`)

Das Datenmodell ist eine gewöhnliche Python-Dataclass ohne admin-spezifische Logik:

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

Die `PostView`-Implementierung nutzt `_build_query`, um die Suchabfrage mit dem Filterbaum zu verschmelzen. Sowohl `find_all` als auch `count` greifen vor der Ausführung der TinyDB-Suche auf diesen Helper zurück:

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

Da TinyDB keine nativen Sortiermöglichkeiten bietet, erfolgt die Sortierlogik in Python. Die Anwendung der Sortierungen in umgekehrter Reihenfolge erzeugt eine zuverlässige Multi-Key-Sortierung.

Schreiboperationen (`create`, `edit`, `delete`) verändern die Datenbank direkt. Entscheidend ist, dass sie zusätzlich die Event-Hooks der View auslösen, wodurch Lifecycle-Events korrekt getriggert werden:

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

Sie benötigen keine spezielle `Admin`-Unterklasse. Das Basis-`Admin` funktioniert universell, da `BaseModelView` sämtliche Backend-Details abstrahiert:

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

Um diese Implementierung zu testen, führen Sie `uv run app.py` im Beispielverzeichnis aus und öffnen Sie `http://localhost:8000/admin/`.

## Eigene Feldfilter

Filter sind eng an die Syntax Ihres jeweiligen Backends gebunden. Eine „contains“-Operation erfordert in TinyDB, SQL und MongoDB völlig unterschiedlichen Code. Jedes eigene Backend muss seine eigenen `BaseFilter`-Unterklassen in einem `FilterRegistry` registrieren und diese über `get_filter_registry()` zurückgeben.

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

Als Best Practice für den Aufbau der Registry gilt, `FilterRegistry` zu subclassen und feldspezifische Methoden mit `@filters(...)` zu dekorieren. Genau dieses Muster verwenden die mitgelieferten Backends:

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

Besitzt ein Feld keinen passenden Registry-Eintrag und verfügt es auch nicht über eine explizite `filters=[]`-Überschreibung, ist es nicht filterbar. Das TinyDB-Beispiel lässt das Feld `id` bewusst mithilfe der `filters=[]`-Technik unfilterbar.

Für dynamische Schemata, bei denen die filterbaren Typen erst zur Laufzeit bekannt sind, stellt `FilterRegistry` eine imperative Methode `register(field_type, *filter_classes)` bereit.

## Verwaltung von Lifecycle-Events

Ihr eigenes Backend besitzt die vollständige Kontrolle über die Methoden `create`, `edit` und `delete`. Da `BaseModelView` nie direkt auf Ihre Datenquelle zugreift, müssen Sie es explizit benachrichtigen, sobald ein Schreibvorgang stattfindet. Andernfalls brechen zwei zentrale Systeme stillschweigend:

1. **Method-Hooks:** `before_create`- und `after_create`-Overrides in Ihrem `ModelView`.
2. **Event-Subscriber:** Handler, die auf `view.events` oder `admin.events` registriert sind.

Die Benachrichtigung erfolgt über paarweise definierte Helper-Methoden auf `BaseModelView`. Jeder Helper ruft den entsprechenden Method-Hook auf und emittiert ein `AdminEvent`.

| Methode | Pre-Write-Helper | Post-Write-Helper |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

Der Pre-Write-Aufruf erhält das im Speicher konstruierte Objekt, das aus den eingereichten Daten erstellt wurde. Dies bietet Handlern eine letzte Gelegenheit, den Schreibvorgang durch Auslösen einer Exception abzulehnen. Der Post-Write-Aufruf verlangt das persistierte Objekt, so wie es aus der Datenbank zurückgelesen wurde. Deshalb ruft die TinyDB-`create`-Methode den Datensatz erneut ab, statt das ursprüngliche In-Memory-Objekt zurückzugeben.

Zwei weitere Helper, `_emit_after_create_committed` und `_emit_after_edit_committed`, unterstützen Backends mit Two-Phase-Commits oder Session-Semantik. Überspringen Sie diese vollständig, sofern Ihre Datenbank keine strikte Transaktionsgrenze erzwingt.

Export- und Import-Operationen erfordern keine manuelle Event-Verdrahtung. Die Klasse `BaseAdmin` behandelt diese Lifecycle-Events automatisch.

---

### Weitere Ressourcen

* **[Views](../user-guide/views.md)**: Erkunden Sie die Konfigurationsoptionen von `BaseModelView` unabhängig vom Backend.
* **[Custom Filters](../advanced/custom-filters.md)**: Erfahren Sie, wie Sie eigene Filter von Grund auf schreiben und registrieren.
* **[Events](../advanced/events.md)**: Verstehen Sie die vollständige Event-Subscription-API, einschließlich Method-Hooks, Event-Bus und Ausführungsprioritäten.
