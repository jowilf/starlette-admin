---
title: Фильтры
description: Добавьте в свои admin-представления возможности сложной вложенной фильтрации
  по логике AND/OR с использованием конструкторов запросов, учитывающих тип данных.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Машинный перевод под контролем человека"

    Этот контент переведён с помощью машинной генерации, направляемой
    составленными людьми глоссариями и руководствами по стилю. Поскольку
    текст не проверяется вручную построчно, возможны отдельные ошибки или
    неестественные формулировки.

    В случае любых расхождений авторитетным источником считается
    оригинальная версия на английском языке.

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# Фильтры

Каждое поле на странице списка может иметь собственный набор операторов фильтрации, таких как `contains`, `between` и `is null`. Ваши пользователи комбинируют эти операторы во вложенное дерево `AND`/`OR`, и вам не приходится писать сложные запросы к базе данных вручную.

Admin определяет доступные фильтры на основе типа поля. Для любого поля вы можете сократить этот набор, расширить его или полностью заменить.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

См. [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) — это работающее приложение, демонстрирующее фильтры по умолчанию, переопределение фильтров для отдельных полей и пользовательский подкласс `BaseFilter`.

Для каждого поля, перечисленного в `searchable_fields`, на панели инструментов списка появляется выпадающее меню **Filters**. С его помощью пользователи комбинируют любое количество фильтров, чтобы найти нужные строки.

## Как работает конструктор фильтров

При нажатии кнопки **Filters** открывается форма-выпадающее меню, в которой пользователи формируют свои запросы:

* **Add filter**: добавляет строку условия. Пользователь выбирает поле, выбирает один из доступных для этого поля операторов фильтрации и указывает значение. Ввод адаптируется к оператору: обычное текстовое поле для `contains`, два поля для `between` и отсутствие ввода вовсе для `is null`.
* **Add group**: добавляет вложенную подформу со своим селектором `AND`/`OR`. Используйте её для построения условий вида `A AND (B OR C)`.
* **Match all/any of the following**: задаёт, какая логика применяется на текущем уровне — `AND` или `OR`.
* **Apply filters**: отправляет форму как `GET`-запрос. Admin сериализует всё дерево фильтров в единственный параметр запроса `filter`, формат которого описан в разделе [Формат URL фильтра](#the-filter-url-format).
* **Active filters**: каждый активный фильтр отображается в виде удаляемой «пилюли» над таблицей. Нажатие на `×` повторно отправляет список без этого правила. Вложенная группа сворачивается в одну «пилюлю», которую можно удалить целиком.

!!! tip
    Поскольку всё состояние фильтров хранится в URL, отфильтрованный список можно передавать другим пользователям: они могут добавить страницу в закладки и отправить ссылку коллеге.

## Переопределение фильтров для конкретного поля {#overriding-filters-for-a-specific-field}

Если фильтры по умолчанию слишком широкие или вам требуется что-то более специфичное, передайте аргумент `filters=` в поле, чтобы заменить набор по умолчанию.

Вы можете сократить список до нужных операторов, расширить его пользовательским фильтром или добавить операторы в поле, которому по умолчанию доступны только базовые проверки на NULL, например `TagsField`:

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

!!! important "Импортируйте фильтры из вашего backend"
    Классы фильтров, которые вы передаёте в `filters=`, должны быть конкретными реализациями для вашей базы данных: `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters` или `.tortoise.filters`. Импортируйте их из модуля `filters` вашего backend, а не из `starlette_admin.filters`.

## Формат URL фильтра {#the-filter-url-format}

Конструктор фильтров сериализует своё состояние в параметр запроса `filter` в виде компактной строки.

Формат выглядит так: `field__operator` — для фильтра без значений, `field__operator=value` — для одного значения и `field__operator=value..value2` — для фильтра с двумя значениями, например `between`. Правила соединяются через `AND` или `OR`, а круглые скобки образуют группу:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Заключайте значение в кавычки, если оно содержит пробел или круглую скобку: `name__eq="quoted value"`. Значение-список для мультивыбора фильтра, такого как `is one of`, разделяется запятыми и в кавычках не нуждается: `status__in=ACTIVE,OUT_OF_STOCK`.

Если URL содержит недопустимую строку `filter` — например, неизвестное поле, недоступный оператор или значение, которое не удаётся разобрать, — приложение возвращает ошибку `HTTP 400`, вместо того чтобы молча отбросить часть условия.

!!! important
    Фильтры получают только те поля, которые перечислены в `searchable_fields`. Если не задать `searchable_fields`, фильтры получит каждое поле.


## Справочник встроенных фильтров

В следующей таблице перечислены все доступные из коробки фильтры, соответствующие slug в URL (который вы видите в сохранённой ссылке) и тип значения, который ожидает каждый из них. Для фильтров, помеченных как «два значения», необходимо указать и `value`, и `value2` в URL, например `between=2026-01-01..2026-01-31`.

| Фильтр | Slug | Тип значения | Два значения? |
| --- | --- | --- | --- |
| Contains | `contains` | текст |  |
| Does not contain | `not_contains` | текст |  |
| Starts with | `startswith` | текст |  |
| Ends with | `endswith` | текст |  |
| Equal | `eq` | текст, число, дата, datetime или время |  |
| Not equal | `neq` | текст или число |  |
| Is null | `is_null` | *(нет)* |  |
| Is not null | `is_not_null` | *(нет)* |  |
| Greater than | `gt` | число |  |
| Less than | `lt` | число |  |
| Greater than or equal | `gte` | число |  |
| Less than or equal | `lte` | число |  |
| Between | `between` | число, дата, datetime или время | ✓ |
| Is in the past | `in_past` | *(нет)* |  |
| Is in the future | `in_future` | *(нет)* |  |
| Is true | `is_true` | *(нет)* |  |
| Is false | `is_false` | *(нет)* |  |
| Is one of | `in` | список через запятую |  |
| Is not one of | `not_in` | список через запятую |  |

Если вам нужен фильтр для типа данных, который не покрывается встроенными фильтрами, например JSON-поле или гео-точка, обратитесь к разделу [Пользовательские фильтры](../advanced/custom-filters.md), чтобы написать подкласс `BaseFilter` и зарегистрировать его глобально или для отдельного экземпляра поля.

---

**Что дальше**

* **[Пользовательские фильтры](../advanced/custom-filters.md):** напишите и зарегистрируйте подкласс `BaseFilter`.
* **[Действия](actions.md):** добавьте массовые действия и действия для строк на страницы списков.
* **[Представления](views.md):** узнайте больше о `searchable_fields` и остальной конфигурации страницы списка.
