---
title: Интеграция с MongoEngine
description: Узнайте, как подключить модели MongoEngine к starlette-admin, чтобы управлять
  данными MongoDB через панель администрирования.
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# Интеграция с MongoEngine

MongoEngine представляет документы MongoDB в виде синхронных классов Python с API полей в стиле Django. Модуль `starlette_admin.contrib.mongoengine` предоставляет специализированные классы `Admin` и `ModelView`, которые строят представления администрирования непосредственно на основе ваших определений `mongoengine.Document`.

**Ключевые возможности:**

* Автоматическое преобразование типов полей, связей и встроенных документов.
* Поддержка загрузки файлов через GridFS для полей `FileField` и `ImageField` из коробки.

## Установка

=== "pip"

    ```bash
    pip install starlette-admin mongoengine
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine
    ```

## Минимальный пример

Необходимо установить соединение с MongoDB до того, как любой запрос достигнет интерфейса администрирования. Лучший способ гарантировать выполнение этого условия — обернуть логику подключения в контекстный менеджер `lifespan` вашего основного приложения.

```python
from contextlib import asynccontextmanager

import mongoengine as me
from starlette.applications import Starlette
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Category(me.Document):
    name = me.StringField(required=True, min_length=2, max_length=50)

    meta = {"collection": "categories"}


@asynccontextmanager
async def lifespan(app: Starlette):
    me.connect(db="podcast_admin", host="mongodb://localhost:27017")
    yield
    me.disconnect()


app = Starlette(lifespan=lifespan)

admin = Admin(title="Podcast Admin", secret_key="change-me-in-production")
admin.add_view(ModelView(Category, icon="fa fa-tags"))
admin.mount_to(app)
```

`ModelView` принимает класс `mongoengine.Document` напрямую. Он автоматически выводит список полей, формы и фильтры из полей документа.

## Основные классы: Admin и ModelView

### Класс `mongoengine.Admin`

Класс `mongoengine.Admin` расширяет базовый `Admin`, добавляя специализированный маршрут: `/api/file/{db}/{col}/{pk}`. Этот маршрут передаёт файл из GridFS напрямую в браузер.

Поскольку каждая загрузка через `FileField` и `ImageField` в модели MongoEngine сохраняется в GridFS, этот маршрут необходим для отдачи таких файлов. Всегда используйте `mongoengine.Admin` вместо базового `Admin`.

### Класс `mongoengine.ModelView`

В отличие от базового класса, конструктор `mongoengine.ModelView` принимает позиционный аргумент `document` вместо декларативного класса модели:

```python
def __init__(
    self,
    document: type[me.Document],
    icon: str | None = None,
    display_name: str | None = None,
    menu_label: str | None = None,
    key: str | None = None,
    converter: BaseMongoEngineModelConverter | None = None,
):

```

Если не задать атрибут `fields` в вашем подклассе `ModelView`, по умолчанию он будет включать все поля документа в порядке их объявления.

Атрибуты `key`, `menu_label` и `display_name` следуют строгому порядку определения значений:

