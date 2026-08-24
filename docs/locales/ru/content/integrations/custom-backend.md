---
title: Интеграция пользовательского бэкенда
description: Узнайте, как создать адаптер пользовательского бэкенда для starlette-admin,
  чтобы подключить собственный ORM или API-хранилище данных к интерфейсу администрирования.
source_hash: 1e6a2e4cecb72a0dcb27f5f1988cd060ce3e1085b9261aec475fb4ed3bf33b8a
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/custom-backend/)
<!-- translation-notice:end -->

# Пользовательские бэкенды

`starlette-admin` предоставляет встроенные бэкенды для SQLAlchemy, SQLModel, Beanie, MongoEngine и Tortoise ORM, однако панель администрирования полностью не зависит от способа хранения данных. Каждый бэкенд — это просто подкласс `BaseModelView`. Этот класс преобразует стандартные CRUD-операции в команды, понятные вашему конкретному источнику данных. Независимо от того, используете ли вы REST API, Redis, устаревшую базу данных без ORM или лёгкое документное хранилище вроде TinyDB, процесс реализации остаётся одинаковым.

## Обязательные методы

`BaseModelView` требует реализации шести абстрактных методов. Определив эти шесть методов, вы автоматически получаете весь набор возможностей панели: вывод списка, поиск, сортировку, фильтрацию, пагинацию, создание, редактирование, импорт, экспорт и удаление.

```python
from collections.abc import Sequence
from typing import Any

from starlette.requests import Request
from starlette_admin.filters import FilterGroup
from starlette_admin.views import BaseModelView


class MyBackendView(BaseModelView):
    async def find_all(
        self,
        request: Request,
        skip: int = 0,
        limit: int = 100,
        q: str | None = None,
        sorts: Sequence[tuple[str, str]] | None = None,
        filters: FilterGroup | None = None,
    ) -> Sequence[Any]:
        ...

    async def count(
        self,
        request: Request,
        q: str | None = None,
        filters: FilterGroup | None = None,
    ) -> int:
        ...

    async def find_by_pk(self, request: Request, pk: Any) -> Any:
        ...

    async def find_by_pks(self, request: Request, pks: list[Any]) -> Sequence[Any]:
        ...

    async def create(self, request: Request, data: dict) -> Any:
        ...

    async def edit(self, request: Request, pk: Any, data: dict[str, Any]) -> Any:
        ...

    async def delete(self, request: Request, pks: list[Any]) -> int | None:
        ...

```

| Метод | Когда вызывается | Что возвращает |
| --- | --- | --- |
| **`find_all`** | Страница списка, экспорт | Страницу записей, соответствующих `q`, `sorts` и `filters` |
| **`count`** | Пагинация страницы списка, проверка лимита экспорта | Общее количество записей, соответствующих `q` и `filters` |
| **`find_by_pk`** | Детали, редактирование, одиночное удаление, действия над строкой | Одну запись или `None`, если она не найдена |
| **`find_by_pks`** | Групповые действия, групповое удаление, экспорт выбранных записей | Последовательность записей, соответствующих указанным первичным ключам |
| **`create`** | Отправка формы создания, импорт | Новую созданную запись |
| **`edit`** | Отправка формы редактирования | Обновлённую запись |
| **`delete`** | Групповое удаление, удаление строки | Количество удалённых записей или `None` |

Панель администрирования сама разбирает строку запроса (например, `?page=2&sort=views__desc&q=fire`). Разбирать сырые параметры запроса вам никогда не придётся. К моменту вызова `find_all` или `count` панель уже обработала входные данные:

* **Пагинация** преобразована в `skip` и `limit` (`skip = (page - 1) * page_size`).
* **Поиск** передан в виде простой строки `q`.
* **Сортировка** отформатирована как приоритизированный список кортежей `(field_name, direction)`.
* **Фильтры** разобраны в структурированное дерево `FilterGroup`.

Ваша единственная задача — преобразовать эти структурированные аргументы в родной язык запросов вашего бэкенда.

## Ключ представления, отображаемое имя и поля

Перед отрисовкой представлению `ModelView` требуются четыре основных атрибута, чтобы понять форму данных и маршрутизацию:

| Атрибут | Назначение |
| --- | --- |
| **`key`** | Уникальный URL-слаг (например, `/admin/post/list`) и внутренний ключ для подписок на события. |
| **`display_name`** / **`menu_label`** | Отображаемые имена для интерфейса. `display_name` используется в единственном числе для заголовков форм, а `menu_label` — во множественном числе для навигации и страниц списка. |
| **`pk_attr`** | Имя конкретного поля, которое однозначно идентифицирует запись. |
| **`fields`** | Список экземпляров `BaseField`, определяющий столбцы для отображения и редактирования. |

