---
title: Пользовательские поля
description: Узнайте, как создавать пользовательские типы полей в starlette-admin
  для работы со специализированными типами данных и пользовательскими виджетами интерфейса.
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# Пользовательские поля

Встроенные поля покрывают большинство столбцов, с которыми вы встретитесь, но если ни одно из них не подходит, вы можете создать своё собственное, унаследовав его от [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField). Поле — это три метода, которые перемещают данные между вашей моделью и браузером, плюс набор путей к шаблонам для его отрисовки. Наследуйте класс напрямую от `BaseField` или расширьте встроенное поле, наиболее близкое к нужному (например, `StringField` или `EnumField`), переопределив только отличающиеся части.

## Минимальный пример

```python
from dataclasses import dataclass
from dataclasses import field as dc_field

from starlette_admin.fields import EnumField


@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )
```

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

Укажите вашему экземпляру `Admin` каталог с шаблонами, затем используйте поле в представлении:

```python
from starlette_admin.contrib.sqla import Admin, ModelView

admin = Admin(engine, title="My Admin", templates_dir="templates/")
```

```python
class EmployeeView(ModelView):
    fields = [
        "id",
        "name",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
    ]
```

Поскольку `StatusBadgeField` наследуется от `EnumField`, а не от `BaseField`, он получает `choices`, валидацию формы по этим вариантам и шаблон по умолчанию `fields/form/enum.html` для форм создания и редактирования. Всё это менять не нужно, поэтому класс переопределяет только атрибуты отрисовки на странице списка и странице деталей.

