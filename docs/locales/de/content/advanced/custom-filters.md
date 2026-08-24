---
title: Benutzerdefinierte Filter
description: Erweitern Sie den integrierten Query-Builder, indem Sie benutzerdefinierte
  Datenbankfilter und Operatoren in starlette-admin erstellen.
source_hash: ac118a53b1d95372b17388cb1ce13241e53cd4b2983158208affa0fedb2e2446
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-24'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/custom-filters/)
<!-- translation-notice:end -->

# Benutzerdefinierte Filter

Erstellen Sie eine Unterklasse von `BaseFilter`, wenn Sie einen Operator benötigen, den der integrierte Satz nicht abdeckt: eine domänenspezifische Prüfung wie „_ist teilbar durch_“, eine berechnete Bedingung wie „_in diesem Monat erstellt_“ oder Unterstützung für einen Feldtyp, den die Default-Registry überspringt. Diese Seite erklärt, wie ein Filter intern funktioniert, und zeigt die zwei Möglichkeiten, einen zu registrieren: entweder durch Erstellen einer Unterklasse des `FilterRegistry` Ihres Backends, um jeden passenden Feldtyp abzudecken, oder durch Übergeben des Filters an die `filters=`-Liste eines einzelnen Felds. Für die Einzelheiten im Alltag, einschließlich der Defaultfilter pro Feldtyp, manueller Overrides und des URL-Formats, siehe den [Filter-Leitfaden](../user-guide/filters.md).

## Die `BaseFilter`-Schnittstelle

Jeder Filter, ob integriert oder benutzerdefiniert, implementiert zwei Methoden:

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

* **`parse_value(raw)`** wandelt den rohen URL-String in den Typ um, den `apply()` erwartet, z. B. ein `Decimal`, ein `date` oder eine Liste. Der Default gibt den String unverändert weiter, was für `STRING`- und `ENUM`-Filter passt, aber nicht für numerische oder zeitliche Daten. Es ist auch Ihr Validierungs-Hook: Werfen Sie `FilterValidationError` für Werte, die sich zwar parsen lassen, aber trotzdem unzulässig sind, etwa außerhalb des Bereichs liegende oder fehlerhaft formatierte Eingaben.
* **`apply(ctx)`** ist die einzige abstrakte Methode. Sie erhält einen `FilterApplyContext`, der `query`, `field_name`, `value`, `value2`, `request` und `view` enthält, und gibt ein Query-Fragment für Ihr Backend zurück.

## Wie rohe URL-Werte geparst werden

Jeder URL-Parameter ist ein String, daher kommen sowohl `price__gt=50` als auch `created_at__eq=2026-01-01` als Rohtext an. Bevor `apply()` ausgeführt wird, wandelt `parse_value()` diesen String in ein Python-Objekt um, das zum `data_type` des Filters passt:

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

So erreichen `?filter=price__gt=50` und `?filter=price__gt=50.5` `GreaterThanFilter.apply()` als Python-Zahlen (`50` als `int`, `50.5` als `float`) statt als die Strings „50“ und „50.5“. `apply()` übergibt den geparsten Wert direkt an das Query-Objekt, und der Datenbanktreiber übernimmt die abschließende Umwandlung gegen den tatsächlichen Typ der Spalte, etwa `Decimal` oder `Numeric`.

