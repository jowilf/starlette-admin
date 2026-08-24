---
title: Инлайн-редактирование
description: Позволяет пользователям изменять значения полей прямо в таблице страницы
  списка для более быстрого ввода данных.
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# Инлайн-редактирование

Инлайн-редактирование позволяет пользователям изменять отдельное поле прямо на странице списка. При выборе ячейки открывается небольшое всплывающее окно, поэтому не нужно открывать полную форму редактирования. Используйте эту возможность для быстрых изменений одного поля: исправления заголовка, переключения статуса или корректировки даты. Взаимодействие следует знакомому шаблону [x-editable](https://vitalets.github.io/x-editable/).

Эта функция опциональна и по умолчанию отключена. Её включение не меняет стандартную страницу редактирования, которая остаётся основным интерфейсом для сложных изменений нескольких полей.

> Пример с инлайн-редактированием, который можно запустить, см. в [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Базовое использование

Укажите имена редактируемых полей в списке `inline_editable_fields`:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Редактируемые ячейки на странице списка подчёркиваются пунктирной линией. При выборе ячейки открывается всплывающее окно со стандартным элементом управления формы этого поля, заполненным текущим значением.

Подчёркивание рисуется не по всей ячейке. Каждый шаблон списка добавляет CSS-класс `inline-edit-value` к конкретному элементу, который нужно подчеркнуть, а стиль применяется только внутри редактируемой ячейки. Все встроенные шаблоны списка уже содержат этот класс. Если вы пишете собственный `list_template` и хотите такое же оформление, добавьте класс самостоятельно:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Без класса ячейка всё равно открывает всплывающее окно, но без подчёркивания.

- **Сохранение:** нажмите кнопку с галочкой или клавишу <kbd>Enter</kbd> в однострочном поле ввода. Панель администрирования проверит поле, сохранит изменение и обновит строку без перезагрузки страницы.
- **Отмена:** нажмите кнопку <kbd>x</kbd> или клавишу <kbd>Esc</kbd>, чтобы отменить изменение.

## Правила конфигурации

Приложение проверяет `inline_editable_fields` при запуске, чтобы ошибки конфигурации обнаруживались сразу. Имя из списка вызывает `ValueError`, если выполняется любое из этих условий:

- Оно не объявлено в `fields`.
- Это поле первичного ключа.
- Оно исключено со страницы списка (`exclude_from_list`) или из формы редактирования (`exclude_from_edit`).
- Это контейнерное поле или поле только для чтения: `CollectionField`, `ListField`, `ComputedField`, `FileField` или `ImageField`.

## Поддержка полей

Каждое редактируемое поле отображает тот же виджет формы, что и на странице редактирования. JavaScript- и CSS-ресурсы поля, такие как select2, flatpickr, JSONEditor или TinyMCE, загружаются на странице списка только если это поле доступно для инлайн-редактирования. Представления без инлайн-редактирования сохраняют прежний лёгкий вес страницы.

| Тип поля                                                                             | Поддерживается | Виджет во всплывающем окне          |
| ------------------------------------------------------------------------------------ | -------------- | ----------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Да             | Обычное поле ввода                  |
| `SlugField`                                                                          | Да             | Обычное поле ввода (без исходного поля) |
| `TextAreaField`                                                                      | Да             | Textarea                            |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Да             | Числовое поле ввода                 |
| `BooleanField`                                                                       | Да             | Переключатель                       |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Да             | flatpickr                           |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Да             | select2 или нативный выпадающий список |
| `TagsField`                                                                          | Да             | Теги select2                        |
| `JSONField`                                                                          | Да             | JSONEditor                          |
| `TinyMCEEditorField`                                                                 | Да             | TinyMCE                             |
| `HasOne`, `HasMany`                                                                  | Да             | select2 с асинхронным поиском       |
| `FileField`, `ImageField`                                                            | Нет            | Нет (требуется страница редактирования) |
| `CollectionField`, `ListField`, `ComputedField`                                      | Нет            | Нет (контейнеры только для чтения)  |

---

## Разрешения

Инлайн-редактирование использует существующую модель разрешений. Всплывающее окно появляется, а панель администрирования принимает запрос, только когда и `is_accessible(request)`, и `can_edit(request)` возвращают `True`. Поэтому переопределение `can_edit` защищает и инлайн-редактирование:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Также отключает инлайн-редактирование при значении False
        return "edit:post" in request.state.admin_user.roles
```

---

## Валидация

При инлайн-сохранении проверяется и записывается только изменённое поле.

- Проверка `required` и цепочка `validators` для поля выполняются точно так же, как на странице редактирования.
- Остальные поля пропускаются. Сохранение со страницы списка не может перезаписать одновременное изменение другого поля, а некорректные данные в другом поле не блокируют сохранение.

Хук кросс-полевой валидации `validate` представления по-прежнему выполняется, но словарь `data` содержит только изменённое поле. Хук, ожидающий полную отправку формы, вызовет `KeyError`, если напрямую обратится к отсутствующим ключам, поэтому сначала проверьте наличие ключа:

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    inline_editable_fields = ["title", "status", "published_at"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}

        if "title" in data and (not data["title"] or len(data["title"]) < 3):
            errors["title"] = "Ensure this value has at least 3 characters"

        if (
            "published_at" in data
            and data.get("status") == "published"
            and data["published_at"] is None
        ):
            errors["published_at"] = "Required when status is published"

        if errors:
            raise FormValidationError(errors)

        await super().validate(request, data)
```

Если валидация не проходит, всплывающее окно остаётся открытым с введённым значением. Сообщение для изменённого поля отображается под элементом управления — точно так же, как на странице редактирования. Сообщение, привязанное к другому полю, предваряется меткой этого поля.

Чтобы обнаружить инлайн-сохранение внутри хука, проверьте условие `request.state.action == RequestAction.INLINE_EDIT`. Используйте его, чтобы пропускать флеш-сообщения, предназначенные для полной отрисовки страницы.

!!! warning
    Правило валидации, привязанное к полю, которое пользователь не изменял, не выполняется при инлайн-сохранении. Если инварианты поля зависят от значений, которые пользователь не видит и не может изменить со страницы списка, не включайте это поле в `inline_editable_fields`.

---

## Хуки жизненного цикла и события

Инлайн-сохранения проходят через стандартный путь `edit()` представления. Хуки `before_edit`, `after_edit` и `after_edit_committed` срабатывают как обычно, а соответствующие [события](../advanced/events.md) используют стандартные типы контекстов. Полезные нагрузки `data` и `old_data` содержат только изменённое поле, поэтому они отражают ровно то, что затронуло сохранение.

Чтобы отличить инлайн-сохранение внутри обработчика события, проверьте значение `ctx.extra["inline"]`, которое равно `True` для инлайн-редактирования:

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## Пользовательские поля

Пользовательские поля поддерживают инлайн-редактирование автоматически, если они следуют стандартному контракту `BaseField`. Поскольку `RequestAction.INLINE_EDIT` является действием формы, метод `action.is_form()` возвращает `True`. Если ваше пользовательское поле проверяет условие `action == RequestAction.EDIT`, чтобы построить представление значения формы, замените эту проверку на `action.is_form()`, чтобы всплывающее окно получило правильное представление. Полный контракт полей описан в разделе [Пользовательские поля](../advanced/custom-fields.md).
