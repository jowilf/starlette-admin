---
title: Filtros personalizados
description: Amplíe el constructor de consultas integrado creando filtros y operadores
  de base de datos personalizados en starlette-admin.
source_hash: ac118a53b1d95372b17388cb1ce13241e53cd4b2983158208affa0fedb2e2446
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/advanced/custom-filters/)
<!-- translation-notice:end -->

# Filtros personalizados

Cree una subclase de `BaseFilter` cuando necesite un operador que el conjunto integrado no cubre: una comprobación específica del dominio como "_es divisible por_", una condición calculada como "_creado este mes_", o soporte para un tipo de campo que el registro predeterminado omite. Esta página explica cómo funciona internamente un filtro y muestra las dos formas de registrarlo: ya sea creando una subclase del `FilterRegistry` de su backend para cubrir todos los tipos de campo coincidentes, o pasando el filtro a la lista `filters=` de un solo campo. Para los detalles del día a día, incluidos los filtros predeterminados por tipo de campo, las anulaciones manuales y el formato de URL, consulte la [Guía de filtros](../user-guide/filters.md).

## La interfaz `BaseFilter`

Todos los filtros, ya sean integrados o personalizados, implementan dos métodos:

```python
from typing import Any
from starlette_admin.filters.base import BaseFilter, FilterApplyContext, FilterDataType


class MyFilter(BaseFilter):
    name = "my_filter"
    label = "My filter"
    data_type = FilterDataType.STRING

    def parse_value(self, raw: str) -> Any:
        """Convert the raw string from the URL into the value apply() expects.

        Raise FilterValidationError if the value isn't acceptable.
        """
        return raw

    def apply(self, ctx: FilterApplyContext) -> Any:
        """Return a query fragment for this filter's condition."""
        raise NotImplementedError()
```

* **`parse_value(raw)`** convierte la cadena sin procesar de la URL al tipo que espera `apply()`, como un `Decimal`, una `date` o una lista. La implementación predeterminada pasa la cadena sin cambios, lo cual es adecuado para filtros `STRING` y `ENUM`, pero no para datos numéricos o temporales. También es su punto de validación: lance `FilterValidationError` para valores que se analizan pero siguen siendo inaceptables, como entradas fuera de rango o mal formadas.
* **`apply(ctx)`** es el único método abstracto. Recibe un `FilterApplyContext` que contiene `query`, `field_name`, `value`, `value2`, `request` y `view`, y devuelve un fragmento de consulta para su backend.

## Cómo se analizan los valores sin procesar de la URL

Cada parámetro de URL es una cadena, por lo que tanto `price__gt=50` como `created_at__eq=2026-01-01` llegan como texto sin procesar. Antes de que se ejecute `apply()`, `parse_value()` convierte esa cadena en un objeto de Python que coincide con el `data_type` del filtro:

```python
def _parse_number(raw: Any) -> int | float:
    text = str(raw).strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        raise FilterValidationError(f"{raw!r} is not a valid number") from None


class GreaterThanFilter(BaseFilter):
    name = "gt"
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)
```

Así, `?filter=price__gt=50` y `?filter=price__gt=50.5` llegan a `GreaterThanFilter.apply()` como números de Python (`50` como `int`, `50.5` como `float`) en lugar de las cadenas `"50"` y `"50.5"`. `apply()` pasa ese valor analizado directamente al objeto de consulta, y el driver de la base de datos gestiona la coerción final contra el tipo real de la columna, como `Decimal` o `Numeric`.

| `data_type` | Valor de ejemplo en la URL | Valor de Python analizado | Analizado por |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number` (intenta `int()` y recurre a `float()`) |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal` usando `date.fromisoformat()` |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal` usando `datetime.fromisoformat()` |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal` usando `time.fromisoformat()` |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array` (divide por comillas no entrecomilladas) |
| `string`, `enum` | `admin` | `"admin"` | Predeterminado de `BaseFilter.parse_value` (se pasa sin cambios) |
| `none` | *(ningún valor en la URL)* | *(nunca se llama)* | N/A |

Cuando un valor no se puede analizar, como `price__gt=abc` o `created_at__eq=not-a-date`, `parse_value()` lanza una `FilterValidationError`. El manejador de solicitudes la captura y devuelve `HTTP 400` antes de ejecutar cualquier consulta a la base de datos:

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

Los filtros sin valor, aquellos con `data_type=none` como `is_null`, `is_true` o `in_past`, omiten este paso. `parse_value` nunca se ejecuta para ellos, razón por la cual `field__is_null` no necesita `=valor` en la URL: no hay ninguna cadena de entrada que convertir.

## Poner un filtro personalizado a disposición

Puede registrar un filtro personalizado en una vista de dos maneras. Elija la que coincida con el alcance que desea.

### Por instancia de campo (alcance reducido)

Pase el filtro a la lista `filters=` del campo objetivo, ya sea junto con los valores predeterminados o en lugar de ellos. Consulte [Anular filtros para un campo específico](../user-guide/filters.md#anular-los-filtros-de-un-campo-especifico) para ver el mismo patrón con filtros integrados. Utilice esta opción cuando el filtro solo tenga sentido para un campo.

### En todo el registro (todos los tipos de campo coincidentes)

Cada backend incluye una subclase de `FilterRegistry`: `SqlaFilterRegistry` para SQLAlchemy, `BeanieFilterRegistry` para Beanie, `MongoEngineFilterRegistry` para MongoEngine y `TortoiseFilterRegistry` para Tortoise ORM. Cada uno define los filtros predeterminados para un tipo de campo admitido en un método decorado con `@filters(FieldType, ...)`:

```python
# starlette_admin/contrib/sqla/filters.py
class SqlaFilterRegistry(FilterRegistry):
    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ContainsFilter,
            NotContainsFilter,
            EqualFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(NumberField, FloatField)
    def numeric_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            NumericEqualFilter,
            GreaterThanFilter,
            LessThanFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    # ... one method per field type
