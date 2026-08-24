---
title: Filtros
description: Añada capacidades de filtrado AND/OR anidadas y complejas a sus vistas
  de administración mediante constructores de consultas que reconocen los tipos.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? warning "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# Filtros

Cada campo de una página de lista puede tener su propio conjunto de operadores de filtro, como `contains`, `between` e `is null`. Sus usuarios combinan estos operadores en un árbol `AND`/`OR` anidado, y usted nunca escribe una consulta de base de datos compleja.

La administración deriva los filtros disponibles a partir del tipo subyacente del campo. Puede reducir, ampliar o reemplazar por completo ese conjunto para cualquier campo.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

Consulte [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) para ver una aplicación ejecutable que cubre los filtros predeterminados, las anulaciones por campo y una subclase personalizada de `BaseFilter`.

Cada campo que incluya en `searchable_fields` obtiene un menú desplegable **Filtros** en la barra de herramientas de la lista. Desde allí, los usuarios combinan cualquier cantidad de filtros para encontrar las filas que necesitan.

## Cómo funciona el constructor de filtros

Al seleccionar el botón **Filtros** se abre un formulario desplegable donde los usuarios construyen sus consultas:

* **Añadir filtro**: añade una fila de condición. El usuario elige un campo, selecciona un operador de entre los filtros disponibles para ese campo y proporciona un valor. La entrada se adapta al operador: un cuadro de texto simple para `contains`, dos cuadros para `between` y ninguna entrada para `is null`.
* **Añadir grupo**: anida un subformulario con su propio selector `AND`/`OR`. Úselo para construir condiciones como `A AND (B OR C)`.
* **Coincidir con todos/cualquiera de los siguientes**: define si el nivel actual usa lógica `AND` u `OR`.
* **Aplicar filtros**: envía el formulario como una solicitud `GET`. La administración serializa todo el árbol de filtros en un único parámetro de consulta `filter`, descrito en [El formato de URL del filtro](#el-formato-de-url-del-filtro).
* **Filtros activos**: cada filtro activo aparece como una etiqueta extraíble sobre la tabla. Al seleccionar la `×` se vuelve a enviar la lista sin esa regla. Un grupo anidado se contrae en una sola etiqueta que los usuarios eliminan como un todo.

!!! tip
    Como todo el estado del filtro reside en la URL, una lista filtrada se puede compartir. Sus usuarios pueden marcar la página como favorita y enviar el enlace a un colega.

## Anular los filtros de un campo específico

Cuando los filtros predeterminados son demasiado amplios, o si necesita algo más específico, pase el argumento `filters=` a un campo para reemplazar su conjunto predeterminado.

Puede reducir la lista a los operadores que le interesan, ampliarla con un filtro personalizado o añadir operadores a un campo que de forma predeterminada solo tiene comprobaciones básicas de nulos, como `TagsField`:

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

Encierre un valor entre comillas cuando contenga un espacio o un paréntesis: `name__eq="quoted value"`. Un valor de lista para un filtro de selección múltiple como «is one of» está separado por comas y no necesita comillas: `status__in=ACTIVE,OUT_OF_STOCK`.

Cuando la URL contiene una cadena `filter` no válida, como un campo desconocido, un operador no disponible o un valor no analizable, la aplicación devuelve un error `HTTP 400` en lugar de descartar silenciosamente parte de la condición.

!!! important
    Solo los campos que incluya en `searchable_fields` reciben filtros. Si deja `searchable_fields` sin definir, todos los campos los reciben.


## Referencia de filtros integrados

La siguiente tabla enumera todos los filtros disponibles de forma predeterminada, el slug de URL que aparece en un enlace guardado y el tipo de valor que espera cada uno. Los filtros marcados como «dos valores» requieren tanto un `value` como un `value2` en la URL, por ejemplo `between=2026-01-01..2026-01-31`.

| Filtro | Slug | Tipo de valor | ¿Dos valores? |
| --- | --- | --- | --- |
| Contiene | `contains` | texto |  |
| No contiene | `not_contains` | texto |  |
| Empieza por | `startswith` | texto |  |
| Termina en | `endswith` | texto |  |
| Igual | `eq` | texto, número, fecha, fecha y hora u hora |  |
| Distinto | `neq` | texto o número |  |
| Es nulo | `is_null` | *(ninguno)* |  |
| No es nulo | `is_not_null` | *(ninguno)* |  |
| Mayor que | `gt` | número |  |
| Menor que | `lt` | número |  |
| Mayor o igual que | `gte` | número |  |
| Menor o igual que | `lte` | número |  |
| Entre | `between` | número, fecha, fecha y hora u hora | ✓ |
| Está en el pasado | `in_past` | *(ninguno)* |  |
| Está en el futuro | `in_future` | *(ninguno)* |  |
| Es verdadero | `is_true` | *(ninguno)* |  |
| Es falso | `is_false` | *(ninguno)* |  |
| Está entre | `in` | lista separada por comas |  |
| No está entre | `not_in` | lista separada por comas |  |

Si necesita un filtro para un tipo de dato que los integrados no cubren, como un campo JSON o un punto geográfico, consulte [Filtros personalizados](../advanced/custom-filters.md) para escribir una subclase de `BaseFilter` y registrarla globalmente o por instancia de campo.

---

**¿Qué sigue?**

* **[Filtros personalizados](../advanced/custom-filters.md):** escriba y registre una subclase de `BaseFilter`.
* **[Acciones](actions.md):** añada acciones por lotes y acciones de fila a sus páginas de lista.
* **[Vistas](views.md):** obtenga más información sobre `searchable_fields` y el resto de la configuración de la página de lista.
