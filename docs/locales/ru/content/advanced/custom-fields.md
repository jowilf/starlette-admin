---
title: Пользовательские поля
description: Узнайте, как создавать собственные типы полей в starlette-admin для работы
  со специализированными типами данных и пользовательскими UI-виджетами.
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# Пользовательские поля

Встроенные поля покрывают большинство столбцов, с которыми вы столкнётесь, но если ни одно из них не подходит, вы можете создать собственное, унаследовав его от [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField). Поле — это три метода, перемещающие данные между вашей моделью и браузером, плюс набор путей к шаблонам, которые его отображают. Можно унаследоваться от `BaseField` напрямую или расширить ближайшее по смыслу встроенное поле (например, `StringField` или `EnumField`), переопределив только отличающиеся части.

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

Укажите вашему экземпляру `Admin` каталог с шаблонами, а затем используйте поле в представлении:

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

Поскольку `StatusBadgeField` наследуется от `EnumField`, а не от `BaseField`, он получает атрибут `choices`, валидацию формы по этим вариантам и шаблон по умолчанию `fields/form/enum.html` для форм создания и редактирования. Всё это менять не нужно, поэтому класс переопределяет только атрибуты отображения в списке и на странице деталей.

Остальная часть этой страницы описывает, что переопределять, когда полю требуется больше, чем замена шаблона. Полный рабочий код, включая второе поле (`AvatarNameField`), которое переопределяет методы работы с данными, см. в [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## Три метода работы с данными

| Метод | Когда вызывается | Сигнатура |
| --- | --- | --- |
| `parse_form_data` | Отправлена форма создания/редактирования | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Чтение значения из экземпляра модели для отображения | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Форматирование значения для frontend (список, детали, API, экспорт) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` не переопределяет ни один из них, поскольку `EnumField` уже проверяет отправленное значение по `choices` и читает исходную строку из `obj.status`. Бейдж — это лишь представление поверх этой строки. Переопределяйте эти три метода, когда само значение нужно вычислить или преобразовать, а не просто отобразить иначе.

!!! tip "Хуки или наследование"
    Для разового изменения одного поля подкласс обычно не нужен. Вместо этого передайте [хуки `getter`, `formatter` и `parser`](../user-guide/fields.md#computing-formatting-and-parsing-values) как аргументы конструктора, чтобы обработать чтение, форматирование отображения и разбор вводимых данных.
    **Когда стоит использовать подкласс:** только если одна и та же логика нужна более чем в одном представлении или требуется изменить шаблоны.

`parse_form_data` получает исходный объект `FormData` (из `starlette.datastructures`) из запроса и возвращает данные, которые должны получить `view.create()` или `view.edit()` для этого поля. Реализация по умолчанию читает `form_data.get(self.id)` и возвращает значение без изменений. Большинству полей достаточно добавить приведение типов:

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` получает экземпляр модели и возвращает значение для отображения. Реализация по умолчанию возвращает `getattr(obj, self.name, None)`. Переопределите его для полей, которые не соответствуют одному атрибуту модели, например объединяющих два столбца. Так, `AvatarNameField` комбинирует строку `name` с загруженным аватаром строки:

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` получает то, что произвёл `parse_obj` (или слой ORM), и форматирует это для текущего запроса. Он вызывается отдельно для страницы списка, страницы деталей, JSON API и экспорта данных, поэтому при необходимости различать форму значения по контексту используйте ветвление по `request.state.action`. `AvatarNameField` требует изображение аватара только на странице списка, а во всех остальных случаях возвращается к обычному тексту:

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

Каждое поле содержит перечисленные ниже атрибуты шаблонов. Каждый из них — путь, который разрешает загрузчик Jinja2 административной панели: сначала проверяется ваш `templates_dir`, если он задан, затем происходит откат к встроенному каталогу `starlette_admin/templates/`. Подробности см. в разделе [Шаблоны](templates.md).

| Атрибут | Значение по умолчанию | Где отображается |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | Значение столбца каждой строки на странице списка |
| `detail_template` | `"fields/detail/text.html"` | Страница деталей (только чтение) |
| `form_template` | `"fields/form/input.html"` | Поле ввода в форме создания/редактирования |
| `null_template` | `"fields/detail/_null.html"` | Страницы списка и деталей, когда значение равно `None` |
| `empty_template` | `"fields/detail/_empty.html"` | Страницы списка и деталей, когда значение — пустой список или кортеж |

Все пять шаблонов получают экземпляр `field` и текущее значение `data`. Для `list_template` и `detail_template` значение `data` никогда не бывает `None` или пустым, поскольку такие случаи направляются в `null_template` или `empty_template` до подключения шаблона конкретного типа. Шаблон `form_template` также получает `error` (сообщение из `FormValidationError`, если оно возникло) и `action` (`RequestAction.CREATE`, `RequestAction.EDIT` или `RequestAction.INLINE_EDIT` при отображении внутри всплывающего окна [inline edit](../user-guide/inline-edit.md) на странице списка). Все три являются действиями формы, поэтому `action.is_form()` возвращает `True`. Код поля, которому нужно представление значения формы, должен ветвиться именно по этому условию, а не по `action == RequestAction.EDIT`.

Переопределяйте `null_template` и `empty_template`, когда отсутствующее значение должно выглядеть иначе, чем стандартные приглушённые метки `-null-` и `-empty-`, например как иконка пустого состояния или бейдж «Не указано» в стилистике самого поля:

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

Поскольку `null_template` и `empty_template` — обычные атрибуты поля, такие же как `list_template`, они общие для списка, страницы деталей и любого другого представления, отображающего это поле, например встроенной таблицы связанного представления.

`StatusBadgeField` назначает один и тот же шаблон и `list_template`, и `detail_template`, потому что один и тот же бейдж уместен в обоих контекстах:

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` переопределяет только `list_template`. Переменная `data` в этом шаблоне — словарь, который построил `parse_obj` и преобразовал `serialize_value`, а не простая строка:

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

Класс `inline-edit-value` — это опциональный маркер подчёркивания [inline edit](../user-guide/inline-edit.md). Он бездействует, пока поле не поддерживает inline-редактирование, поэтому размещение его на имени, а не на аватаре ничего не стоит здесь, при этом сохраняя корректную область действия этого элемента, если поле когда-нибудь станет редактируемым.

Переопределение `list_template` и `detail_template` с сохранением стандартного `form_template` — это ровно то, что делает `StatusBadgeField`, расширяя `EnumField`. Шаблон по умолчанию `fields/form/enum.html` отображает выпадающий список `<select>`, заполненный из `field.choices`, поэтому редактирование статуса работает без каких-либо дополнительных изменений.

## Регистрация в реестре конвертеров

Список `fields = [...]` в представлении принимает как простые имена атрибутов, так и объекты полей. Любой элемент, который ещё не является `BaseField`, проходит через **реестр конвертеров**, сопоставляющий тип столбца с классом поля. Каждый ORM-backend поставляется со своим реестром (`starlette_admin.contrib.sqla.converters.ModelConverter` и аналоги для `beanie`, `mongoengine` и `tortoise`), все они построены на одной базе:

```python
from starlette_admin.converters import BaseModelConverter, converts
```

Декоратор `@converts(*types)` помечает метод как конвертер для одного или нескольких ключей типов. `BaseModelConverter.__init__` сканирует экземпляр на наличие таких декорированных методов и строит из них словарь `converters`. Для backend'а SQLAlchemy ключами типов служат **имена** типов столбцов (`"String"`, `"Integer"`, `"Enum"` и т. д.), поскольку у SQLAlchemy нет единого общего базового класса для всех диалектов.

Наследуйте конвертер backend'а, чтобы добавить собственные сопоставления. Этот пример направляет каждый столбец `Enum` в `StatusBadgeField` вместо стандартного `EnumField`:

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

Передайте подкласс в `ModelView(converter=...)`, чтобы имена строковых полей в `fields = [...]` разрешались через ваш конвертер, а не через стандартный:

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Если вы всегда создаёте поля явно, как в минимальном примере выше, реестр конвертеров можно пропустить. Он нужен только тогда, когда вы хотите, чтобы запись вида `fields = ["status"]` порождала `StatusBadgeField` на основе типа underlying-столбца.

---

## Что дальше

* **[Поля](../user-guide/fields.md):** Полный справочник встроенных полей и таблица атрибутов `BaseField`.
* **[Шаблоны](templates.md):** Как загрузчик шаблонов разрешает `list_template`, `detail_template`, `form_template`, `null_template` и `empty_template`.
* **[Точки расширения](extension-points.md):** Все остальные подключаемые поверхности в `starlette-admin`.
