---
title: События
description: Подпишитесь на глобальные события жизненного цикла, такие как AFTER_CREATE,
  чтобы вести журналы аудита, отправлять вебхуки и строить асинхронные рабочие процессы.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# События

Метод-хук вроде `before_create` выполняется только в том представлении, в котором он определён. Система событий позволяет коду за пределами этого представления реагировать на происходящее внутри него: журнал аудита, вебхук или сброс кэша можно описать в одном месте вместо того, чтобы копировать их в каждый написанный вами `ModelView`.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Зарегистрируйте этот обработчик один раз рядом с экземпляром `admin`, и эндпоинт создания каждого представления будет его вызывать, включая представления, которые вы добавите позже.

## Уровень представления и уровень администратора

У каждого представления есть атрибут `events`, на который можно подписаться напрямую; область действия такой подписки ограничена этим представлением. Такой же атрибут есть у экземпляра `Admin`: он охватывает все зарегистрированные в нём представления или их подмножество, если передать `keys=`.

* **`view.events.on(...)`**: срабатывает только для этого представления.
* **`admin.events.on(...)`**: срабатывает для всех текущих и будущих представлений, если не ограничить его с помощью `keys=`.

Регистрировать обработчики в `admin.events` можно как до, так и после вызова `admin.add_view(...)`. Порядок не имеет значения: обработчик, зарегистрированный раньше, всё равно привяжется к представлению после его добавления.

## Хуки методов и подписки на события

И те и другие срабатывают в одной и той же точке жизненного цикла запроса. Различие — в том, где находится код и сколько представлений он охватывает.