Встроенные бэкенды заполняют эти атрибуты автоматически, анализируя ваши модели. Например, `ModelView` для SQLAlchemy читает столбцы и первичный ключ из маппера. Этот анализ выполняет подкласс `BaseModelConverter`. Такие конвертеры используют декораторы `@converts(...)`, чтобы сопоставить нативные типы столбцов с соответствующими им `BaseField`.

Если вы создаёте бэкенд без модели, доступной для анализа, — например, REST API или простое словарное хранилище, — необходимо задать эти четыре атрибута явно как атрибуты класса:

```python
class PostView(BaseModelView):
    key = "post"
    display_name = "Post"
    menu_label = "Blog Posts"
    pk_attr = "id"
    fields = [
        IntegerField("id", filters=[]),
        StringField("title"),
        TextAreaField("body"),
        IntegerField("views"),
    ]

```

Явное перечисление полей — самый простой подход для разовых представлений. Однако если вы создаёте переиспользуемый базовый класс `ModelView`, рассчитанный на несколько моделей на пользовательском бэкенде, вместо этого следует написать собственный `BaseModelConverter`. Реализуйте методы `convert()` и `convert_fields_list()`, украсьте обработчики типов декораторами `@converts(...)` и вызывайте конвертер при инициализации. Это позволит конкретным представлениям автоматически наследовать определения полей, как это делают встроенные бэкенды.

## Обработка дерева фильтров

Фильтры передаются в ваши методы в виде объекта `FilterGroup`. Эта структура представляет собой дерево логических узлов AND/OR, содержащих листовые объекты `FilterRule`:

```python
@dataclass
class FilterRule:
    field: str
    filter: str         # The slug of the BaseFilter to apply (e.g., "contains", "gte")
    value: Any = None
    value2: Any = None  # Only populated for filters with has_value2 (e.g., "between")

@dataclass
class FilterGroup:
    logic: str = "and"  # Accepts "and" or "or"
    rules: list["FilterGroup | FilterRule"] = field(default_factory=list)

```

Чтобы преобразовать это дерево в запрос к базе данных, необходимо обойти его рекурсивно. Для каждого `FilterRule` получите соответствующий конкретный класс фильтра из вашего `FilterRegistry` и вызовите его метод `apply()`. Для вложенных узлов `FilterGroup` выполните рекурсию и объедините полученные фрагменты с помощью соответствующего логического оператора.

Ниже показан шаблон `build_query`, используемый в справочном примере TinyDB:

```python
def build_query(
    group: FilterGroup,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    fragments = []
    for rule in group.rules:
        if isinstance(rule, FilterGroup):
            fragment = build_query(rule, fields_by_name, registry)
        else:
            fragment = _build_rule_fragment(rule, fields_by_name, registry)
        if fragment is not None:
            fragments.append(fragment)

    if not fragments:
        return None

    combined = fragments[0]
    for fragment in fragments[1:]:
        combined = (combined | fragment) if group.logic == "or" else (combined & fragment)
    return combined


def _build_rule_fragment(
    rule: FilterRule,
    fields_by_name: dict[str, BaseField],
    registry: FilterRegistry,
) -> QueryInstance | None:
    filter_cls = registry.get_filter(fields_by_name[rule.field], rule.filter)
    if filter_cls is None:
        return None
    ctx = FilterApplyContext(
        query=None, field_name=rule.field, value=rule.value, value2=rule.value2
    )
    return filter_cls().apply(ctx)

```

Метод `apply(ctx)` каждого конкретного фильтра получает объект `FilterApplyContext`, содержащий `query`, имя поля и значения. Он возвращает фрагмент запроса на языке вашего бэкенда. Поскольку этот процесс не изменяет общее состояние, вы можете чисто объединять полученные правила независимо от архитектуры вашей базы данных.

## Справочный пример TinyDB

