---
title: Действия
description: Выполняйте пакетные и построчные операции с настраиваемыми подтверждениями
  и формами прямо из представления списка.
source_hash: 91835b28170a6a3e07ed477b89c2b03aabc37254d3037ef4e47467e6ee240fca
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/actions/)
<!-- translation-notice:end -->

# Действия

Действия предоставляют прямой способ работы с записями базы данных из административного интерфейса: пользователи могут выполнять такие операции, как массовое удаление, пакетное обновление и отправку email-сообщений.

## Понимание `ActionSelection`

`ActionSelection` — центральный объект в API действий. Вместо «сырого» списка первичных ключей ваш обработчик получает экземпляр `ActionSelection`.

Этот объект разрешается лениво и ведёт себя одинаково независимо от того, отметил ли пользователь строки по одной или воспользовался опцией «выбрать все подходящие». Он также передаёт вашему обработчику активные фильтры страницы списка.

### Справочник по API `ActionSelection`

| Метод или свойство        | Описание                                                              |
| ------------------------- | --------------------------------------------------------------------- |
| `await selection.rows()`  | Возвращает целевые строки. Загружаются один раз, затем кэшируются.    |
| `await selection.pks()`   | Возвращает первичные ключи целевых строк.                             |
| `await selection.count()` | Возвращает общее количество строк, на которые направлено действие.    |
| `selection.is_select_all` | Логическое значение, указывающее, выбрал ли пользователь «все подходящие». |
| `selection.filters`       | Активная `FilterGroup`, идентичная `ListParams.filters`.               |
| `selection.q`             | Активный поисковый запрос полнотекстового поиска или `None`, если поиск неактивен. |

## Пакетные действия

По умолчанию пользователь изменяет объект, выбирая его на странице списка и редактируя отдельно. Чтобы применить одно и то же изменение сразу ко многим объектам, добавьте собственное **пакетное действие**.

!!! note
    По умолчанию `starlette-admin` добавляет пакетное действие `delete`.

Чтобы добавить собственное пакетное действие в ваш `ModelView`, напишите асинхронную функцию с нужной логикой и оберните её декоратором `@action`.

!!! important
    Имена пакетных действий должны быть уникальными в пределах одного `ModelView`.

### Пример пакетного действия

```python
from starlette.datastructures import FormData
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response

from starlette_admin import ActionSelection, action, flash
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    actions = [
        "make_published",
        "redirect",
        "delete",
    ]

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")
        articles = await selection.rows()

        # TODO: Implement database update logic here

        if not articles:
            raise ActionFailed("Sorry, we cannot process this action right now.")

        flash(
            request,
            f"{len(articles)} articles were successfully marked as published.",
            "success",
        )

    @action(
        name="redirect",
        text="Redirect",
        custom_response=True,
        confirmation="Fill the form",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="value" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def redirect_action(
        self, request: Request, selection: ActionSelection
    ) -> Response:
        data = await request.form()
        return RedirectResponse(f"https://example.com/?value={data['value']}")
```

## Глобальные действия

Стандартному пакетному действию требуется активный выбор: выпадающий список **With selected** появляется только тогда, когда отмечена хотя бы одна строка. Если же действие направлено на всю коллекцию целиком — например, полная синхронизация базы данных — сделайте его глобальным действием.

Установите `allow_empty_selection=True` в декораторе `@action`. Глобальные действия отображаются в всегда видимом выпадающем списке **Actions** и выполняются без выбора строк.

**Как ведёт себя обработчик для глобальных действий:**

- **Пустой выбор:** объект `selection` может разрешиться в ноль строк.
- **Случайные выделения:** если при запуске глобального действия у пользователя остались отмеченные строки, обработчик всё равно получит эти строки. Явно игнорируйте `selection`, когда ваша логика охватывает всю коллекцию.

