---
title: Filtres personnalisés
description: Étendez le générateur de requêtes intégré en créant des filtres de base
  de données et des opérateurs personnalisés dans starlette-admin.
source_hash: ac118a53b1d95372b17388cb1ce13241e53cd4b2983158208affa0fedb2e2446
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/custom-filters/)
<!-- translation-notice:end -->

# Filtres personnalisés

Sous-classez `BaseFilter` lorsque vous avez besoin d'un opérateur non couvert par l'ensemble intégré : une vérification propre à votre domaine comme «_est divisible par_ », une condition calculée comme «_créé ce mois-ci_ », ou la prise en charge d'un type de champ ignoré par le registre par défaut. Cette page explique comment fonctionne un filtre en interne et présente les deux façons d'en enregistrer un : soit en sous-classant le `FilterRegistry` de votre backend pour couvrir tous les types de champs correspondants, soit en passant le filtre à la liste `filters=` d'un seul champ. Pour les détails du quotidien, notamment les filtres par défaut par type de champ, les surcharges manuelles et le format des URL, consultez le [guide des filtres](../user-guide/filters.md).

## L'interface `BaseFilter`

Chaque filtre, qu'il soit intégré ou personnalisé, implémente deux méthodes :

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

* **`parse_value(raw)`** convertit la chaîne brute issue de l'URL dans le type attendu par `apply()`, tel qu'un `Decimal`, une `date` ou une liste. L'implémentation par défaut transmet la chaîne inchangée, ce qui convient aux filtres `STRING` et `ENUM`, mais pas aux données numériques ou temporelles. C'est également votre hook de validation : levez une `FilterValidationError` pour les valeurs qui s'analysent mais restent inacceptables, comme une entrée hors plage ou mal formée.
* **`apply(ctx)`** est la seule méthode abstraite. Elle reçoit un `FilterApplyContext` contenant `query`, `field_name`, `value`, `value2`, `request` et `view`, et renvoie un fragment de requête pour votre backend.

## Comment les valeurs brutes des URL sont analysées

Chaque paramètre d'URL est une chaîne, donc `price__gt=50` et `created_at__eq=2026-01-01` arrivent tous deux sous forme de texte brut. Avant l'exécution de `apply()`, `parse_value()` convertit cette chaîne en un objet Python correspondant au `data_type` du filtre :

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

Ainsi, `?filter=price__gt=50` et `?filter=price__gt=50.5` atteignent `GreaterThanFilter.apply()` sous forme de nombres Python (`50` en `int`, `50.5` en `float`) plutôt que sous forme des chaînes `"50"` et `"50.5"`. `apply()` transmet cette valeur analysée directement à l'objet de requête, et le driver de base de données gère la conversion finale vers le type réel de la colonne, tel que `Decimal` ou `Numeric`.