Остальная часть этой страницы описывает, что нужно переопределять, когда полю требуется больше, чем замена шаблона. Полный рабочий код, а также второе поле (`AvatarNameField`), которое действительно переопределяет методы работы с данными, см. в [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## Три метода работы с данными

| Метод | Когда вызывается | Сигнатура |
| --- | --- | --- |
| `parse_form_data` | Отправлена форма создания или редактирования | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Чтение значения из экземпляра модели для отображения | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Форматирование значения для фронтенда (список, детали, API, экспорт) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` не переопределяет ни один из них, потому что `EnumField` уже проверяет отправленное значение по `choices` и читает исходную строку из `obj.status`. Значок — это лишь представление поверх этой строки. Переопределяйте эти три метода, когда само значение нужно вычислить или преобразовать, а не просто отрисовать иначе.

!!! tip "Хуки или наследование"
    Для разового изменения одного поля редко требуется создавать подкласс. Передайте вместо этого [хуки `getter`, `formatter` и `parser`](../user-guide/fields.md#computing-formatting-and-parsing-values) как аргументы конструктора, чтобы обработать чтение, форматирование для отображения и разбор ввода.
    **Когда создавать подкласс:** только когда одна и та же логика нужна более чем в одном представлении или когда нужно изменить шаблоны.

`parse_form_data` получает исходный объект `FormData` (из `starlette.datastructures`) из запроса и возвращает данные, которые `view.create()` или `view.edit()` должны получить для этого поля. Реализация по умолчанию читает `form_data.get(self.id)` и возвращает значение без изменений. Большинству полей достаточно добавить приведение типов:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` получает экземпляр модели и возвращает значение для отображения. Реализация по умолчанию возвращает `getattr(obj, self.name, None)`. Переопределите его для полей, которые не соответствуют одному атрибуту модели, например, объединяющих два столбца. Так, `AvatarNameField` объединяет строку `name` с загруженным аватаром строки:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` получает то, что создал `parse_obj` (или слой ORM), и форматирует это для текущего запроса. Он вызывается отдельно для страницы списка, страницы деталей, JSON API и экспорта данных, поэтому, когда форма данных должна различаться по контексту, используйте ветвление по `request.state.action`. Полю `AvatarNameField` изображение аватара нужно только на странице списка, а во всех остальных случаях оно возвращается как обычный текст:

```python
async def serialize_value(self, request: Request, value: Any) -> Any:
    name, avatar_key = value.get("name"), value.get("avatar_key")
    if request.state.action != RequestAction.LIST:
        return name
    if avatar_key is not None:
        value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
    return value
```

!!! warning
    Всё, что `serialize_value` возвращает для `RequestAction.LIST` и `RequestAction.RELATION_LOOKUP`, попадает напрямую в JSON-ответ, поэтому результат должен быть сериализуемым в JSON.

## Пути к шаблонам

Каждое поле содержит перечисленные ниже атрибуты шаблонов. Каждый из них — это путь, который разрешает загрузчик Jinja2 в панели администрирования: он сначала проверяет ваш `templates_dir`, если он задан, а затем обращается к встроенному каталогу `starlette_admin/templates/`. Подробности см. в разделе [Шаблоны](templates.md).

| Атрибут | Значение по умолчанию | Где используется |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | Значение столбца в каждой строке на странице списка |
| `detail_template` | `"fields/detail/text.html"` | Страница деталей (только чтение) |
| `form_template` | `"fields/form/input.html"` | Поле ввода в форме создания и редактирования |
| `null_template` | `"fields/detail/_null.html"` | Страницы списка и деталей, когда значение равно `None` |
| `empty_template` | `"fields/detail/_empty.html"` | Страницы списка и деталей, когда значение — пустой список или кортеж |

Все пять шаблонов получают экземпляр `field` и текущее значение `data`. Для `list_template` и `detail_template` значение `data` никогда не бывает `None` или пустым, потому что такие случаи направляются в `null_template` или `empty_template` до подключения шаблона конкретного типа. `form_template` также получает `error` (сообщение из `FormValidationError`, если оно возникло) и `action` (`RequestAction.CREATE`, `RequestAction.EDIT` или `RequestAction.INLINE_EDIT`, когда шаблон отрисован внутри всплывающего окна [инлайн-редактирования](../user-guide/inline-edit.md) на странице списка). Все три — это действия формы, поэтому `action.is_form()` возвращает `True`. Код поля, которому нужно представление значения формы, должен делать ветвление по этому признаку, а не по `action == RequestAction.EDIT`.

Переопределяйте `null_template` и `empty_template`, когда отсутствующее значение должно выглядеть иначе, чем стандартные приглушённые метки `-null-` и `-empty-`, например, как иконка пустого состояния или значок «Не указано» в стиле самого поля:

```python
@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    null_template: str = "employee/status_badge_null.html"
    empty_template: str = "employee/status_badge_null.html"
```

```html title="templates/employee/status_badge_null.html"
<span class="badge">Unknown</span>
```

Поскольку `null_template` и `empty_template` — обычные атрибуты поля, как и `list_template`, они общие для страницы списка, страницы деталей и любого другого представления, которое отрисовывает это поле, например инлайн-таблицы связанного представления.

`StatusBadgeField` назначает один и тот же шаблон и `list_template`, и `detail_template`, потому что один и тот же значок подходит для обоих контекстов:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` переопределяет только `list_template`. Переменная `data` в этом шаблоне — это словарь, который построил `parse_obj` и преобразовал `serialize_value`, а не обычная строка:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

Класс `inline-edit-value` — это маркер включения подчёркивания [инлайн-редактирования](../user-guide/inline-edit.md). Он ни на что не влияет, пока поле не поддерживает инлайн-редактирование, поэтому указать его на имени, а не на аватаре ничего не стоит, при этом возможность редактирования остаётся корректно ограниченной, если поле когда-нибудь станет редактируемым.

Переопределить `list_template` и `detail_template`, оставив `form_template` по умолчанию, — это именно то, что делает `StatusBadgeField`, расширяя `EnumField`. Шаблон по умолчанию `fields/form/enum.html` отрисовывает выпадающий список `<select>`, заполненный из `field.choices`, поэтому редактирование статуса работает без каких-либо дополнительных изменений.

## Регистрация в реестре конвертеров

Список `fields = [...]` в представлении принимает как простые имена атрибутов, так и объекты полей. Любой элемент, который ещё не является `BaseField`, проходит через **реестр конвертеров**, который сопоставляет тип столбца с классом поля. Каждый бэкенд ORM поставляется со своим реестром (`starlette_admin.contrib.sqla.converters.ModelConverter` и аналоги для `beanie`, `mongoengine` и `tortoise`), и все они построены на одной базе:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

Декоратор `@converts(*types)` помечает метод как конвертер для одного или нескольких ключей типов. `BaseModelConverter.__init__` сканирует экземпляр на наличие таких методов и строит из них свой словарь `converters`. Для бэкенда SQLAlchemy ключами типов служат **имена** типов столбцов (`"String"`, `"Integer"`, `"Enum"` и так далее), потому что у SQLAlchemy нет единого общего базового класса для всех диалектов.

Создайте подкласс конвертера бэкенда, чтобы добавить собственные сопоставления. Этот пример направляет каждый столбец типа `Enum` в `StatusBadgeField` вместо `EnumField` по умолчанию:

```python
from typing import Any

from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts
from starlette_admin.fields import BaseField


class MyModelConverter(ModelConverter):
    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        return StatusBadgeField(
            **self._field_common(*args, **kwargs), enum=_type.enum_class
        )
```

Передайте подкласс в `ModelView(converter=...)`, чтобы имена строковых полей в `fields = [...]` разрешались через ваш конвертер, а не через конвертер по умолчанию:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Если вы всегда создаёте поля явно, как в минимальном примере выше, реестр конвертеров можно не использовать. Он нужен только тогда, когда вы хотите, чтобы запись вроде `fields = ["status"]` создавала `StatusBadgeField` на основе типа столбца.

---

## Что дальше

* **[Поля](../user-guide/fields.md):** полный справочник встроенных полей и таблица атрибутов `BaseField`.
* **[Шаблоны](templates.md):** как загрузчик шаблонов разрешает `list_template`, `detail_template`, `form_template`, `null_template` и `empty_template`.
* **[Точки расширения](extension-points.md):** все остальные подключаемые поверхности в `starlette-admin`.