Все остальные параметры (`confirmation`, `form`, `custom_response` и `is_action_allowed`) работают точно так же, как и для стандартного пакетного действия.

**Отдельные кнопки на панели инструментов:** добавьте `dedicated_button=True`, чтобы отобразить глобальное действие как отдельную кнопку панели инструментов вместо пункта в выпадающем списке **Actions**. Встроенное действие экспорта использует эту опцию. Сочетание `dedicated_button=True` с действием, требующим выбора строк, приводит к ошибке при запуске.

### Пример глобального действия

```python
class ArticleView(ModelView):
    actions = ["purge_drafts", "make_published", "delete"]

    @action(
        name="purge_drafts",
        text="Purge drafts",
        confirmation="Delete every draft article? This cannot be undone.",
        submit_btn_text="Yes, delete them",
        submit_btn_class="btn btn-danger",
        allow_empty_selection=True,
    )
    async def purge_drafts_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        # Executes without a selection; ignores the selection object entirely
        drafts = await delete_all_draft_articles()
        flash(request, f"{len(drafts)} draft article(s) were purged.", "success")
```

### Функция «выбрать все подходящие»

Когда пользователь отмечает все строки на текущей странице, а фильтру соответствует больше строк за её пределами, интерфейс предлагает выбрать все подходящие строки.

Эта опция отправляет в action API значение `all=1` вместо списка первичных ключей. Используйте `selection.is_select_all` для ветвления логики или позвольте `selection.rows()` разрешить данные в любом случае:

```python
@action(name="archive", text="Archive")
async def archive_action(self, request: Request, selection: ActionSelection) -> None:
    if selection.is_select_all:
        await self.bulk_archive_where(request, selection.filters, selection.q)
    else:
        await self.bulk_archive_pks(request, await selection.pks())
```

!!! important "Ограничения материализации"
    В режиме select-all методы `selection.rows()`, `pks()` и `count()` ограничены параметром `action_select_all_limit`, который по умолчанию равен 1000. Превышение лимита вызывает исключение `ActionFailed`. Обработчик, который читает только `selection.filters` и `selection.q`, ничего не материализует, поэтому лимит к нему не применяется.

## Построчные действия {#row-actions}

Построчные действия позволяют пользователю работать с отдельным элементом прямо из представления списка. По умолчанию `starlette-admin` включает три таких действия: `view`, `edit` и `delete`.

Чтобы добавить собственное построчное действие, напишите логику и примените декоратор `@row_action`. Если действие лишь перенаправляет пользователя на другой URL, используйте вместо него декоратор `@link_row_action`. Он встраивает ссылку в HTML-атрибут `href` и минует action API.

!!! important
    Имена построчных действий должны быть уникальными в пределах одного `ModelView`.

### Пример построчного действия

```python
from typing import Any
from starlette.datastructures import FormData
from starlette.requests import Request

from starlette_admin import flash, RowActionsDisplayType
from starlette_admin.actions import link_row_action, row_action
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed


class ArticleView(ModelView):
    row_actions = [
        "view",
        "edit",
        "go_to_example",
        "make_published",
        "delete",
    ]
    row_actions_display_type = RowActionsDisplayType.ICON_LIST

    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn btn-success",
        action_btn_class="btn btn-info",
        form="""
        <form>
            <div class="mt-3">
                <input type="text" class="form-control" name="example-text-input" placeholder="Enter value">
            </div>
        </form>
        """,
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> None:
        data: FormData = await request.form()
        user_input = data.get("example-text-input")

        # TODO: Implement database update logic here

        flash(request, "The article was successfully marked as published", "success")

    @link_row_action(
        name="go_to_example",
        text="Go to example.com",
        icon_class="fas fa-arrow-up-right-from-square",
    )
    def go_to_example_row_action(self, request: Request, pk: Any) -> str:
        return f"https://example.com/?pk={pk}"
```

### Ограничение построчных действий

