---
title: Фильтры
description: Добавьте сложные вложенные фильтры AND/OR в представления панели администрирования
  с помощью конструкторов запросов, учитывающих типы данных.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
prompt_hash: efac6b04187c7def41059e1c72e46a95b2ca178220b0cb995f0594e001f3f1a5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
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

Каждое поле на странице списка может иметь свой набор операторов фильтрации, например `contains`, `between` и `is null`. Пользователи комбинируют эти операторы во вложенное дерево `AND`/`OR`, и вам не нужно писать сложные запросы к базе данных.

Панель администрирования выводит доступные фильтры из базового типа поля. Вы можете сократить, расширить или полностью заменить этот набор для любого поля.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Enable filtering and searching for these specific fields
    searchable_fields = ["title", "content", "published", "created_at"]
```

См. [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) — там находится работающее приложение, демонстрирующее фильтры по умолчанию, переопределения для отдельных полей и пользовательский подкласс `BaseFilter`.

Для каждого поля, указанного в `searchable_fields`, на панели инструментов страницы списка появляется выпадающий список **Фильтры**. С его помощью пользователи комбинируют любое количество фильтров, чтобы найти нужные строки.

## Как работает конструктор фильтров

При нажатии кнопки **Фильтры** открывается форма-выпадающий список, где пользователи строят свои запросы:

* **Добавить фильтр**: добавляет строку условия. Пользователь выбирает поле, выбирает оператор из доступных для этого поля фильтров и задаёт значение. Поле ввода подстраивается под оператор: обычное текстовое поле для `contains`, два поля для `between` и никакого ввода для `is null`.
* **Добавить группу**: вкладывает подформу со своим переключателем `AND`/`OR`. Используйте её для построения условий вида `A AND (B OR C)`.
* **Match all/any of the following**: определяет, какая логика — `AND` или `OR` — применяется на текущем уровне.
* **Apply filters**: отправляет форму как `GET`-запрос. Панель администрирования сериализует всё дерево фильтров в единственный параметр запроса `filter`, формат которого описан в разделе [Формат URL фильтра](#filter-url-format).
* **Активные фильтры**: каждый активный фильтр отображается над таблицей в виде удаляемой «пилюли». Нажатие на `×` повторно загружает список без этого правила. Вложенная группа сворачивается в одну «пилюлю», которую можно удалить целиком.

!!! tip
    Поскольку всё состояние фильтров хранится в URL, отфильтрованным списком можно поделиться. Пользователи могут добавить страницу в закладки и отправить ссылку коллеге.

## Переопределение фильтров для конкретного поля {#overriding-filters-for-a-specific-field}

Если фильтры по умолчанию слишком широкие или нужны более специфичные варианты, передайте аргумент `filters=` полю, чтобы заменить его набор по умолчанию.

Вы можете сократить список до нужных операторов, расширить его пользовательским фильтром или добавить операторы полю, у которого по умолчанию есть только проверки на null, например `TagsField`:

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

!!! important "Импортируйте фильтры из модуля вашего бэкенда"
    Классы фильтров, которые вы передаёте в `filters=`, должны быть конкретными реализациями для вашего бэкенда базы данных: `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters` или `.tortoise.filters`. Импортируйте их из модуля `filters` вашего бэкенда, а не из `starlette_admin.filters`.

## Формат URL фильтра {#filter-url-format}

Конструктор фильтров сериализует своё состояние в параметр запроса `filter` в виде компактной строки.

Формат: `field__operator` для фильтра без значений, `field__operator=value` для одного значения и `field__operator=value..value2` для фильтра с двумя значениями, например `between`. Правила соединяются через `AND` или `OR`, а скобки вкладывают группу:

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Заключайте значение в кавычки, если оно содержит пробел или скобку: `name__eq="quoted value"`. Значение-список для мультиселектного фильтра, например `is one of`, разделяется запятыми и в кавычках не нуждается: `status__in=ACTIVE,OUT_OF_STOCK`.

Если URL содержит недопустимую строку `filter` — например, неизвестное поле, недоступный оператор или значение, которое не удаётся разобрать, — приложение возвращает ошибку `HTTP 400`, а не молча отбрасывает часть условия.

!!! important
    Фильтры получают только поля, перечисленные в `searchable_fields`. Если `searchable_fields` не задан, фильтры получают все поля.


## Справочник встроенных фильтров

В следующей таблице перечислены все доступные из коробки фильтры, их обозначение (slug) в URL сохранённой ссылки и тип ожидаемого значения. Для фильтров с пометкой «два значения» в URL нужны и `value`, и `value2`, например `between=2026-01-01..2026-01-31`.

| Фильтр | Slug | Тип значения | Два значения? |
| --- | --- | --- | --- |
| Contains | `contains` | текст |  |
| Does not contain | `not_contains` | текст |  |
| Starts with | `startswith` | текст |  |
| Ends with | `endswith` | текст |  |
| Equal | `eq` | текст, число, дата, дата и время или время |  |
| Not equal | `neq` | текст или число |  |
| Is null | `is_null` | *(нет)* |  |
| Is not null | `is_not_null` | *(нет)* |  |
| Greater than | `gt` | число |  |
| Less than | `lt` | число |  |
| Greater than or equal | `gte` | число |  |
| Less than or equal | `lte` | число |  |
| Between | `between` | число, дата, дата и время или время | ✓ |
| Is in the past | `in_past` | *(нет)* |  |
| Is in the future | `in_future` | *(нет)* |  |
| Is true | `is_true` | *(нет)* |  |
| Is false | `is_false` | *(нет)* |  |
| Is one of | `in` | список через запятую |  |
| Is not one of | `not_in` | список через запятую |  |

Если нужен фильтр для типа данных, который встроенные фильтры не покрывают, — например, для JSON-поля или геоточки, — см. раздел [Пользовательские фильтры](../advanced/custom-filters.md), чтобы написать подкласс `BaseFilter` и зарегистрировать его глобально или для отдельного экземпляра поля.

---

**Что дальше**

* **[Пользовательские фильтры](../advanced/custom-filters.md):** напишите и зарегистрируйте подкласс `BaseFilter`.
* **[Действия](actions.md):** добавьте групповые действия и действия над строками на страницы списка.
* **[Представления](views.md):** узнайте больше о `searchable_fields` и остальной конфигурации страницы списка.
