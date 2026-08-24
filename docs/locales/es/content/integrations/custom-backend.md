---
title: Integración de un backend personalizado
description: Aprenda a construir un adaptador de backend personalizado para starlette-admin
  y conectar su propio ORM o almacén de datos basado en API a la interfaz de administración.
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/integrations/custom-backend/)
<!-- translation-notice:end -->

# Backends personalizados

`starlette-admin` proporciona backends integrados para SQLAlchemy, SQLModel, Beanie, MongoEngine y Tortoise ORM, pero el panel de administración es completamente agnóstico respecto al almacenamiento. Cada backend es simplemente una subclase de `BaseModelView`. Esta clase traduce las operaciones CRUD estándar en comandos que su fuente de datos específica entiende. Ya sea que utilice una API REST, Redis, una base de datos heredada sin ORM o un almacén de documentos ligero como TinyDB, el proceso de implementación sigue siendo idéntico.

## Métodos requeridos

`BaseModelView` requiere que implemente seis métodos abstractos. Al proporcionar estos seis métodos, hereda automáticamente todo el conjunto de características del panel de administración: listado, búsqueda, ordenamiento, filtrado, paginación, creación, edición, importación, exportación y eliminación.

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

| Método | Se invoca para | Devuelve |
| --- | --- | --- |
| **`find_all`** | Página de lista, exportación | Una página de registros que coinciden con `q`, `sorts` y `filters` |
| **`count`** | Paginación de la página de lista, verificación del límite de exportación | El número total de registros que coinciden con `q` y `filters` |
| **`find_by_pk`** | Detalle, edición, eliminación individual, acciones de fila | Un único registro, o `None` si no se encuentra |
| **`find_by_pks`** | Acciones masivas, eliminación masiva, exportación de selección | Una secuencia de registros que coinciden con las claves primarias proporcionadas |
| **`create`** | Envío del formulario de creación, importación | El registro recién creado |
| **`edit`** | Envío del formulario de edición | El registro actualizado |
| **`delete`** | Eliminación masiva, eliminación de fila | El número de registros eliminados, o `None` |

El panel de administración se encarga internamente de analizar la cadena de consulta de la solicitud (como `?page=2&sort=views__desc&q=fire`). Nunca necesitará analizar parámetros crudos de la solicitud. Para cuando se invoca `find_all` o `count`, el panel ya ha procesado las entradas:

* **La paginación** se convierte en `skip` y `limit` (`skip = (page - 1) * page_size`).
* **La búsqueda** se proporciona como la cadena simple `q`.
* **El ordenamiento** se formatea como una lista priorizada de tuplas `(field_name, direction)`.
* **Los filtros** se analizan en un árbol estructurado `FilterGroup`.

Su única tarea consiste en traducir estos argumentos estructurados al lenguaje de consulta nativo de su backend.

## Clave de vista, nombre visible y campos

Antes de renderizar, una `ModelView` requiere cuatro atributos fundamentales para comprender la forma de los datos y el enrutamiento:

| Atributo | Propósito |
| --- | --- |
| **`key`** | Slug único de URL (por ejemplo, `/admin/post/list`) y clave interna para las suscripciones a eventos. |
| **`display_name`** / **`menu_label`** | Nombres visibles para la interfaz. `display_name` es singular para los títulos de los formularios, mientras que `menu_label` es plural para la navegación y las páginas de lista. |
| **`pk_attr`** | El nombre específico del campo que identifica de manera única un registro. |
| **`fields`** | Una lista de instancias de `BaseField` que define las columnas a mostrar y editar. |

Los backends integrados rellenan estos atributos automáticamente mediante introspección de sus modelos. Por ejemplo, la `ModelView` de SQLAlchemy lee las columnas y la clave primaria del mapper. Esta introspección la gestiona una subclase de `BaseModelConverter`. Estos convertidores utilizan decoradores `@converts(...)` para mapear los tipos de columna nativos a sus equivalentes `BaseField` correspondientes.

Al construir un backend sin un modelo introspectable, como una API REST o un almacén de diccionarios simple, debe establecer estos cuatro atributos explícitamente como atributos de clase:

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

Listar los campos explícitamente es el enfoque más sencillo para vistas únicas. Sin embargo, si está construyendo una clase base `ModelView` reutilizable diseñada para múltiples modelos sobre un backend personalizado, debería escribir en su lugar un `BaseModelConverter` personalizado. Implemente los métodos `convert()` y `convert_fields_list()`, decore sus manejadores de tipos con `@converts(...)` e invoque el convertidor durante la inicialización. Esto permite que las vistas concretas hereden automáticamente las definiciones de campos, replicando el comportamiento de los backends integrados.

## Procesamiento de árboles de filtros

Los filtros se pasan a sus métodos como un `FilterGroup`. Esta estructura es un árbol de nodos lógicos AND/OR que contiene objetos hoja `FilterRule`:

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

Para convertir este árbol en una consulta de base de datos, debe recorrerlo recursivamente. Para cada `FilterRule`, obtenga la clase de filtro concreta correspondiente de su `FilterRegistry` e invoque su método `apply()`. Para los nodos `FilterGroup` anidados, recurra y combine los fragmentos resultantes utilizando el operador lógico apropiado.