Каталог [`examples/advanced/03-custom-backend`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/03-custom-backend) содержит полностью работоспособную панель администрирования на базе [TinyDB](https://github.com/msiemens/tinydb). TinyDB — это документное хранилище, сохраняющее данные в локальный JSON-файл. Оно служит отличным ориентиром, поскольку не имеет ORM, то есть каждый метод взаимодействует с хранилищем напрямую.

### Определение модели (`models.py`)

Модель данных — это обычный дата-класс Python без какой-либо специфичной для панели логики:

```python
@dataclass
class Post:
    title: str
    body: str
    tags: list[str]
    views: int = 0
    comments: list[Comment] = field(default_factory=list)
    cover: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] = field(default_factory=list)
    id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if k != "id"}

    @classmethod
    def from_document(cls, doc: Document) -> "Post":
        return cls(**doc, id=doc.doc_id)

    @classmethod
    def search_query(cls, term: str):
        q = Query()
        return (
            q.title.search(term, flags=re.IGNORECASE)
            | q.body.search(term, flags=re.IGNORECASE)
            | q.tags.test(lambda tags: any(re.match(term, tag, re.IGNORECASE) for tag in tags))
        )

```

Метод `search_query` обрабатывает параметр `q`, выполняя полнотекстовый поиск по релевантным полям.

### Реализация представления (`view.py`)

Реализация `PostView` использует `_build_query`, чтобы объединить поисковый запрос с деревом фильтров. И `find_all`, и `count` полагаются на этот вспомогательный метод перед выполнением поиска в TinyDB:

```python
async def _build_query(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> QueryInstance | None:
    query = None
    if q is not None:
        query = Post.search_query(q)
    if filters is not None and not filters.is_empty():
        fields_by_name = {field.name: field for field in self.get_fields_list(request)}
        filter_query = build_query(filters, fields_by_name, self.get_filter_registry())
        if filter_query is not None:
            query = filter_query if query is None else (query & filter_query)
    return query

async def find_all(
    self,
    request: Request,
    skip: int = 0,
    limit: int = 100,
    q: str | None = None,
    sorts: list[tuple[str, str]] | None = None,
    filters: FilterGroup | None = None,
) -> Sequence[Any]:
    query = await self._build_query(request, q, filters)
    docs = self.db.search(query) if query is not None else self.db.all()
    values = [Post.from_document(doc) for doc in docs]
    for sort_by, sort_dir in reversed(sorts or []):
        values.sort(
            key=lambda v, s=sort_by: (getattr(v, s) is None, getattr(v, s)),
            reverse=(sort_dir == "desc"),
        )
    if limit > 0:
        return values[skip : skip + limit]
    return values[skip:]

async def count(
    self,
    request: Request,
    q: str | None = None,
    filters: FilterGroup | None = None,
) -> int:
    query = await self._build_query(request, q, filters)
    return len(self.db.search(query)) if query is not None else len(self.db.all())

```

Поскольку TinyDB не имеет встроенных возможностей сортировки, логика сортировки выполняется средствами Python. Применение сортировок в обратном порядке создаёт надёжную многоключевую сортировку.

Операции записи (`create`, `edit`, `delete`) изменяют базу данных напрямую. Важно, что они также вызывают хуки событий представления, обеспечивая корректное срабатывание событий жизненного цикла:

```python
async def create(self, request: Request, data: dict) -> Any:
    await self.validate_data(data)
    obj = Post(**data)
    await self._emit_before_create(request, data, obj)
    new_id = self.db.insert(obj.to_dict())
    obj = await self.find_by_pk(request, new_id)
    await self._emit_after_create(request, obj)
    return obj

async def delete(self, request: Request, pks: list[Any]) -> int | None:
    ids = list(map(int, pks))
    objs = [Post.from_document(self.db.get(doc_id=i)) for i in ids if self.db.contains(doc_id=i)]
    for obj in objs:
        await self._emit_before_delete(request, await self.get_pk_value(request, obj), obj)
    removed = self.db.remove(doc_ids=ids)
    for obj in objs:
        await self._emit_after_delete(request, await self.get_pk_value(request, obj), obj)
    return len(removed)

```

### Подключение к приложению (`app.py`)

Специализированный подкласс `Admin` не требуется. Базовый `Admin` работает универсально, потому что `BaseModelView` абстрагирует все детали бэкенда:

```python
from pathlib import Path

import uvicorn
from starlette.applications import Starlette
from starlette_admin import BaseAdmin as Admin
from tinydb import TinyDB
from view import PostView

db = TinyDB(Path(__file__).parent / "db.json")

app = Starlette()
admin = Admin(debug=True, secret_key="123456")
admin.add_view(PostView(db))
admin.mount_to(app)

if __name__ == "__main__":
    uvicorn.run("app:app", reload=True)

```

Чтобы протестировать эту реализацию, запустите `uv run app.py` из каталога примера и откройте `http://localhost:8000/admin/`.

## Пользовательские фильтры полей

Фильтры тесно связаны с синтаксисом вашего конкретного бэкенда. Операция «contains» требует совершенно разного кода в TinyDB, SQL и MongoDB. Каждый пользовательский бэкенд должен регистрировать собственные подклассы `BaseFilter` в `FilterRegistry` и возвращать их через `get_filter_registry()`.

Чтобы создать фильтр, унаследуйте его от базового типа вроде `EqualFilter` или `ContainsFilter` и реализуйте метод `apply`:

```python
import re

from starlette_admin.filters import FilterApplyContext
from starlette_admin.filters.string import ContainsFilter
from tinydb import Query
from tinydb.queries import QueryInstance


class TinyDBContainsFilter(ContainsFilter):
    def apply(self, ctx: FilterApplyContext) -> QueryInstance:
        return Query()[ctx.field_name].search(re.escape(ctx.value), flags=re.IGNORECASE)

```

Лучший способ построения реестра — создать подкласс `FilterRegistry` и украсить методы для конкретных типов полей декораторами `@filters(...)`. Именно этот шаблон используют поставляемые бэкенды:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.fields import BaseField
from starlette_admin.filters import FilterRegistry, filters
from starlette_admin.filters.generic import IsNotNullFilter, IsNullFilter
from starlette_admin.filters.numeric import EqualFilter, GreaterThanFilter, LessThanFilter


class TinyDBFilterRegistry(FilterRegistry):
    @filters(BaseField)
    def fallback_filters(self, field: BaseField) -> list[type]:
        # Ensures every field is filterable by null-ness, even without specific registrations.
        return [IsNullFilter, IsNotNullFilter]

    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type]:
        return [TinyDBContainsFilter, EqualFilter, IsNullFilter, IsNotNullFilter]

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type]:
        return [EqualFilter, GreaterThanFilter, LessThanFilter, IsNullFilter, IsNotNullFilter]