Доступность построчного действия определяют два hook'а. Оба по умолчанию разрешают действие.

1. **`is_row_action_allowed(request, name)`**: выполняется один раз для каждого имени действия. Используйте его для ограничений, не зависящих от строки, например для контроля доступа на основе ролей.
2. **`is_row_action_allowed_for_obj(request, name, obj)`**: выполняется один раз для каждой строки — только для действий, прошедших первую проверку. Используйте его для ограничений, зависящих от данных, например чтобы скрыть кнопку **Publish** у уже опубликованной статьи.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "publish" in request.state.admin_user.roles
        return await super().is_row_action_allowed(request, name)

    async def is_row_action_allowed_for_obj(
        self, request: Request, name: str, obj: Any
    ) -> bool:
        if name == "make_published":
            return not obj.is_published
        return await super().is_row_action_allowed_for_obj(request, name, obj)
```

!!! warning
    Всегда вызывайте `super()` для имён действий, которые ваш переопределённый метод не обрабатывает. Иначе вы незаметно отключите проверки прав доступа для встроенных действий.

## Настройка интерфейса для построчных действий

### Типы отображения

Параметр `row_actions_display_type` определяет, как действия выглядят на странице списка. На странице деталей действия всегда отображаются как полноценные кнопки.

| Тип отображения | Описание                                                              |
| --------------- | --------------------------------------------------------------------- |
| `ICON_LIST`     | Отображает горизонтальный список кнопок, состоящих только из иконок.  |
| `DROPDOWN`      | Группирует действия в выпадающее меню с подписью.                     |
| `KEBAB`         | Группирует действия в выпадающее меню, открываемое иконкой `⋮`.       |
| `INLINE_LINKS`  | Отображает название действия под иконкой, разделённые средней точкой. |

### Позиционирование столбца

По умолчанию столбец действий отображается перед столбцами с данными. Чтобы переместить его в правую часть таблицы, используйте `RowActionsPosition`:

```python
from starlette_admin.types import RowActionsPosition


class ArticleView(ModelView):
    row_actions_position = RowActionsPosition.AFTER_COLUMNS
```

## Динамические формы действий

Параметр `form` в обоих декораторах — `@action` и `@row_action` — принимает вызываемый объект, что позволяет генерировать HTML во время обработки запроса.

Вызываемый объект может быть синхронным или асинхронным и должен возвращать строку.

- **Сигнатура для `@action`**: `(request) -> str`
- **Сигнатура для `@row_action`**: `(request, obj) -> str`

Используйте вызываемый объект, когда нужно предварительно заполнить поля формы текущими значениями строки.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.actions import ActionSelection, action, row_action
from starlette_admin.contrib.sqla import ModelView


def build_publish_form(request: Request) -> str:
    return """
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="note" placeholder="Publication note">
        </div>
    </form>
    """


def build_rename_form(request: Request, obj: Any) -> str:
    return f"""
    <form>
        <div class="mt-3">
            <input type="text" class="form-control" name="title" value="{escape(obj.title)}">
        </div>
    </form>
    """


class ArticleView(ModelView):
    actions = ["make_published"]
    row_actions = ["rename", "delete"]

    @action(
        name="make_published",
        text="Publish selected",
        confirmation="Are you sure?",
        form=build_publish_form,
    )
    async def make_published_action(
        self, request: Request, selection: ActionSelection
    ) -> None:
        pass

    @row_action(
        name="rename",
        text="Rename",
        confirmation="Rename this article?",
        form=build_rename_form,
    )
    async def rename_row_action(self, request: Request, pk: Any) -> None:
        data = await request.form()
        article = await self.find_by_pk(request, pk)
        article.title = data["title"]
```

!!! important
    Вызываемый объект формы построчного действия выполняется один раз для каждой строки на странице списка. Держите его быстрым и избегайте запросов к базе данных внутри него. Все необходимые данные строки уже доступны через параметр `obj`.
