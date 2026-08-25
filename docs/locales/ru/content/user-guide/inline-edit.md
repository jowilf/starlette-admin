---
title: Встроенное редактирование
description: Позволяет пользователям изменять значения полей прямо в таблице списка
  для более быстрого ввода данных.
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# Встроенное редактирование

Встроенное редактирование позволяет пользователям изменять отдельное поле прямо со страницы списка. При выборе ячейки открывается небольшое всплывающее окно (popover), поэтому не нужно открывать полную форму редактирования. Используйте эту функцию для быстрых изменений одного поля: исправления заголовка, переключения статуса или корректировки даты. Механика взаимодействия повторяет привычный шаблон [x-editable](https://vitalets.github.io/x-editable/).

Функция включается явно и по умолчанию отключена. Её включение не меняет стандартную страницу редактирования, которая остаётся основным интерфейсом для сложных изменений нескольких полей.

> Пример с встроенным редактированием, который можно запустить, см. в [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Базовое использование

Укажите имена редактируемых полей в списке `inline_editable_fields`:

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Редактируемые ячейки на странице списка подчёркиваются пунктирной линией. При выборе ячейки открывается popover со стандартным элементом управления формы для этого поля, заполненный текущим значением.

Подчёркивание наносится не на всю ячейку. Каждый встроенный шаблон списка помещает CSS-класс `inline-edit-value` на конкретный элемент, который нужно подчеркнуть, а стиль применяется только внутри редактируемой ячейки. Во всех встроенных шаблонах списка этот класс уже есть. Если вы пишете собственный `list_template` и хотите такое же визуальное оформление, добавьте класс самостоятельно:

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Без этого класса ячейка по-прежнему открывает popover, но без подчёркивания.

- **Сохранение:** Нажмите кнопку с галочкой или клавишу <kbd>Enter</kbd> в однострочном поле ввода. Административная панель проверит значение поля, сохранит изменение и обновит строку без перезагрузки страницы.
- **Отмена:** Нажмите кнопку <kbd>x</kbd> или клавишу <kbd>Esc</kbd>, чтобы отменить изменение.

## Правила конфигурации

Приложение проверяет `inline_editable_fields` при запуске, чтобы ошибки конфигурации обнаруживались сразу. Имя из списка вызывает исключение `ValueError`, если выполняется любое из следующих условий:

- Оно не объявлено в `fields`.
- Это поле первичного ключа.
- Оно исключено со страницы списка (`exclude_from_list`) или из формы редактирования (`exclude_from_edit`).
- Это контейнерное или доступное только для чтения поле: `CollectionField`, `ListField`, `ComputedField`, `FileField` или `ImageField`.

## Поддерживаемые поля

Каждое редактируемое поле отображает тот же виджет формы, что и на странице редактирования. JavaScript- и CSS-ресурсы поля, такие как select2, flatpickr, JSONEditor или TinyMCE, загружаются на странице списка только если это поле доступно для встроенного редактирования. Представления без встроенного редактирования сохраняют прежний лёгкий объём страницы.

| Тип поля                                                                             | Поддерживается | Виджет в popover                        |
| ------------------------------------------------------------------------------------ | -------------- | --------------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Да             | Обычное поле ввода                      |
| `SlugField`                                                                          | Да             | Обычное поле ввода (без исходного поля) |
| `TextAreaField`                                                                      | Да             | Textarea                                |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Да             | Числовое поле ввода                     |
| `BooleanField`                                                                       | Да             | Переключатель                           |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Да             | flatpickr                               |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Да             | select2 или нативный select             |
| `TagsField`                                                                          | Да             | select2 tags                            |
| `JSONField`                                                                          | Да             | JSONEditor                              |
| `TinyMCEEditorField`                                                                 | Да             | TinyMCE                                 |
| `HasOne`, `HasMany`                                                                  | Да             | select2 с асинхронным поиском           |
| `FileField`, `ImageField`                                                            | Нет            | Отсутствует (требуется страница правки) |
| `CollectionField`, `ListField`, `ComputedField`                                      | Нет            | Отсутствует (контейнеры только чтения)  |

---

## Права доступа

Встроенное редактирование использует существующую модель прав доступа. Popover появляется, а административная панель принимает запрос, только когда и `is_accessible(request)`, и `can_edit(request)` возвращают `True`. Поэтому переопределение `can_edit` также защищает встроенное редактирование:

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Также отключает встроенное редактирование при False
        return "edit:post" in request.state.admin_user.roles
```

---

## Валидация

При встроенном сохранении проверяется и записывается только изменённое поле.

- Проверка атрибута `required` поля и цепочка `validators` выполняются точно так же, как на странице редактирования.
- Остальные поля пропускаются. Сохранение со страницы списка не может перезаписать одновременное изменение другого поля, а некорректные данные в другом поле не блокируют сохранение.

Межполевой hook `validate` представления по-прежнему выполняется, но словарь `data` содержит только изменённое поле. Hook, ожидающий полную отправку формы, вызовет исключение `KeyError` при прямом обращении к отсутствующим ключам, поэтому сначала проверяйте наличие ключа:

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

Если валидация завершается ошибкой, popover остаётся открытым с введённым значением. Сообщение об ошибке для изменённого поля отображается под элементом управления — точно так же, как на странице редактирования. Сообщение, привязанное к другому полю, предваряется меткой этого поля.

Чтобы определить встроенное сохранение внутри hook, проверьте `request.state.action == RequestAction.INLINE_EDIT`. Используйте это, чтобы пропустить flash-сообщения, предназначенные для полной отрисовки страницы.

!!! warning
    Правило валидации, привязанное к полю, которое пользователь не редактировал, не выполняется при встроенном сохранении. Если инварианты поля зависят от значений, которые пользователь не видит и не может изменить со страницы списка, не включайте это поле в `inline_editable_fields`.

---

## Lifecycle hooks и события

Встроенные сохранения проходят через стандартный путь `edit()` представления. Hooks `before_edit`, `after_edit` и `after_edit_committed` срабатывают как обычно, а соответствующие [события](../advanced/events.md) используют стандартные типы контекстов. Полезные нагрузки `data` и `old_data` содержат только изменённое поле, поэтому они отражают ровно то, что затронуло сохранение.

Чтобы отличить встроенное сохранение внутри обработчика события, проверьте `ctx.extra["inline"]`, которое равно `True` для встроенных правок:

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

Пользовательские поля поддерживают встроенное редактирование автоматически, если они следуют стандартному контракту `BaseField`. Поскольку `RequestAction.INLINE_EDIT` является формой действия (form action), метод `action.is_form()` возвращает `True`. Если ваше пользовательское поле проверяет условие `action == RequestAction.EDIT` для построения представления значения формы, замените эту проверку на `action.is_form()`, чтобы popover получал корректное представление. Полный контракт полей см. в разделе [Custom Fields](../advanced/custom-fields.md).