class PostView(BaseModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return TinyDBFilterRegistry()

```

Если для поля нет соответствующей записи в реестре и отсутствует явное переопределение `filters=[]`, оно не будет поддерживать фильтрацию. Пример TinyDB намеренно оставляет поле `id` без поддержки фильтрации, используя приём с переопределением `filters=[]`.

Для динамических схем, где поддерживаемые фильтрами типы становятся известны только во время выполнения, `FilterRegistry` предоставляет императивный метод `register(field_type, *filter_classes)`.

## Управление событиями жизненного цикла

Ваш пользовательский бэкенд полностью владеет методами `create`, `edit` и `delete`. Поскольку `BaseModelView` никогда не обращается к вашему источнику данных напрямую, вы должны явно уведомлять его о каждой операции записи. Если этого не делать, две ключевые системы перестают работать незаметно:

1. **Хуки методов:** переопределения `before_create` и `after_create` в вашем `ModelView`.
2. **Подписчики событий:** обработчики, зарегистрированные через `view.events` или `admin.events`.

Уведомление выполняется вызовом парных вспомогательных методов, определённых в `BaseModelView`. Каждый такой метод вызывает соответствующий хук метода и отправляет `AdminEvent`.

| Метод | Вспомогательный метод до записи | Вспомогательный метод после записи |
| --- | --- | --- |
| **`create`** | `_emit_before_create(request, data, obj)` | `_emit_after_create(request, obj)` |
| **`edit`** | `_emit_before_edit(request, data, obj, pk=pk, old_data=old_data)` | `_emit_after_edit(request, obj, pk=pk, old_data=old_data)` |
| **`delete`** | `_emit_before_delete(request, pk, obj)` | `_emit_after_delete(request, pk, obj)` |

Вызов до записи принимает находящийся в памяти объект, созданный из отправленных данных. Это даёт обработчикам последнюю возможность отклонить запись, вызвав исключение. Вызов после записи требует сохранённый объект, прочитанный обратно из базы данных. Именно поэтому метод `create` в примере TinyDB повторно извлекает запись, а не возвращает исходный объект из памяти.

Два дополнительных вспомогательных метода, `_emit_after_create_committed` и `_emit_after_edit_committed`, предназначены для бэкендов с двухфазной фиксацией или семантикой сессий. Полностью пропустите их, если ваша база данных не требует строгой границы транзакции.

Операции экспорта и импорта не требуют ручного подключения событий. Класс `BaseAdmin` обрабатывает эти события жизненного цикла автоматически.

---

### Дополнительные материалы

* **[Представления](../user-guide/views.md)**: изучите параметры конфигурации `BaseModelView`, независимые от бэкенда.
* **[Пользовательские фильтры](../advanced/custom-filters.md)**: узнайте, как писать и регистрировать пользовательские фильтры с нуля.
* **[События](../advanced/events.md)**: разберитесь в полном API подписки на события, включая хуки методов, шину событий и приоритеты выполнения.
