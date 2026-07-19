# Custom Backends

`starlette-admin` provides built-in backends for SQLAlchemy, SQLModel, Beanie, and MongoEngine, but the admin panel is entirely storage-agnostic. Every backend is simply a subclass of `BaseModelView`. This class translates standard CRUD operations into commands your specific data source understands. Whether you are using a REST API, Redis, a legacy database without an ORM, or a lightweight document store like TinyDB, the implementation process remains identical.

## Required Methods

`BaseModelView` requires you to implement six abstract methods. By providing these six methods, you automatically inherit the admin's full suite of features: listing, searching, sorting, filtering, pagination, creation, editing, importing, exporting, and deletion.

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

| Method | Called For | Returns |
| --- | --- | --- |
| **`find_all`** | List page, export | A page of records matching `q`, `sorts`, and `filters` |
| **`count`** | List page pagination, export cap check | Total record count matching `q` and `filters` |
| **`find_by_pk`** | Detail, edit, single delete, row actions | A single record, or `None` if not found |
| **`find_by_pks`** | Bulk actions, bulk delete, export-selected | A sequence of records matching the provided primary keys |
| **`create`** | Create form submission, import | The newly created record |
| **`edit`** | Edit form submission | The updated record |
| **`delete`** | Bulk delete, row delete | The number of deleted records, or `None` |

The admin handles parsing the request's query string (like `?page=2&sort=views__desc&q=fire`) internally. You will never need to parse raw request parameters. By the time `find_all` or `count` is called, the admin has already processed the inputs:

* **Pagination** is converted into `skip` and `limit` (`skip = (page - 1) * page_size`).
* **Search** is provided as the plain string `q`.
* **Sorting** is formatted as a prioritized list of `(field_name, direction)` tuples.
* **Filters** are parsed into a structured `FilterGroup` tree.

Your only task is to translate these structured arguments into your backend's native query language.

## View Key, Display Name, and Fields

Before rendering, a `ModelView` requires four core attributes to understand the data shape and routing:

| Attribute | Purpose |
| --- | --- |
| **`key`** | Unique URL slug (e.g., `/admin/post/list`) and the internal key for event subscriptions. |
| **`display_name`** / **`menu_label`** | Display names for the UI. `display_name` is singular for form titles, while `menu_label` is plural for navigation and list pages. |
| **`pk_attr`** | The specific field name that uniquely identifies a record. |
| **`fields`** | A list of `BaseField` instances defining the columns to display and edit. |

Built-in backends populate these attributes automatically by introspecting your models. For example, the SQLAlchemy `ModelView` reads the mapper's columns and primary key. This introspection is handled by a `BaseModelConverter` subclass. These converters use `@converts(...)` decorators to map native column types to their corresponding `BaseField` equivalents.

When building a backend without an introspectable model, such as a REST API or a plain dictionary store, you must set these four attributes explicitly as class attributes:

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

Explicitly listing fields is the simplest approach for one-off views. However, if you are building a reusable `ModelView` base class designed for multiple models on a custom backend, you should write a custom `BaseModelConverter` instead. Implement the `convert()` and `convert_fields_list()` methods, decorate your type handlers with `@converts(...)`, and invoke the converter during initialization. This allows concrete views to inherit field definitions automatically, matching the behavior of the built-in backends.

## Processing Filter Trees

Filters are passed to your methods as a `FilterGroup`. This structure is a tree of logical AND/OR nodes containing `FilterRule` leaf objects:

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

To convert this tree into a database query, you must walk it recursively. For each `FilterRule`, retrieve the matching concrete filter class from your `FilterRegistry` and call its `apply()` method. For nested `FilterGroup` nodes, recurse and combine the resulting fragments using the appropriate logical operator.

This is the `build_query` pattern used by the TinyDB reference example:

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

The `apply(ctx)` method on each concrete filter receives a `FilterApplyContext` object containing the `query`, `field name`, and `values`. It returns a query fragment specific to your backend language. Because this process avoids mutating shared state, you can cleanly combine the resulting rules regardless of your underlying database architecture.

## The TinyDB Reference Example

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) contains a fully runnable admin panel backed by [TinyDB](https://github.com/msiemens/tinydb). TinyDB is a document store that saves data to a local JSON file. It serves as an excellent reference point because it lacks an ORM, meaning every method interacts directly with the data store.

### Model Definition (`models.py`)

The data model is a standard Python dataclass without any admin-specific logic:

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

The `search_query` method handles the `q` parameter by generating a full-text search across relevant fields.

### View Implementation (`view.py`)

The `PostView` implementation uses `_build_query` to merge the search query with the filter tree. Both `find_all` and `count` rely on this helper before executing the TinyDB search:

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

Because TinyDB lacks native sorting capabilities, the sorting logic executes in Python. Applying sorts in reverse order creates a reliable multi-key sort.

Write operations (`create`, `edit`, `delete`) modify the database directly. Crucially, they also fire the view's event hooks, ensuring lifecycle events trigger correctly:

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

### Application Wiring (`app.py`)

You do not need a specialized `Admin` subclass. The base `Admin` works universally because `BaseModelView` abstracts all backend details:

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

To test this implementation, run `uv run app.py` from the example directory and navigate to `http://localhost:8000/admin/`.

## Custom Field Filters

Filters are deeply tied to your specific backend syntax. A "contains" operation requires entirely different code in TinyDB, SQL, and MongoDB. Each custom backend must register its own `BaseFilter` subclasses in a `FilterRegistry` and return them via `get_filter_registry()`.

To create a filter, subclass a base type like `EqualFilter` or `ContainsFilter` and implement the `apply` method:

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

The best practice for building the registry is to subclass `FilterRegistry` and decorate field-specific methods with `@filters(...)`. This is the exact pattern used by the shipped backends:

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

If a field has no matching registry entry and lacks an explicit `filters=[]` override, it will not be filterable. The TinyDB example intentionally leaves the `id` field unfilterable using the `filters=[]` override technique.

For dynamic schemas where filterable types are unknown until runtime, `FilterRegistry` provides an imperative `register(field_type, *filter_classes)` method.

## Managing Lifecycle Events

Your custom backend completely owns the `create`, `edit`, and `delete` methods. Because the `BaseModelView` never touches your data source directly, you must explicitly notify it when a write occurs. Failing to do so breaks two core systems silently:

1. **Method hooks:** `before_create` and `after_create` overrides on your `ModelView`.
2. **Event subscribers:** Handlers registered on `view.events` or `admin.events`.

Notification is handled by calling paired helper methods defined on `BaseModelView`. Each helper invokes the corresponding method hook and emits an `AdminEvent`.

| Method | Pre-Write Helper | Post-Write Helper |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

The pre-write call accepts the in-memory object constructed from the submitted data. This provides a final opportunity for handlers to reject the write by raising an exception. The post-write call requires the persisted object as read back from the database. This explains why the TinyDB `create` method re-fetches the record instead of returning the initial in-memory object.

Two additional helpers, `_emit_after_create_committed` and `_emit_after_edit_committed`, support backends with two-phase commits or session semantics. Skip these completely unless your database enforces a strict transaction boundary.

Export and import operations do not require manual event wiring. The `BaseAdmin` class handles these lifecycle events automatically.

---

### Additional Resources

* **[Views](../user-guide/views.md)**: Explore `BaseModelView` configuration options independent of the backend.
* **[Custom Filters](../advanced/custom-filters.md)**: Learn how to write and register custom filters from scratch.
* **[Events](../advanced/events.md)**: Understand the full event subscription API, including method hooks, the event bus, and execution priorities.