Este es el patrón `build_query` utilizado por el ejemplo de referencia de TinyDB:

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

El método `apply(ctx)` de cada filtro concreto recibe un objeto `FilterApplyContext` que contiene la `query`, el nombre del campo y los valores. Devuelve un fragmento de consulta específico del lenguaje de su backend. Dado que este proceso evita mutar estado compartido, puede combinar limpiamente las reglas resultantes independientemente de la arquitectura de su base de datos subyacente.

## El ejemplo de referencia de TinyDB

[`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) contiene un panel de administración completamente ejecutable respaldado por [TinyDB](https://github.com/msiemens/tinydb). TinyDB es un almacén de documentos que guarda los datos en un archivo JSON local. Constituye un excelente punto de referencia porque carece de un ORM, lo que significa que cada método interactúa directamente con el almacén de datos.

### Definición del modelo (`models.py`)

El modelo de datos es una dataclass estándar de Python sin ninguna lógica específica de administración:

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

El método `search_query` gestiona el parámetro `q` generando una búsqueda de texto completo sobre los campos relevantes.

### Implementación de la vista (`view.py`)

La implementación de `PostView` utiliza `_build_query` para fusionar la consulta de búsqueda con el árbol de filtros. Tanto `find_all` como `count` dependen de este helper antes de ejecutar la búsqueda en TinyDB:

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

Dado que TinyDB carece de capacidades nativas de ordenamiento, la lógica de ordenamiento se ejecuta en Python. Aplicar los ordenamientos en orden inverso produce un ordenamiento confiable por múltiples claves.

Las operaciones de escritura (`create`, `edit`, `delete`) modifican la base de datos directamente. Es fundamental que también disparen los hooks de eventos de la vista, garantizando así que los eventos del ciclo de vida se activen correctamente:

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

### Cableado de la aplicación (`app.py`)

No necesita una subclase especializada de `Admin`. La clase base `Admin` funciona universalmente porque `BaseModelView` abstrae todos los detalles del backend:

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

Para probar esta implementación, ejecute `uv run app.py` desde el directorio del ejemplo y navegue a `http://localhost:8000/admin/`.

## Filtros de campo personalizados

Los filtros están profundamente ligados a la sintaxis específica de su backend. Una operación «contains» requiere código completamente distinto en TinyDB, SQL y MongoDB. Cada backend personalizado debe registrar sus propias subclases de `BaseFilter` en un `FilterRegistry` y devolverlas mediante `get_filter_registry()`.

Para crear un filtro, derive una subclase de un tipo base como `EqualFilter` o `ContainsFilter` e implemente el método `apply`:

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

La mejor práctica para construir el registro consiste en derivar una subclase de `FilterRegistry` y decorar los métodos específicos por tipo de campo con `@filters(...)`. Este es exactamente el patrón utilizado por los backends incluidos:

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

Si un campo no tiene una entrada coincidente en el registro y carece de una anulación explícita `filters=[]`, no será filtrable. El ejemplo de TinyDB deja intencionalmente el campo `id` sin filtrado mediante la técnica de anulación `filters=[]`.

Para esquemas dinámicos donde los tipos filtrables no se conocen hasta el tiempo de ejecución, `FilterRegistry` proporciona un método imperativo `register(field_type, *filter_classes)`.

## Gestión de eventos del ciclo de vida

Su backend personalizado posee por completo los métodos `create`, `edit` y `delete`. Dado que `BaseModelView` nunca accede directamente a su fuente de datos, debe notificarle explícitamente cuando ocurra una escritura. No hacerlo rompe silenciosamente dos sistemas fundamentales:

1. **Hooks de método:** las anulaciones `before_create` y `after_create` en su `ModelView`.
2. **Suscriptores de eventos:** los manejadores registrados en `view.events` o `admin.events`.

La notificación se realiza invocando pares de métodos helper definidos en `BaseModelView`. Cada helper invoca el hook de método correspondiente y emite un `AdminEvent`.

| Método | Helper previo a la escritura | Helper posterior a la escritura |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

La llamada previa a la escritura acepta el objeto en memoria construido a partir de los datos enviados. Esto ofrece una última oportunidad para que los manejadores rechacen la escritura lanzando una excepción. La llamada posterior a la escritura requiere el objeto persistido tal como se leyó de vuelta desde la base de datos. Esto explica por qué el método `create` de TinyDB vuelve a obtener el registro en lugar de devolver el objeto inicial en memoria.

Dos helpers adicionales, `_emit_after_create_committed` y `_emit_after_edit_committed`, dan soporte a backends con confirmaciones en dos fases o semántica de sesión. Omita estos por completo a menos que su base de datos imponga un límite transaccional estricto.

Las operaciones de exportación e importación no requieren cableado manual de eventos. La clase `BaseAdmin` gestiona automáticamente estos eventos del ciclo de vida.

---

### Recursos adicionales

* **[Views](../user-guide/views.md)**: Explore las opciones de configuración de `BaseModelView` independientes del backend.
* **[Custom Filters](../advanced/custom-filters.md)**: Aprenda a escribir y registrar filtros personalizados desde cero.
* **[Events](../advanced/events.md)**: Comprenda la API completa de suscripción a eventos, incluyendo los hooks de método, el bus de eventos y las prioridades de ejecución.