1. Аргумент конструктора.
2. Атрибут уровня класса, заданный в подклассе.
3. Значение, выведенное из имени класса документа (`key` становится именем в формате slug, `menu_label` — множественным форматированным именем, а `display_name` — единственным форматированным именем).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Реестр фильтров {#filter-registry}

Для каждого типа поля предусмотрен фиксированный набор фильтров, предоставляемый реестром `MongoEngineFilterRegistry`. Вы можете переопределить эти значения по умолчанию для отдельного поля с помощью аргумента `filters=[...]`.

| Тип поля | Доступные фильтры |
| --- | --- |
| `StringField` | contains, not contains, starts with, ends with, equals, not equals, is null, is not null |
| `TextAreaField` | contains, not contains, starts with, ends with, is null, is not null |
| `EnumField` | equals, not equals, in, not in, is null, is not null |
| `NumberField` | equals, not equals, greater than, less than, between, is null, is not null |
| `FloatField` | equals, not equals, greater than, less than, between, is null, is not null |
| `DateField` | equals, between, in the past, in the future, is null, is not null |
| `DateTimeField` | equals, between, in the past, in the future, is null, is not null |
| `BooleanField` | is true, is false, is null, is not null |
| `TagsField` | in, not in, is null, is not null |
| `RelationField` | is null, is not null |
| `ObjectIdField` | equals, not equals, in, not in, is null, is not null |

!!! note
    Поле `ObjectIdField` представляет собой `id` документа.

Внутри метод `apply()` каждого фильтра возвращает фрагмент `Q` MongoEngine для своего конкретного условия. Вложенные деревья `FilterGroup` затем объединяют эти фрагменты с помощью побитовых операторов (`&` или `|`) перед выполнением запроса. Подробнее см. документацию [Фильтры](../user-guide/filters.md).

## Встроенные документы

Поле `EmbeddedDocumentField` в MongoEngine преобразуется в `CollectionField`. При этом каждое поле встроенного документа рекурсивно преобразуется в собственное подполе:

```python
import mongoengine as me
from starlette_admin.contrib.mongoengine import Admin, ModelView


class Address(me.EmbeddedDocument):
    street = me.StringField()
    city = me.StringField()


class Comment(me.EmbeddedDocument):
    content = me.StringField()


class Post(me.Document):
    name = me.StringField()
    address = me.EmbeddedDocumentField(Address)
    comments = me.EmbeddedDocumentListField(Comment)


class PostView(ModelView):
    fields = ["id", "name", "address", "comments"]


admin = Admin()
admin.add_view(PostView(Post))
```

В этом примере:

* Поле `address` отображается как вложенная подформа при создании и редактировании и как вложенный блок на странице деталей.
* Поле `comments` (типа `EmbeddedDocumentListField`) преобразуется в `ListField` из `CollectionField`. Оно отображается как повторяемая группа подформ — по одной для каждого элемента списка.

## Полный рабочий пример

Этот раздел содержит полный запускаемый пример интеграции MongoEngine со `starlette-admin`.

### 1. Установите зависимости

=== "pip"

    ```bash
    pip install starlette-admin mongoengine "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv install starlette-admin mongoengine "fastapi[standard]"
    ```

Пакет `fastapi[standard]` включает FastAPI CLI, что позволяет запустить сервер разработки командой `fastapi dev`.

### 2. Создайте приложение

```python title="main.py"
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum

import mongoengine as me
from fastapi import FastAPI
from starlette.requests import Request
from starlette_admin import SlugField
from starlette_admin.contrib.mongoengine import Admin, ModelView

MONGO_URI = "mongodb://localhost:27017"


class PostStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class Author(me.Document):
    name = me.StringField(required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.name

    meta = {"collection": "authors"}


class Post(me.Document):
    title = me.StringField(required=True)
    slug = me.StringField(required=True, unique=True)
    content = me.StringField(required=True)
    status = me.EnumField(PostStatus, default=PostStatus.DRAFT)
    created_at = me.DateTimeField(default=lambda: datetime.now(timezone.utc))
    author = me.ReferenceField(Author, required=True)

    def __admin_repr__(self, request: Request) -> str:
        return self.title

    meta = {"collection": "posts"}


class AuthorView(ModelView):
    fields = ["id", "name"]


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        "content",
        "status",
        "created_at",
        "author",
    ]
    exclude_fields_from_create = ["created_at"]
    exclude_fields_from_edit = ["created_at"]
    searchable_fields = ["title", "content", "status"]
    fields_default_sort = [("created_at", True)]


@asynccontextmanager
async def lifespan(app: FastAPI):
    me.connect(db="blog", host=MONGO_URI)
    yield
    me.disconnect()


app = FastAPI(lifespan=lifespan)

admin = Admin(title="Blog Admin", secret_key="change-me")
admin.add_view(AuthorView(Author, icon="fa fa-user"))
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

### 3. Запустите сервер

Запустите сервер разработки FastAPI:

=== "pip"

    ```bash
    fastapi dev
    ```


=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Откройте в браузере адрес [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы просмотреть дашборд администрирования и поработать с ним.

> **Расширенный пример:** приложение [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) в репозитории содержит полнофункциональный пример. Оно включает инлайн-представления, события, пользовательские действия над строками и групповые действия, а также загрузку изображений и файлов через GridFS.

---

## Что читать дальше

* **[Представления](../user-guide/views.md)**: изучите параметры конфигурации `BaseModelView`, независимые от бэкенда.
* **[Поля](../user-guide/fields.md):** подробное руководство по каждому типу поля и его атрибутам, включая `CollectionField`.
* **[Фильтры](../user-guide/filters.md):** изучите интерфейс конструктора фильтров и узнайте, как написать пользовательский фильтр.
* **[Beanie](beanie.md):** познакомьтесь с асинхронной альтернативой для MongoDB на основе Pydantic.
