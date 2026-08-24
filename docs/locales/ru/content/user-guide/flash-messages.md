---
title: Флеш-сообщения
description: Отправляйте пользователям временные уведомления об успехе, предупреждения
  или ошибки после выполнения действий в starlette-admin.
source_hash: 597d52f90701d02e1620bfc199dbd2bdebc85f958d6f79d8458d1f8d50a0f9ec
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/flash-messages/)
<!-- translation-notice:end -->

# Флеш-сообщения

Флеш-сообщения дают пользователю временную, однократную обратную связь после выполнения действия, например «Пост успешно создан» или «Недопустимый тип файла». Сообщение переживает один HTTP-редирект, и панель администрирования удаляет его после отображения.

`flash()` ставит сообщение в очередь текущего запроса. Панель администрирования отображает сообщение на следующей странице, которую видит пользователь, а затем очищает очередь. Этот шаблон пришёл из Flask-Admin.


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

Каждое флеш-сообщение требует категорию. Категория задаёт цвет баннера в теме по умолчанию, поэтому пользователь может с первого взгляда оценить серьёзность ситуации.

```python
from starlette_admin.flash import flash

flash(request, "Report generated.", category="success")
flash(request, "3 rows were skipped.", category="info")
flash(request, "This action can't be undone.", category="warning")
flash(request, "Upload failed: file too large.", category="error")

```

Аргумент `category` по умолчанию равен `"info"`. Он должен быть строго одним из значений `success`, `info`, `warning` или `error`. Любое другое значение вызывает `ValueError`.

## Встроенные CRUD-сообщения

Для стандартных операций CRUD не нужно вызывать `flash()`. Панель администрирования автоматически показывает сообщение `success`, когда завершаются следующие действия:

| Действие | Сообщение по умолчанию |
| --- | --- |
| **Создание** | `The item "<repr>" was added successfully.` |
| **Редактирование** | `The item "<repr>" was changed successfully.` |
| **Удаление (одиночное)** | `The item "<repr>" was successfully deleted.` |
| **Удаление (групповое)** | `%(count)d items were successfully deleted.` |

!!! note "Что подставляется вместо `<repr>`"
    Автоматические сообщения используют представление строки, которое определяет `view.repr()`, а не имя класса модели. Например, при создании поста появится флеш-сообщение *«The item 'My First Post' was added successfully»*, а не общее *«Post was added successfully»*.

## Использование флеш-сообщений в пользовательских действиях

Обработчики пользовательских действий (`@action` и `@row_action`) по умолчанию возвращают `None`. Чтобы дать пользователю обратную связь, вызовите `flash()` до возврата из обработчика.

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

        # Уведомляем пользователя об успешном выполнении пользовательского действия
        flash(request, f"{len(pks)} post(s) published.", category="success")

```

* **Если вы не вызвали `flash()`:** действие всё равно выполнится, но после редиректа страницы пользователь не получит визуального подтверждения.
* **Если действие завершилось ошибкой:** когда ваше пользовательское действие вызывает `ActionFailed`, панель администрирования перехватывает исключение и показывает его строку в виде баннера с ошибкой. Не вызывайте `flash()` в ветке `ActionFailed`, потому что редиректа запроса не происходит.

## Отображение сообщений в пользовательских шаблонах

Базовый шаблон панели администрирования извлекает и отображает флеш-сообщения за вас. Получать их самостоятельно нужно только при создании полностью [пользовательского представления](custom-views.md).

```python
from starlette_admin.flash import get_flashed_messages

messages = get_flashed_messages(request)
# Returns: [{"message": "The item \"My First Post\" was added successfully.", "category": "success"}]

```

Чтение очереди флеш-сообщений — **деструктивная** операция. Первый вызов `get_flashed_messages(request)` извлекает и очищает очередь. Последующие вызовы в рамках того же запроса вернут пустой список `[]`.

!!! important "Держите сообщения короткими"
    Флеш-сообщения хранятся в подписанной cookie `httponly` с именем `admin_flash`, а не в серверной сессии. Браузеры ограничивают размер cookie примерно 4 КБ, поэтому используйте флеш-сообщения только для краткой обратной связи. Избегайте длинных строк и больших объёмов данных. Cookie-подход также означает, что флеш-сообщения работают без `SessionMiddleware`.

> Пример работающего приложения, вызывающего `flash()` из хуков и пользовательских действий, см. в [examples/09-actions](https://github.com/jowilf/starlette-admin/tree/main/examples/09-actions).

---

## Что дальше

* **[Действия](actions.md)**: запускайте бизнес-логику из групповых действий и действий над строкой.
* **[Безопасность](security.md)**: узнайте, как `secret_key` защищает и флеш-cookie, и CSRF-токены.
* **[Шаблоны](../advanced/templates.md)**: отображайте флеш-баннеры внутри собственных компоновок.