| Возможность | Метод-хук (`before_create`, ...) | Подписка на события (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Где находится код** | Внутри класса представления | Где угодно, например функция уровня модуля или класс-подписчик |
| **Область действия** | Конкретное представление | Одно представление (`view.events`) или все представления (`admin.events`) |
| **Для чего подходит** | Логика, специфичная для ресурса (преобразование заголовка в slug, простановка метки времени) | Сквозная функциональность (журналы аудита, уведомления, плагины) |
| **Можно ли несколько?** | Нет, один метод на представление | Да, любое количество обработчиков на событие с упорядочиванием по приоритету |

Используйте метод-хук, когда логика неотъемлема от модели. Используйте подписку на события, когда она не относится ни к одному конкретному представлению или когда вы распространяете её как переиспользуемый компонент для нескольких панелей администрирования.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Belongs to this view only, stays here
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## Значения `AdminEvent`

`AdminEvent` — это строковое перечисление (enum). Ниже перечислены его члены, которые активно генерируются в ходе жизненного цикла представления:

| Событие | Когда срабатывает | Класс контекста |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Запись создана | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Транзакция создания зафиксирована | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Запись обновлена | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Транзакция редактирования зафиксирована | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Запись удалена | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Транзакция удаления зафиксирована | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Выполнено групповое действие или действие над строкой | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Запущен экспорт | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Запущен импорт | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Вход выполнен успешно | `AfterLoginContext` |

События `AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` и `AFTER_DELETE_COMMITTED` срабатывают только в бэкендах, которые откладывают фиксацию транзакции до конца запроса; сегодня это бэкенд SQLAlchemy. О методах-хуках `after_create_committed`, `after_edit_committed` и `after_delete_committed`, которые генерируют эти события, см. раздел [Представления](../user-guide/views.md#lifecycle-hooks).

В случае `AFTER_DELETE_COMMITTED` объект `ctx.obj` — это отсоединённый экземпляр: уже загруженные атрибуты остаются доступными для чтения, но обращение к атрибуту, который не был загружен до удаления, вызовет исключение, поскольку соответствующая строка больше не существует.

Каждый контекст — это дата-класс (dataclass), наследуемый от `EventContext`; он содержит поля, общие для всех событий:

| Атрибут | Тип | Описание |
| --- | --- | --- |
| `event` | `AdminEvent` или `str` | Сработавшее событие |
| `request` | `Request` | Текущий запрос |
| `view_key` | `str` | Значение `key` представления |
| `extra` | `dict` | По умолчанию пустой; используйте его свободно для передачи данных в цепочке пользовательских обработчиков |

Каждый подкласс добавляет поля, относящиеся к соответствующему событию.

События редактирования, вызванные [инлайн-редактированием](../user-guide/inline-edit.md) со страницы списка, содержат `extra["inline"] = True`, а их полезные нагрузки `data` / `old_data` включают только изменённое поле. Во всём остальном они идентичны обычному редактированию, поэтому существующие обработчики менять не нужно.

## Подписка с помощью декоратора

`view.events.on()` можно использовать и как декоратор, и как прямой вызов функции:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext
from starlette_admin.contrib.sqla import ModelView

logger = logging.getLogger(__name__)


class OrderView(ModelView):
    fields = ["id", "customer_name", "total", "status"]


order_view = OrderView(Order, icon="fa fa-shopping-cart")


@order_view.events.on(AdminEvent.BEFORE_DELETE)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("Deleting order pk=%s", ctx.pk)
```

При такой регистрации `log_deletion` срабатывает только для `order_view`, но не для других представлений панели администрирования. Метод `on()` также принимает обработчик напрямую, без формы декоратора:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## `AdminEventSubscriber`: группировка обработчиков

Когда одна задача реагирует на несколько событий, `AdminEventSubscriber` позволяет собрать обработчики в одном классе вместо того, чтобы разбрасывать функции по уровню модуля. Украсьте методы декоратором `@on(AdminEvent.X)` — это `on` уровня модуля из `starlette_admin.events`, а не метод шины, — затем один раз вызовите `subscribe()`:

```python
import logging
from starlette_admin.events import (
    AdminEvent,
    AdminEventSubscriber,
    AfterCreateContext,
    AfterDeleteContext,
    AfterEditContext,
    on,
)

logger = logging.getLogger(__name__)


class AuditSubscriber(AdminEventSubscriber):
    """Logs every create, update, or delete, on any view."""

    @on(AdminEvent.AFTER_CREATE)
    async def record_create(self, ctx: AfterCreateContext) -> None:
        logger.info("created %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_EDIT)
    async def record_update(self, ctx: AfterEditContext) -> None:
        logger.info("updated %s pk=%s", ctx.view_key, ctx.pk)

    @on(AdminEvent.AFTER_DELETE)
    async def record_delete(self, ctx: AfterDeleteContext) -> None:
        logger.info("deleted %s pk=%s", ctx.view_key, ctx.pk)


admin.events.subscribe(AuditSubscriber())
```

`subscribe()` доступен и в `view.events`, и в `admin.events`. Вызовите его в `view.events`, чтобы ограничить подписчика одним представлением.

Один метод может обрабатывать несколько событий: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` регистрирует один и тот же метод для обоих.

## `admin.events`: делегирование представлениям

`admin.events.on()` принимает те же аргументы, что и `view.events.on()`, плюс `keys=` — список ключей представлений, которыми ограничивается подписка. Если его не задавать (`None`, значение по умолчанию), обработчик получит каждое текущее и будущее представление модели:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Этот обработчик вызывает только представление, зарегистрированное с `key="order"`, либо то, чей ключ по умолчанию равен `"order"`. Событие `AFTER_CREATE` любого другого представления его не запустит.

`admin.events.subscribe()` тоже принимает `keys=`, так что вы можете таким же образом ограничить `AdminEventSubscriber` подмножеством представлений:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

Параметр `keys=` влияет только на события жизненного цикла представления из таблицы выше: создание, редактирование, удаление, действия, экспорт и импорт. Именно так `admin.events` определяет, к каким представлениям применяется обработчик. Событие `AFTER_LOGIN` относится к уровню администратора и не связано ни с каким представлением, поэтому `keys=` на него не действует.

## Приоритет

`on()` принимает именованный аргумент `priority` — целое число, по умолчанию равное `0`. Обработчики одного события выполняются в порядке убывания приоритета, поэтому большее число срабатывает первым:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # runs first


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # runs second
```

Обработчики с одинаковым приоритетом выполняются в порядке регистрации. Методы `AdminEventSubscriber` задают приоритет через `@on(AdminEvent.X, priority=10)`, который передаётся тем же способом.

!!! warning
    Обработчик `BEFORE_DELETE` — как и любой обработчик `BEFORE_*`, — вызвавший исключение, останавливает операцию, и последующие обработчики этого события не выполняются. Исключение в обработчике `AFTER_*` превращает уже зафиксированное изменение в неудавшийся запрос. Если ошибка не должна выглядеть как ошибка панели администрирования, заключите рискованную логику — сетевые вызовы, обращения к сторонним API — в собственный блок `try`/`except` внутри обработчика.

## Расширенный пример

Пример [`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) объединяет все шаблоны с этой страницы: переопределение хуков в `PostView`, `AuditSubscriber`, зарегистрированный в `admin.events` для всех представлений, прямую регистрацию обработчиков предупреждений при удалении, экспорте и импорте, обработчик с областью действия `post_view.events` и `CommentModerationSubscriber` с областью действия `comment_view.events`. Запустите его, чтобы увидеть, как приоритет и область действия взаимодействуют в одном приложении.

---

## Что дальше

* **[Представления](../user-guide/views.md)**: методы-хуки `before_*` и `after_*`, на которых построена эта страница.
* **[Действия](../user-guide/actions.md)**: групповые действия и действия над строкой, которые генерируют `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Инлайн-формы](../user-guide/inline-forms.md)**: вложенные записи, создаваемые вместе с родительской.