```

Para cambiar los filtros disponibles para un tipo de campo en toda una vista, cree una subclase del registro del backend, anule o añada un método `@filters` y devuelva una instancia de su subclase desde `get_filter_registry()`:

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

Declare estos métodos de dos maneras posibles, según si desea reemplazar los filtros existentes o ampliarlos:

* **Anular:** vuelva a declarar `@filters(StringField)` en su subclase y devuelva exactamente las clases que desea. Esto reemplaza la lista de la clase padre, así que incluya cualquier filtro integrado que desee conservar.
* **Ampliar:** declare `@filters(IntegerField)` cuando el registro padre solo registre el `NumberField` más general. Como `IntegerField` es una subclase de `NumberField`, el orden de resolución de métodos (MRO) resuelve `IntegerField` hacia su nuevo método, mientras que `DecimalField`, otra subclase de `NumberField` sin registro propio, sigue heredando el `numeric_filters` del padre sin cambios.

Esta es una subclase de Python común, por lo que no muta ningún estado global. Cada llamada a `ProductFilterRegistry()` construye un registro independiente, y sus cambios quedan limitados a las vistas que lo devuelven. Todas las demás vistas conservan los valores predeterminados del backend.

## Ejemplo completo con SQLAlchemy

El `DivisibleByFilter` siguiente toma un valor, el divisor contra el que se comprueba la columna. Una subclase de `SqlaFilterRegistry` lo aplica a todos los `IntegerField` de `ProductView`, en lugar de adjuntarlo a campos individuales:

```python
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from sqlalchemy import Integer, Numeric, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.requests import Request
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.contrib.sqla.filters import SqlaFilterRegistry
from starlette_admin.fields import BaseField
from starlette_admin.filters import (
    BaseFilter,
    FilterApplyContext,
    FilterDataType,
    FilterRegistry,
    FilterValidationError,
    filters,
)

engine = create_engine(
    "sqlite:///product.db", connect_args={"check_same_thread": False}, echo=True
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    lot_size: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class DivisibleByFilter(BaseFilter):
    """
    Filters database rows where the column value is an exact multiple of a given divisor.
    """

    name = "divisible_by"
    label = "Is divisible by"
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: str) -> int:
        """Validates and converts the raw admin UI input into an integer divisor."""
        try:
            divisor = int(raw)
        except ValueError:
            raise FilterValidationError(f"{raw!r} is not a valid integer") from None

        if divisor == 0:
            raise FilterValidationError("divisor must not be 0")

        return divisor

    def apply(self, ctx: FilterApplyContext) -> Any:
        """Applies the modulus condition to the underlying SQLAlchemy query context."""
        column = getattr(ctx.view.model, ctx.field_name)
        return column % ctx.value == 0


class ProductFilterRegistry(SqlaFilterRegistry):
    """
    Custom filter registry that injects `DivisibleByFilter` into integer fields.

    Overriding `integer_filters` gives every IntegerField the divisibility filter
    on top of the standard numeric defaults. Other numeric fields, such as
    DecimalField, are unaffected.
    """

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    fields = [
        "id",
        "name",
        "price",
        # Note: Passing just the string "lot_size" would also work, as SQLAlchemy's
        # default converter automatically maps integer columns to IntegerField.
        IntegerField("lot_size"),
    ]

    def get_filter_registry(self) -> FilterRegistry:
        """Binds the custom filter registry to this specific view."""
        return ProductFilterRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-product"))
