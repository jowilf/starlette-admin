---
title: Flash-сообщения
description: Отправляйте пользователям временные уведомления об успехе, предупреждения
  или сообщения об ошибках после выполнения действий в starlette-admin.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Flash-сообщения

Flash-сообщения дают пользователю временную одноразовую обратную связь после выполнения действия, например «Запись успешно создана» или «Недопустимый тип файла». Сообщение переживает один HTTP-редирект, после отображения административная панель его удаляет.

Функция `flash()` ставит сообщение в очередь текущего запроса. Административная панель отобразит это сообщение на следующей странице, которую увидит пользователь, а затем очистит очередь. Этот паттерн пришёл из Flask-Admin.


```python
from starlette.requests import Request
from starlette_admin import BaseModelView
from starlette_admin.flash import flash


class PostView(BaseModelView):
    async def before_create(self, request: Request, data: dict) -> None:
        if not data.get("title", "").strip():
            # Ставим сообщение в очередь для следующей загрузки страницы
            flash(request, "Title cannot be blank.", category="error")
            raise ValueError("Title cannot be blank.")
```

## Категории сообщений

Каждое flash-сообщение требует указания категории. Категория определяет цвет баннера в стандартной теме оформления, что позволяет пользователю мгновенно оценить серьёзность ситуации.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")
```

Аргумент `category` по умолчанию имеет значение `"info"`. Он должен быть строго одним из следующих: `success`, `info`, `warning` или `error`. Любое другое значение приведёт к исключению `ValueError`.

## Встроенные CRUD-сообщения

Для стандартных CRUD-операций вызывать `flash()` вручную не требуется. Административная панель автоматически показывает сообщение с категорией `success` после завершения следующих действий:

| Действие | Сообщение по умолчанию |
| --- | --- |
| **Создание** | `The item "<repr>" was added successfully.` |
| **Редактирование** | `The item "<repr>" was changed successfully.` |
| **Удаление (одиночное)** | `The item "<repr>" was successfully deleted.` |
| **Удаление (массовое)** | `%(count)d items were successfully deleted.` |

!!! note "Что подставляется вместо `<repr>`"
    Автоматические сообщения используют представление строки, которое определяет метод `view.repr()`, а не имя класса модели. Например, при создании записи будет показано сообщение *"The item 'My First Post' was added successfully"*, а не общее *"Post was added successfully"*.

## Использование flash-сообщений в кастомных действиях

Обработчики кастомных действий (`@action` и `@row_action`) по умолчанию возвращают `None`. Чтобы дать пользователю обратную связь, вызовите `flash()` до того, как обработчик завершит работу.

```python
from starlette.requests import Request
from starlette_admin import BaseModelView, action, flash


class PostView(BaseModelView):
    @action(
        name="publish",
        text="Publish",
        confirmation="Publish the selected posts?",
    )
    async def publish_action(self, request: Request, pks: list) -> None:
        for pk in pks:
            obj = await self.find_by_pk(request, pk)
            obj.published = True
            await self.edit(request, pk, {"published": True})

        # Уведомляем пользователя об успешном выполнении кастомного действия
        flash(request, f"{len(pks)} post(s) published.", category="success")
```

* **Если вы не вызываете `flash()`:** действие всё равно выполнится, но после редиректа страницы пользователь не получит визуального подтверждения.
* **Если действие завершилось ошибкой:** когда ваш кастомный обработчик выбрасывает исключение `ActionFailed`, административная панель перехватывает его и отображает текст исключения в виде баннера с ошибкой. Не вызывайте `flash()` в ветке `ActionFailed`, поскольку запрос в этом случае не выполняет редирект.

## Отображение сообщений в кастомных шаблонах

Базовый шаблон административной панели извлекает и отображает flash-сообщения автоматически. Извлекать их самостоятельно нужно только при создании полностью [кастомного представления](custom-views.md).

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]
```

Чтение очереди flash-сообщений — операция **разрушающая**. Первый вызов `get_flashed_messages(request)` извлекает и очищает очередь. Последующие вызовы в рамках того же запроса вернут пустой список `[]`.

!!! important "Держите сообщения короткими"
    Flash-сообщения хранятся в подписанной cookie с флагом `httponly` под именем `admin_flash`, а не в серверной сессии. Браузеры ограничивают размер cookie примерно 4 КБ, поэтому используйте flash-сообщения только для краткой обратной связи. Избегайте длинных строк и больших объёмов данных. Кроме того, подход на основе cookie означает, что flash-сообщения работают без `SessionMiddleware`.

> Пример работающего приложения, вызывающего `flash()` из hook'ов и кастомных действий, см. в [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions).

---

## Что дальше

* **[Действия](actions.md)**: запускайте бизнес-логику из массовых или строчных действий.
* **[Безопасность](security.md)**: узнайте, как параметр `secret_key` защищает и flash-cookie, и CSRF-токены.
* **[Шаблоны](../advanced/templates.md)**: отображайте flash-баннеры внутри собственных макетов.
