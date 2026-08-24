---
title: Интеграция с MongoEngine
description: Узнайте, как подключить модели MongoEngine к starlette-admin, чтобы управлять
  данными MongoDB через административную панель.
source_hash: 8782d539b644b3b326c33fe888719c2964127823189e389afa0546976021964c
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/integrations/mongoengine/)
<!-- translation-notice:end -->

# Интеграция с MongoEngine

MongoEngine представляет документы MongoDB в виде синхронных классов Python с использованием API полей в стиле Django. Модуль `starlette_admin.contrib.mongoengine` предоставляет специализированные классы `Admin` и `ModelView`, которые строят административные представления непосредственно на основе ваших определений `mongoengine.Document`.

**Ключевые возможности:**

* Автоматическое преобразование типов полей, связей и встроенных документов.
* Поддержка загрузки файлов на основе GridFS через `FileField` и `ImageField` из коробки.

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

Вы должны установить соединение с MongoDB до того, как любой запрос достигнет административного интерфейса. Лучший способ гарантировать выполнение этого условия — обернуть логику подключения внутри контекстного менеджера `lifespan` вашего основного приложения.

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

Конструктор `ModelView` принимает класс `mongoengine.Document` напрямую. Список полей, формы и фильтры автоматически формируются на основе полей документа.

## Основные классы: Admin и ModelView

### Класс `mongoengine.Admin`

Класс `mongoengine.Admin` расширяет базовый `Admin`, добавляя специализированный маршрут: `/api/file/{db}/{col}/{pk}`. Этот маршрут передаёт файл GridFS из браузера напрямую.

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

Если атрибут `fields` не задан в вашем подклассе `ModelView`, по умолчанию включаются все поля документа в порядке их объявления.

Атрибуты `key`, `menu_label` и `display_name` подчиняются строгому порядку определения значений:

1. Аргумент конструктора.
2. Атрибут уровня класса, заданный в подклассе.
3. Значение, вычисляемое на основе имени класса документа (`key` становится именем после слагификации, `menu_label` — плюрализованным «причёсанным» именем, а `display_name` — единичным «причёсанным» именем).

```python
from starlette_admin.contrib.mongoengine import ModelView


class CategoryView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ["name"]
```

## Реестр фильтров {#filter-registry}

Для каждого типа поля предусмотрен фиксированный набор фильтров, предоставляемых реестром `MongoEngineFilterRegistry`. Эти значения по умолчанию можно переопределить для отдельного поля с помощью аргумента `filters=[...]`.

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
    `ObjectIdField` соответствует полю `id` документа.

Под капотом метод `apply()` каждого фильтра возвращает фрагмент `Q` MongoEngine для своего конкретного условия. Вложенные деревья `FilterGroup` затем комбинируют эти фрагменты с помощью битовых операторов (`&` или `|`) перед выполнением запроса. Подробнее см. документацию [Filters](../user-guide/filters.md).

## Встроенные документы

Поле `EmbeddedDocumentField` в MongoEngine преобразуется в `CollectionField`. Этот процесс рекурсивно преобразует каждое поле встроенного документа в его собственное подполе:

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

* Поле `address` отображается как вложенная подформа при создании и редактировании и как вложенный блок на странице детального просмотра.
* Поле `comments` (экземпляр `EmbeddedDocumentListField`) преобразуется в `ListField` из `CollectionField`. Оно отображается как повторяющаяся группа подформ — по одной для каждой записи списка.

## Полный рабочий пример

В этом разделе представлен полный готовый к запуску пример интеграции MongoEngine со `starlette-admin`.

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

Откройте в браузере страницу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin), чтобы просмотреть административную панель и работать с ней.

> **Расширенный пример:** приложение [`examples/16-mongoengine`](https://github.com/jowilf/starlette-admin/tree/main/examples/16-mongoengine) в репозитории содержит полнофункциональный пример. Оно включает инлайн-представления (inline views), события (events), пользовательские действия над строками и пакетные действия, а также загрузку изображений и файлов через GridFS.

---

## Что читать дальше

* **[Views](../user-guide/views.md)**: ознакомьтесь с параметрами конфигурации `BaseModelView`, не зависящими от backend.
* **[Fields](../user-guide/fields.md):** подробное руководство по каждому типу поля и его атрибутам, включая `CollectionField`.
* **[Filters](../user-guide/filters.md):** изучите интерфейс конструктора фильтров и узнайте, как написать собственный фильтр.
* **[Beanie](beanie.md):** откройте для себя асинхронную альтернативу для MongoDB на основе Pydantic.