| `data_type` | Beispiel für rohen URL-Wert | Geparster Python-Wert | Geparst von |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number` (versucht `int()`, fällt auf `float()` zurück) |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal` mit `date.fromisoformat()` |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal` mit `datetime.fromisoformat()` |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal` mit `time.fromisoformat()` |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array` (splittet an Kommas außerhalb von Anführungszeichen) |
| `string`, `enum` | `admin` | `"admin"` | `BaseFilter.parse_value` Default (unverändert durchgereicht) |
| `none` | *(kein Wert in der URL)* | *(wird nie aufgerufen)* | N/A |

Wenn ein Wert nicht geparst werden kann, etwa `price__gt=abc` oder `created_at__eq=not-a-date`, wirft `parse_value()` ein `FilterValidationError`. Der Request-Handler fängt es ab und gibt `HTTP 400` zurück, bevor irgendeine Datenbank-Query ausgeführt wird:

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

Wertlose Filter, also solche mit `data_type=none` wie `is_null`, `is_true` oder `in_past`, überspringen diesen Schritt. `parse_value` läuft für sie nie, weshalb `field__is_null` kein `=value` in der URL benötigt: Es gibt keinen Eingabe-String, der umgewandelt werden müsste.

## Einen benutzerdefinierten Filter verfügbar machen

Sie können einen benutzerdefinierten Filter auf zwei Arten bei einer View registrieren. Wählen Sie die Variante, die zum gewünschten Geltungsbereich passt.

### Pro Feldinstanz (schmaler Geltungsbereich)

Übergeben Sie den Filter an die `filters=`-Liste des Zielfelds, entweder zusätzlich zu den Defaults oder an deren Stelle. Siehe [Filter für ein bestimmtes Feld überschreiben](../user-guide/filters.md#overriding-filters-for-a-specific-field) für dasselbe Muster mit integrierten Filtern. Verwenden Sie dies, wenn der Filter nur für ein einzelnes Feld sinnvoll ist.

### Registrierungsweit (für alle passenden Feldtypen)

Jedes Backend liefert eine `FilterRegistry`-Unterklasse mit: `SqlaFilterRegistry` für SQLAlchemy, `BeanieFilterRegistry` für Beanie, `MongoEngineFilterRegistry` für MongoEngine und `TortoiseFilterRegistry` für Tortoise ORM. Jede davon definiert die Defaultfilter eines unterstützten Feldtyps in einer Methode, die mit `@filters(FieldType, ...)` dekoriert ist:

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

Um die für einen Feldtyp verfügbaren Filter über eine ganze View hinweg zu ändern, erstellen Sie eine Unterklasse der Registry des Backends, überschreiben oder ergänzen eine `@filters`-Methode und geben aus `get_filter_registry()` eine Instanz Ihrer Unterklasse zurück:

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

Deklarieren Sie diese Methoden auf eine von zwei Arten, je nachdem, ob Sie die vorhandenen Filter ersetzen oder erweitern möchten:

* **Override:** Deklarieren Sie `@filters(StringField)` in Ihrer Unterklasse erneut und geben Sie genau die Klassen zurück, die Sie möchten. Damit ersetzen Sie die Liste der Elternklasse, schließen Sie also auch alle integrierten Filter ein, die Sie behalten möchten.
* **Extend:** Deklarieren Sie `@filters(IntegerField)`, wenn die Registry der Elternklasse nur den allgemeineren `NumberField` registriert. Da `IntegerField` eine Unterklasse von `NumberField` ist, löst die Method Resolution Order (MRO) `IntegerField` auf Ihre neue Methode auf, während `DecimalField`, ein anderer `NumberField`-Nachkomme ohne eigene Registrierung, weiterhin unverändert die `numeric_filters` der Elternklasse erbt.

Es handelt sich um eine gewöhnliche Python-Unterklasse, daher wird kein globaler Zustand verändert. Jeder Aufruf von `ProductFilterRegistry()` baut eine unabhängige Registry auf, und Ihre Änderungen bleiben auf die Views beschränkt, die diese Instanz zurückgeben. Alle anderen Views behalten die Defaults des Backends.

## Vollständiges SQLAlchemy-Beispiel

Der folgende `DivisibleByFilter` nimmt einen Wert entgegen, den Divisor, gegen den die Spalte geprüft wird. Eine `SqlaFilterRegistry`-Unterklasse wendet ihn auf jedes `IntegerField` von `ProductView` an, statt ihn an einzelne Felder anzuhängen:

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

Siehe [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) für eine lauffähige App mit einer benutzerdefinierten `BaseFilter`-Unterklasse, die auf dieselbe Weise registriert ist.

Die Option `lot_size__divisible_by` erscheint nun als Filter für `IntegerField("lot_size")`, ganz ohne explizite `filters=`-Deklaration am Feld. Zum Beispiel passt `lot_size__divisible_by=6` auf Produkte, deren Losgröße ein Vielfaches von 6 ist:

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

!!! tip
    Verwenden Sie eine `FilterRegistry`-Unterklasse, wenn ein Filter generisch genug ist, um auf jedes Feld eines bestimmten Typs in einer View angewendet zu werden. Verwenden Sie die `filters=`-Liste pro Feld, wenn die Logik nur zu einem einzigen Feld gehört. Der [Filter-Leitfaden](../user-guide/filters.md#overriding-filters-for-a-specific-field) enthält Beispiele für das Muster pro Feld.

## Dynamische Auswahlmöglichkeiten mit `get_choices`

Standardmäßig folgt die Werteingabe eines Filters seinem `data_type`: ein einfaches Textfeld für `STRING`, ein Zahlenfeld für `NUMBER` usw. Überschreiben Sie `get_choices(request)`, wenn der Wert stattdessen aus einem Dropdown-Menü kommen soll, das mit einer Liste von `(value, label)`-Paaren pro Request gefüllt wird. Ein „is one of“-Filter über ein Beziehungsfeld ist der typische Fall: Der zurückgesendete Wert ist ein Fremdschlüssel, aber die Auswahl sollte einen lesbaren Namen zeigen.

`get_choices` erhält den aktuellen `Request` und gibt eine Sequenz von `(value, label)`-Paaren oder `None` (den Default) zurück, um die einfache Eingabe beizubehalten. Ein nicht leeres Ergebnis hat Vorrang vor beiden: der einfachen Eingabe und allen Choices, die das Feld selbst liefert, wie es bei `EnumField` der Fall ist.

Das folgende Beispiel aus [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr) fügt dem `department`-Feld der Employee-Liste ein Paar aus „is one of“ und „is not one of“ hinzu. `department` ist ein `RelationField`, daher liefert die Default-Registry dafür nur Null-Checks: Es gibt keine generische Möglichkeit, eine verwandte Zeile mit einem rohen String zu vergleichen. `get_choices` listet jede `Department` nach Name für das Dropdown-Menü auf, und `parse_value` wandelt die zurückgesendeten Werte in Ganzzahlen um, damit `apply` direkt auf dem Fremdschlüssel `Department.id` matchen kann, statt über die Beziehung zu joinen und Namen zu vergleichen:

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

Ein paar Dinge, die Sie bei diesem Muster beachten sollten:

* **Der Mixin steht in der MRO vor der Basisklasse des Filters.** `_DepartmentChoicesMixin` kommt zuerst in `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)`, daher überschreiben sein `get_choices` und sein `parse_value` diejenigen, die jeder Filter sonst erben würde. `super().parse_value(raw)` erreicht dennoch `InFilter.parse_value`, das den Rohwert in eine Liste aufteilt, bevor der Mixin ihn in Ganzzahlen umwandelt.
* **`get_choices` läuft bei jedem Request**, nicht einmalig zur Importzeit, daher spiegelt das Dropdown-Menü immer die aktuellen Zeilen wider. Eine neu hinzugefügte `Department` erscheint sofort im Filter-Builder, ohne Serverneustart und ohne Cache, den man invalidieren müsste.
* **Die `(value, label)`-Paare und der Ausgabetyp von `parse_value` müssen zusammenpassen.** Das Dropdown-Menü sendet den vom Benutzer gewählten `value` zurück, daher wandelt `parse_value` ihn in das um, was `apply` erwartet. `Department.id` ist hier bereits ein `int`, daher stellt der `parse_value` des Mixins das lediglich erneut sicher und wirft bei allem anderen einen Validierungsfehler.
* **`InFilter` und `NotInFilter` haben bereits den Default `data_type = FilterDataType.ENUM`**, eine Mehrfachauswahl, daher braucht keine der beiden Unterklassen ein `data_type`-Override. Das Überschreiben von `get_choices` genügt, um diese Mehrfachauswahl mit Departments statt leer zu füllen.

---

## Nächste Schritte

* **[Filter](../user-guide/filters.md):** Erfahren Sie mehr über die Defaultfilter pro Feldtyp, das URL-Format und das `filters=`-Override.
* **[SQLAlchemy](../integrations/sqlalchemy.md):** Erkunden Sie das in diesem Seitenbeispiel verwendete SQLAlchemy-Backend.
* **[Erweiterungspunkte](extension-points.md):** Sehen Sie sich die vollständige Liste der Methoden an, die Sie auf `ModelView` überschreiben können.
