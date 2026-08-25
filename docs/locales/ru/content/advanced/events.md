---
title: События
description: Подписка на глобальные события жизненного цикла, такие как AFTER_CREATE,
  для создания журналов аудита, вебхуков и асинхронных рабочих процессов.
source_hash: e066fc5f57c4f38a189d1a2889e1aa3463d726bf0b7b986068937f673c067a6f
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/events/)
<!-- translation-notice:end -->

# События

Метод-хук вроде `before_create` выполняется только в том представлении (view), где он определён. Система событий позволяет коду за пределами этого представления реагировать на происходящее внутри него: журнал аудита, вебхук или инвалидация кэша могут находиться в одном месте вместо того, чтобы копироваться в каждый создаваемый вами `ModelView`.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def notify_slack(ctx: AfterCreateContext) -> None:
    print(f"New {ctx.view_key} created: pk={ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, notify_slack)
```

Зарегистрируйте это один раз рядом с экземпляром `admin`, и endpoint создания каждого представления будет вызывать обработчик, включая представления, которые вы добавите позже.

## Уровень представления и уровень admin

У каждого представления есть атрибут `events`, на который можно подписаться напрямую; область действия такой подписки ограничена этим представлением. У экземпляра `Admin` атрибут `events` тоже есть — он охватывает все зарегистрированные в нём представления или их подмножество, если передать `keys=`.

* **`view.events.on(...)`**: срабатывает только для этого представления.
* **`admin.events.on(...)`**: срабатывает для всех текущих и будущих представлений, если не ограничить подписку через `keys=`.

Регистрация на `admin.events` возможна как до, так и после вызова `admin.add_view(...)`. Порядок не имеет значения: обработчик, зарегистрированный первым, всё равно привяжется к представлению после его добавления.

## Методы-хуки и подписки на события

И те, и другие срабатывают в одной и той же точке жизненного цикла запроса. Различие заключается в том, где находится код и скольким представлениям он доступен.

| Характеристика | Метод-хук (`before_create`, ...) | Подписка на событие (`view.events` / `admin.events`) |
| --- | --- | --- |
| **Где находится код** | Внутри класса представления | Где угодно, например функция уровня модуля или класс-подписчик |
| **Область действия** | Конкретное представление | Одно представление (`view.events`) или все представления (`admin.events`) |
| **Подходит для** | Логики, специфичной для данного ресурса (slugify заголовка, проставление метки времени) | Сквозной функциональности (журналы аудита, уведомления, плагины) |
| **Можно ли несколько?** | Нет, один метод на представление | Да, любое количество обработчиков на событие, упорядоченных по приоритету |

Используйте метод-хук, когда логика неотъемлема от модели. Используйте подписку на событие, когда она не относится к какому-то одному представлению или когда вы поставляете её как переиспользуемый компонент для нескольких админ-панелей.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    # Относится только к этому представлению, остаётся здесь
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")
```

## Значения AdminEvent

`AdminEvent` — это строковый enum. Ниже перечислены члены, активно генерируемые жизненным циклом представлений:

| Событие | Когда срабатывает | Класс контекста |
| --- | --- | --- |
| `BEFORE_CREATE` / `AFTER_CREATE` | Запись создана | `BeforeCreateContext` / `AfterCreateContext` |
| `AFTER_CREATE_COMMITTED` | Транзакция создания зафиксирована | `AfterCreateContext` |
| `BEFORE_EDIT` / `AFTER_EDIT` | Запись обновлена | `BeforeEditContext` / `AfterEditContext` |
| `AFTER_EDIT_COMMITTED` | Транзакция редактирования зафиксирована | `AfterEditContext` |
| `BEFORE_DELETE` / `AFTER_DELETE` | Запись удалена | `BeforeDeleteContext` / `AfterDeleteContext` |
| `AFTER_DELETE_COMMITTED` | Транзакция удаления зафиксирована | `AfterDeleteContext` |
| `BEFORE_ACTION` / `AFTER_ACTION` | Выполнено пакетное или строчное действие | `BeforeActionContext` / `AfterActionContext` |
| `BEFORE_EXPORT` / `AFTER_EXPORT` | Запущен экспорт | `BeforeExportContext` / `AfterExportContext` |
| `BEFORE_IMPORT` / `AFTER_IMPORT` | Запущен импорт | `BeforeImportContext` / `AfterImportContext` |
| `AFTER_LOGIN` | Вход выполнен успешно | `AfterLoginContext` |

События `AFTER_CREATE_COMMITTED`, `AFTER_EDIT_COMMITTED` и `AFTER_DELETE_COMMITTED` срабатывают только для backend'ов, откладывающих фиксацию транзакции до конца запроса; сегодня так работает только SQLAlchemy backend. О методах-хуках `after_create_committed`, `after_edit_committed` и `after_delete_committed`, которые их генерируют, см. раздел [Представления](../user-guide/views.md#lifecycle-hooks).

Для события `AFTER_DELETE_COMMITTED` объект `ctx.obj` является отсоединённым (detached) экземпляром: уже загруженные атрибуты остаются доступны для чтения, но обращение к атрибуту, который не был загружен до удаления, вызовет исключение, поскольку соответствующая строка в базе больше не существует.

Каждый контекст — это dataclass, наследующийся от `EventContext`, который содержит поля, общие для всех событий:

| Атрибут | Тип | Описание |
| --- | --- | --- |
| `event` | `AdminEvent` или `str` | Сработавшее событие |
| `request` | `Request` | Обрабатываемый запрос |
| `view_key` | `str` | Значение `key` представления |
| `extra` | `dict` | По умолчанию пустой; свободен для хранения данных в собственной цепочке обработчиков |

Каждый подкласс добавляет поля, относящиеся к соответствующему событию.

События редактирования, вызванные [инлайн-редактированием](../user-guide/inline-edit.md) со страницы списка, содержат `extra["inline"] = True`, а их полезные нагрузки `data` / `old_data` включают только изменённое поле. Всё остальное идентично обычному редактированию, поэтому существующие обработчики не требуют изменений.

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

При такой регистрации `log_deletion` срабатывает только для `order_view`, но не для других представлений админ-панели. Метод `on()` также принимает обработчик напрямую, без формы декоратора:

```python
order_view.events.on(AdminEvent.BEFORE_DELETE, log_deletion)
```

## AdminEventSubscriber: группировка обработчиков

Когда одна задача реагирует на несколько событий, `AdminEventSubscriber` позволяет собрать их в одном классе вместо того, чтобы разбрасывать функции по уровню модуля. Украсьте методы декоратором `@on(AdminEvent.X)` — здесь имеется в виду функция `on` уровня модуля из `starlette_admin.events`, а не метод шины событий, — а затем один раз вызовите `subscribe()`:

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
    """Журналирует каждое создание, обновление или удаление в любом представлении."""

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

`subscribe()` доступен как на `view.events`, так и на `admin.events`. Вызовите его на `view.events`, чтобы ограничить действие подписчика одним представлением.

Один метод может обрабатывать несколько событий: `@on(AdminEvent.AFTER_CREATE, AdminEvent.AFTER_EDIT)` регистрирует один и тот же метод для обоих событий.

## admin.events: делегирование представлениям

`admin.events.on()` принимает те же аргументы, что и `view.events.on()`, плюс `keys=` — список ключей представлений, ограничивающий область действия подписки. Если его не задать (`None`, значение по умолчанию), обработчик получит каждое текущее и будущее model view:

```python
import httpx
from starlette_admin.events import AdminEvent, AfterCreateContext


@admin.events.on(AdminEvent.AFTER_CREATE, keys=["order"])
async def notify_new_order(ctx: AfterCreateContext) -> None:
    async with httpx.AsyncClient() as client:
        await client.post(SLACK_WEBHOOK_URL, json={"text": f"New order: {ctx.pk}"})
```

Этот обработчик вызывает только представление, зарегистрированное с `key="order"`, либо представление, ключ которого по умолчанию разрешается в `"order"`. Событие `AFTER_CREATE` любого другого представления не приведёт к его вызову.

`admin.events.subscribe()` тоже принимает `keys=`, поэтому `AdminEventSubscriber` можно ограничить подмножеством представлений тем же способом:

```python
admin.events.subscribe(AuditSubscriber(), keys=["order", "invoice"])
```

Параметр `keys=` влияет только на события жизненного цикла представлений из таблицы выше: создание, редактирование, удаление, action, экспорт и импорт. Именно так `admin.events` определяет, к каким представлениям применяется обработчик. Событие `AFTER_LOGIN` является событием уровня admin и не привязано ни к одному представлению, поэтому `keys=` для него ничего не делает.

## Приоритет

`on()` принимает именованный аргумент `priority` — целое число, по умолчанию равное `0`. Обработчики одного события выполняются в порядке убывания приоритета, то есть большее число срабатывает раньше:

```python
import logging
from starlette_admin.events import AdminEvent, BeforeDeleteContext

logger = logging.getLogger(__name__)


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=10)
async def validate_can_delete(ctx: BeforeDeleteContext) -> None:
    if ctx.obj.status == "shipped":
        raise ValueError("Cannot delete a shipped order")  # выполняется первым


@order_view.events.on(AdminEvent.BEFORE_DELETE, priority=0)
async def log_deletion(ctx: BeforeDeleteContext) -> None:
    logger.info("deleting order pk=%s", ctx.pk)  # выполняется вторым
```

Обработчики с одинаковым приоритетом выполняются в порядке регистрации. Методы `AdminEventSubscriber` принимают приоритет через `@on(AdminEvent.X, priority=10)`, который передаётся таким же образом.

!!! warning
    Обработчик `BEFORE_DELETE` или любой другой обработчик `BEFORE_*`, выбросивший исключение, останавливает операцию, и последующие обработчики этого события не выполняются. Исключение в обработчике `AFTER_*` превращает уже зафиксированное изменение в неудавшийся запрос. Если сбой не должен проявляться как ошибка админ-панели, заключайте рискованную логику — сетевые вызовы, обращения к сторонним API — в собственный блок `try`/`except` внутри обработчика.

## Расширенный пример

Пример [`examples/05-events`](https://github.com/jowilf/starlette-admin/tree/main/examples/05-events) объединяет все паттерны с этой страницы: переопределения хуков в `PostView`, `AuditSubscriber`, зарегистрированный на `admin.events` для всех представлений, прямую регистрацию обработчиков предупреждений при удалении, экспорте и импорте, обработчик с областью действия `post_view.events` и `CommentModerationSubscriber` с областью действия `comment_view.events`. Запустите его, чтобы увидеть взаимодействие приоритета и области действия в одном приложении.

---

## Что дальше

* **[Представления](../user-guide/views.md)**: методы-хуки `before_*` и `after_*`, на которых строится эта страница.
* **[Действия](../user-guide/actions.md)**: пакетные и строчные действия, генерирующие `BEFORE_ACTION` / `AFTER_ACTION`.
* **[Инлайн-формы](../user-guide/inline-forms.md)**: вложенные записи, создаваемые вместе с родительской записью.