| `data_type` | Exemple de valeur brute dans l'URL | Valeur Python analysée | Analysé par |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number` (essaie `int()`, sinon bascule vers `float()`) |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal` avec `date.fromisoformat()` |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal` avec `datetime.fromisoformat()` |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal` avec `time.fromisoformat()` |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array` (sépare sur les virgules non entre guillemets) |
| `string`, `enum` | `admin` | `"admin"` | Valeur par défaut de `BaseFilter.parse_value` (transmise telle quelle) |
| `none` | *(aucune valeur dans l'URL)* | *(jamais appelé)* | N/A |

Lorsqu'une valeur ne peut être analysée, comme `price__gt=abc` ou `created_at__eq=not-a-date`, `parse_value()` lève une `FilterValidationError`. Le gestionnaire de requête la capture et renvoie `HTTP 400` avant d'exécuter toute requête en base de données :

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

Les filtres sans valeur, ceux dont `data_type=none` tels que `is_null`, `is_true` ou `in_past`, ignorent cette étape. `parse_value` n'est jamais exécuté pour eux, c'est pourquoi `field__is_null` ne nécessite aucun `=valeur` dans l'URL : il n'y a aucune chaîne d'entrée à convertir.

## Rendre un filtre personnalisé disponible

Vous pouvez enregistrer un filtre personnalisé auprès d'une vue de deux manières. Choisissez celle qui correspond au périmètre souhaité.

### Par instance de champ (périmètre restreint)

Passez le filtre dans la liste `filters=` du champ ciblé, soit à côté des valeurs par défaut, soit à leur place. Consultez [Overriding filters for a specific field](../user-guide/filters.md#overriding-filters-for-a-specific-field) pour le même schéma avec des filtres intégrés. Utilisez cette approche lorsque le filtre n'a de sens que pour un seul champ.

### À l'échelle du registre (tous les types de champs correspondants)

Chaque backend fournit une sous-classe de `FilterRegistry` : `SqlaFilterRegistry` pour SQLAlchemy, `BeanieFilterRegistry` pour Beanie, `MongoEngineFilterRegistry` pour MongoEngine et `TortoiseFilterRegistry` pour Tortoise ORM. Chacune définit les filtres par défaut d'un type de champ pris en charge dans une méthode décorée avec `@filters(FieldType, ...)` :

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

Pour modifier les filtres disponibles pour un type de champ sur l'ensemble d'une vue, sous-classez le registre du backend, surchargez ou ajoutez une méthode `@filters`, puis renvoyez une instance de votre sous-classe depuis `get_filter_registry()` :

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

Déclarez ces méthodes de deux façons possibles, selon que vous souhaitez remplacer les filtres existants ou les étendre :

* **Remplacement :** redéclarez `@filters(StringField)` dans votre sous-classe et renvoyez exactement les classes souhaitées. Cela remplace la liste du parent ; incluez donc tout filtre intégré que vous souhaitez conserver.
* **Extension :** déclarez `@filters(IntegerField)` lorsque le registre parent n'enregistre que le type plus général `NumberField`. Comme `IntegerField` est une sous-classe de `NumberField`, l'ordre de résolution des méthodes (MRO) associe `IntegerField` à votre nouvelle méthode, tandis que `DecimalField`, autre sous-classe de `NumberField` sans enregistrement propre, continue d'hériter du `numeric_filters` parent sans modification.

Il s'agit d'une simple sous-classe Python : elle ne modifie aucun état global. Chaque appel à `ProductFilterRegistry()` construit un registre indépendant, et vos modifications restent limitées aux vues qui le renvoient. Toutes les autres vues conservent les valeurs par défaut du backend.

## Exemple complet avec SQLAlchemy

Le `DivisibleByFilter` ci-dessous prend une valeur : le diviseur à appliquer à la colonne. Une sous-classe de `SqlaFilterRegistry` l'applique à chaque `IntegerField` de `ProductView`, plutôt que de l'attacher à des champs individuels :

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

Consultez [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) pour une application exécutable contenant une sous-classe personnalisée de `BaseFilter` enregistrée de la même manière.

L'option `lot_size__divisible_by` apparaît désormais comme un filtre pour `IntegerField("lot_size")`, sans déclaration explicite de `filters=` sur le champ. Par exemple, `lot_size__divisible_by=6` sélectionne les produits dont la taille de lot est un multiple de 6 :

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

!!! tip
    Utilisez une sous-classe de `FilterRegistry` lorsqu'un filtre est suffisamment générique pour s'appliquer à chaque champ d'un type donné dans une vue. Utilisez la liste `filters=` par champ lorsque la logique se rapporte à un seul champ. Le [guide des filtres](../user-guide/filters.md#overriding-filters-for-a-specific-field) propose des exemples du schéma par champ.

## Choix dynamiques avec `get_choices`

Par défaut, le champ de saisie de valeur d'un filtre suit son `data_type` : une zone de texte simple pour `STRING`, une zone numérique pour `NUMBER`, etc. Surchargez `get_choices(request)` lorsque la valeur doit provenir d'une liste déroulante alimentée par une liste de paires `(value, label)` spécifique à chaque requête. Un filtre « is one of » sur un champ de relation est le cas typique : la valeur renvoyée est une clé étrangère, mais le sélecteur doit afficher un nom lisible.

`get_choices` reçoit la `Request` courante et renvoie une séquence de paires `(value, label)`, ou `None` (la valeur par défaut) pour conserver la saisie simple. Un résultat non vide prime à la fois sur la saisie simple et sur tout choix fourni par le champ lui-même, comme le fait `EnumField`.

L'exemple ci-dessous, tiré de [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr), ajoute une paire « is one of » / « is not one of » au champ `department` de la liste `Employee`. Comme `department` est une `RelationField`, le registre par défaut ne lui offre que des vérifications de nullité : il n'existe aucun moyen générique de comparer une ligne liée à une chaîne brute. `get_choices` liste chaque `Department` par nom pour la liste déroulante, et `parse_value` convertit les valeurs renvoyées en entiers afin que `apply` puisse faire correspondre directement la clé étrangère `Department.id` au lieu de passer par la relation et de comparer des noms :

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

Quelques points à retenir concernant ce schéma :

* **Le mixin précède la classe de base du filtre dans le MRO.** `_DepartmentChoicesMixin` apparaît en premier dans `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)`, si bien que ses méthodes `get_choices` et `parse_value` surchargent celles que chaque filtre hériterait sinon. `super().parse_value(raw)` atteint toujours `InFilter.parse_value`, qui scinde la valeur brute en liste avant que le mixin ne la convertisse en entiers.
* **`get_choices` s'exécute à chaque requête**, et non une seule fois à l'importation, de sorte que la liste déroulante reflète toujours les lignes actuelles. Un `Department` nouvellement ajouté apparaît immédiatement dans le générateur de filtres, sans redémarrage du serveur ni cache à invalider.
* **Les paires `(value, label)` et le type de sortie de `parse_value` doivent concorder.** La liste déroulante renvoie la `value` choisie par l'utilisateur ; `parse_value` la convertit donc dans ce qu'attend `apply`. Ici, `Department.id` est déjà un `int`, le `parse_value` du mixin réaffirme donc ce type et lève une erreur de validation dans tout autre cas.
* **`InFilter` et `NotInFilter` utilisent déjà `data_type = FilterDataType.ENUM` par défaut**, une sélection multiple : aucune des deux sous-classes n'a besoin de surcharger `data_type`. Surcharger `get_choices` suffit pour alimenter cette sélection multiple avec les départements au lieu de la laisser vide.

---

## Et ensuite

* **[Filtres](../user-guide/filters.md) :** découvrez les filtres par défaut par type de champ, le format des URL et la surcharge via `filters=`.
* **[SQLAlchemy](../integrations/sqlalchemy.md) :** explorez le backend SQLAlchemy utilisé dans l'exemple de cette page.
* **[Points d'extension](extension-points.md) :** consultez la liste complète des méthodes que vous pouvez surcharger sur `ModelView`.
