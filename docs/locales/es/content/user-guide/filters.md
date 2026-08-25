---
title: Filtros
description: Añada capacidades de filtrado AND/OR anidadas y complejas a sus vistas
  de administración mediante constructores de consultas que reconocen los tipos.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# Filtros

Cada campo de una página de lista puede tener su propio conjunto de operadores de filtrado, como `contains`, `between` e `is null`. Sus usuarios combinan estos operadores en un árbol `AND`/`OR` anidado, y usted nunca escribe una consulta de base de datos compleja.

La interfaz de administración deduce los filtros disponibles a partir del tipo subyacente del campo. Puede reducir, ampliar o reemplazar por completo ese conjunto para cualquier campo.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

Consulte [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) para ver una aplicación ejecutable que cubre los filtros predeterminados, las anulaciones por campo y una subclase personalizada de `BaseFilter`.

Cada campo que incluya en `searchable_fields` obtiene un menú desplegable **Filters** en la barra de herramientas de la lista. Desde allí, los usuarios combinan cualquier cantidad de filtros para encontrar las filas que necesitan.

## Cómo funciona el constructor de filtros

Al seleccionar el botón **Filters** se abre un formulario desplegable donde los usuarios construyen sus consultas:

* **Add filter**: Añade una fila de condición. El usuario elige un campo, selecciona un operador entre los filtros disponibles de ese campo y proporciona un valor. La entrada se adapta al operador: un cuadro de texto simple para `contains`, dos cuadros para `between` y ninguna entrada para `is null`.
* **Add group**: Anida un subformulario con su propio selector `AND`/`OR`. Úselo para construir condiciones como `A AND (B OR C)`.
* **Match all/any of the following**: Establece si el nivel actual usa lógica `AND` u `OR`.
* **Apply filters**: Envía el formulario como una solicitud `GET`. La interfaz de administración serializa todo el árbol de filtros en un único parámetro de consulta `filter`, descrito en [El formato de URL del filtro](#el-formato-de-url-del-filtro).
* **Active filters**: Cada filtro activo aparece como una píldora eliminable sobre la tabla. Al seleccionar la `×`, se vuelve a enviar la lista sin esa regla. Un grupo anidado se contrae en una sola píldora que los usuarios eliminan en su conjunto.

!!! tip
    Como todo el estado del filtro reside en la URL, una lista filtrada se puede compartir. Sus usuarios pueden guardar la página en marcadores y enviar el enlace a un colega.

## Anular los filtros de un campo específico {#overriding-filters-for-a-specific-field}

Cuando los filtros predeterminados son demasiado amplios, o necesita algo más específico, pase el argumento `filters=` a un campo para reemplazar su conjunto predeterminado.

Puede reducir la lista a los operadores que le interesan, ampliarla con un filtro personalizado o añadir operadores a un campo que por defecto solo tiene comprobaciones básicas de nulos, como `TagsField`:

```python
from enum import Enum

from starlette_admin import (
    DateTimeField,
    DecimalField,
    EnumField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.sqla import ModelView

# Import the concrete filter implementations for your specific backend
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
    NumericEqualFilter,
)


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class ProductView(ModelView):
    fields = [
        "id",
        StringField("name"),  # Uses the default filter set, no override needed
        EnumField("status", enum=ProductStatus),  # Uses the default filter set
        DecimalField(
            "price",
            # Narrowed down to just 3 of the 9 default numeric filters
            filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter],
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

!!! important "Importe los filtros desde su backend"
    Las clases de filtro que pase a `filters=` deben ser las implementaciones concretas para su backend de base de datos: `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters` o `.tortoise.filters`. Importe desde el módulo `filters` de su backend, no desde `starlette_admin.filters`.

## El formato de URL del filtro

El constructor de filtros serializa su estado en el parámetro de consulta `filter` como una cadena compacta.

El formato es `field__operator` para un filtro sin valores, `field__operator=value` para un valor único y `field__operator=value..value2` para un filtro de dos valores como `between`. Las reglas se unen con `AND` u `OR`, y los paréntesis anidan un grupo:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Envuelva un valor entre comillas cuando contenga un espacio o un paréntesis: `name__eq="quoted value"`. Un valor de lista para un filtro de selección múltiple como `is one of` está separado por comas y no necesita comillas: `status__in=ACTIVE,OUT_OF_STOCK`.

Cuando la URL contiene una cadena `filter` no válida, como un campo desconocido, un operador no disponible o un valor no analizable, la aplicación devuelve un error `HTTP 400` en lugar de descartar silenciosamente parte de la condición.

!!! important
    Solo los campos que incluya en `searchable_fields` reciben filtros. Si deja `searchable_fields` sin establecer, todos los campos los reciben.


## Referencia de filtros integrados

La siguiente tabla enumera cada filtro disponible de forma predeterminada, el slug de URL que aparece en un enlace guardado en marcadores y el tipo de valor que espera cada uno. Los filtros marcados como «dos valores» necesitan tanto un `value` como un `value2` en la URL, por ejemplo `between=2026-01-01..2026-01-31`.

| Filter | Slug | Value type | Two values? |
| --- | --- | --- | --- |
| Contains | `contains` | text |  |
| Does not contain | `not_contains` | text |  |
| Starts with | `startswith` | text |  |
| Ends with | `endswith` | text |  |
| Equal | `eq` | text, number, date, datetime, or time |  |
| Not equal | `neq` | text or number |  |
| Is null | `is_null` | *(none)* |  |
| Is not null | `is_not_null` | *(none)* |  |
| Greater than | `gt` | number |  |
| Less than | `lt` | number |  |
| Greater than or equal | `gte` | number |  |
| Less than or equal | `lte` | number |  |
| Between | `between` | number, date, datetime, or time | ✓ |
| Is in the past | `in_past` | *(none)* |  |
| Is in the future | `in_future` | *(none)* |  |
| Is true | `is_true` | *(none)* |  |
| Is false | `is_false` | *(none)* |  |
| Is one of | `in` | comma-separated list |  |
| Is not one of | `not_in` | comma-separated list |  |

Si necesita un filtro para un tipo de dato que los filtros integrados no cubren, como un campo JSON o un punto geográfico, consulte [Filtros personalizados](../advanced/custom-filters.md) para escribir una subclase de `BaseFilter` y registrarla globalmente o por instancia de campo.

---

**¿Qué sigue?**

* **[Filtros personalizados](../advanced/custom-filters.md):** Escriba y registre una subclase de `BaseFilter`.
* **[Acciones](actions.md):** Añada acciones masivas y por fila a sus páginas de listas.
* **[Vistas](views.md):** Obtenga más información sobre `searchable_fields` y el resto de la configuración de la página de listas.