admin.mount_to(app)
```

Consulte [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) para ver una aplicación ejecutable con una subclase personalizada de `BaseFilter` registrada de la misma manera.

La opción `lot_size__divisible_by` aparece ahora como un filtro para `IntegerField("lot_size")`, sin necesidad de declarar explícitamente `filters=` en el campo. Por ejemplo, `lot_size__divisible_by=6` coincide con los productos cuyo tamaño de lote es múltiplo de 6:

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

!!! tip
    Utilice una subclase de `FilterRegistry` cuando un filtro sea lo bastante genérico como para aplicarse a todos los campos de un tipo determinado en una vista. Utilice la lista `filters=` por campo cuando la lógica pertenezca únicamente a un campo. La [Guía de filtros](../user-guide/filters.md#anular-los-filtros-de-un-campo-especifico) contiene ejemplos del patrón por campo.

## Opciones dinámicas con `get_choices`

De forma predeterminada, la entrada de valor de un filtro sigue su `data_type`: un cuadro de texto simple para `STRING`, un cuadro numérico para `NUMBER`, etc. Anule `get_choices(request)` cuando el valor deba provenir de un menú desplegable alimentado con una lista de pares `(value, label)` por solicitud. Un filtro «es uno de» sobre un campo de relación es el caso típico: el valor que se envía de vuelta es una clave externa, pero el selector debería mostrar un nombre legible.

`get_choices` recibe la `Request` actual y devuelve una secuencia de pares `(value, label)`, o `None` (el valor predeterminado) para mantener la entrada simple. Un resultado no vacío tiene prioridad tanto sobre la entrada simple como sobre cualquier opción que el propio campo proporcione, como hace `EnumField`.

El ejemplo siguiente, tomado de [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr), añade un par «es uno de» e «is not one of» al campo `department` de la lista de `Employee`. Como `department` es un `RelationField`, el registro predeterminado solo le asigna comprobaciones de nulos: no existe una forma genérica de comparar una fila relacionada con una cadena sin procesar. `get_choices` enumera todos los `Department` por nombre para el menú desplegable, y `parse_value` convierte los valores enviados de vuelta a enteros para que `apply` pueda buscar directamente por la clave externa `Department.id` en lugar de unirse a través de la relación y comparar nombres:

```python
# examples/advanced/07-hr/filters.py
from typing import Any

from models import Department, Employee
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin.filters.base import FilterApplyContext, FilterValidationError
from starlette_admin.filters.enum import InFilter, NotInFilter


class _DepartmentChoicesMixin:
    """Shared `get_choices`/`parse_value` for the two filters below: the
    filter builder's dropdown lists every department by name, and posts back
    the department's `id` rather than its name, so `apply` can match on the
    primary key instead of an `ilike` comparison.
    """

    def get_choices(self, request: Request) -> list[tuple[int, str]]:
        session: Session = request.state.session
        return list(
            session.execute(
                select(Department.id, Department.name).order_by(Department.name)
            ).all()
        )

    def parse_value(self, raw: Any) -> list[int]:
        values = super().parse_value(raw)  # type: ignore[misc]
        try:
            return [int(v) for v in values]
        except ValueError as err:
            raise FilterValidationError("Department id must be an integer") from err


class DepartmentInFilter(_DepartmentChoicesMixin, InFilter):
    """Employees in one of the selected departments."""

    name = "department_in"
    label = "is one of"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Employee.department_id.in_(ctx.value)


class DepartmentNotInFilter(_DepartmentChoicesMixin, NotInFilter):
    """Employees not in any of the selected departments"""

    name = "department_not_in"
    label = "is not one of"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return ~Employee.department_id.in_(ctx.value)
```

Algunos aspectos que debe tener en cuenta sobre este patrón:

* **El mixin se sitúa antes de la clase base del filtro en el MRO.** `_DepartmentChoicesMixin` aparece primero en `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)`, por lo que sus métodos `get_choices` y `parse_value` anulan los que cada filtro heredaría de otro modo. `super().parse_value(raw)` todavía llega a `InFilter.parse_value`, que divide el valor sin procesar en una lista antes de que el mixin lo convierta a enteros.
* **`get_choices` se ejecuta en cada solicitud**, no una sola vez al importar, por lo que el menú desplegable siempre refleja las filas actuales. Un `Department` recién añadido aparece en el constructor de filtros de inmediato, sin reiniciar el servidor ni invalidar cachés.
* **Los pares `(value, label)` y el tipo de salida de `parse_value` deben coincidir.** El menú desplegable envía de vuelta el `value` que el usuario eligió, por lo que `parse_value` lo convierte en lo que espera `apply`. Aquí `Department.id` ya es un `int`, por lo que el `parse_value` del mixin lo reafirma y lanza un error de validación ante cualquier otra cosa.
* **`InFilter` y `NotInFilter` ya tienen por defecto `data_type = FilterDataType.ENUM`**, una selección múltiple, por lo que ninguna de las dos subclases necesita anular `data_type`. Anular `get_choices` es suficiente para poblar esa selección múltiple con departamentos en lugar de dejarla vacía.

---

## Próximos pasos

* **[Filtros](../user-guide/filters.md):** Conozca los filtros predeterminados por tipo de campo, el formato de URL y la anulación mediante `filters=`.
* **[SQLAlchemy](../integrations/sqlalchemy.md):** Explore el backend de SQLAlchemy utilizado en el ejemplo de esta página.
* **[Puntos de extensión](extension-points.md):** Vea la lista completa de métodos que puede anular en `ModelView`.
