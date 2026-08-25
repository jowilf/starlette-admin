---
title: Быстрый старт
description: Создайте полнофункциональный CRUD-интерфейс администрирования для FastAPI
  и Starlette за считанные минуты с помощью нашего подробного руководства по быстрому
  старту.
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# Быстрый старт

Создайте полнофункциональный CRUD-интерфейс администрирования для блога за считанные минуты — с автоматически генерируемыми формами, списками, поиском, импортом и экспортом на основе ваших моделей данных.

## Установка

Установите необходимые пакеты с помощью предпочитаемого менеджера пакетов:

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

!!! note
    Пакет `fastapi[standard]` включает FastAPI CLI, который позволяет запустить сервер разработки командой `fastapi dev`.

## Полный пример

Создайте файл с именем `main.py` и добавьте в него следующий код:

```python
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///blog.db", connect_args={"check_same_thread": False})


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


# Note: This can also be replaced by Starlette(lifespan=lifespan)
app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

## Запуск приложения

Запустите сервер разработки:

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Откройте браузер и перейдите по адресу [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin).

В боковой панели выберите **Posts**, а затем **Create**. Теперь вам доступны страницы со списком с разбивкой на страницы, детальным просмотром, созданием, редактированием и удалением записей. Все эти интерфейсы система генерирует автоматически на основе определения вашей модели.

## Как это работает

В следующих разделах описываются основные компоненты приложения.

### Модель

```python
class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    content: Mapped[str]
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc)
    )
```

Этот код использует стандартный SQLAlchemy 2.0. Пакет starlette-admin считывает метаданные столбцов, сопоставленные с этими атрибутами, чтобы определить, какой именно HTML-элемент ввода следует сгенерировать. Например, для `str` создаётся текстовое поле, для `bool` — флажок, а для `datetime` — виджет выбора даты и времени.

### Представление

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` является центральным объектом для данного ресурса. Атрибут `fields` определяет, какие столбцы отображаются в списке и форме, а `searchable_fields` включает строку поиска. Все настройки внешнего вида и поведения `Post` в панели администрирования сосредоточены в этом единственном классе.

!!! note
    В примере `ModelView` импортируется из `starlette_admin.contrib.sqla`, поскольку он опирается на SQLAlchemy. Если вы используете другой backend, например Beanie, MongoEngine или Tortoise ORM, необходимо импортировать `ModelView` из соответствующего contrib-пакета. Конфигурационный API остаётся единообразным для всех поддерживаемых backend'ов.

### Административная панель

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Класс `Admin` связывает движок базы данных с пользовательским интерфейсом.

* `add_view` регистрирует ваше представление в боковой панели. Необязательный параметр `icon` принимает любой корректный класс [Font Awesome](https://fontawesome.com/icons).
* `mount_to` подключает административное приложение к вашему приложению FastAPI или Starlette по пути `/admin`.

!!! warning
    Параметр `secret_key` подписывает cookies для данных сессии, включая flash-сообщения и защиту от CSRF. В производственной среде необходимо заменить примерное значение длинной случайной строкой, сгенерированной безопасным способом. Никогда не используйте заглушку в рабочем развёртывании.

## Добавление второй модели

Вы можете зарегистрировать неограниченное количество моделей. Например, чтобы добавить модель `Tag` и соответствующее ей представление, определите классы и снова вызовите `add_view`:

```python
class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class TagView(ModelView):
    fields = ["id", "name"]
    searchable_fields = ("name",)


admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.add_view(TagView(Tag, icon="fa fa-tag"))
```

Обновите окно браузера, чтобы увидеть в боковой панели как **Posts**, так и **Tags**. Теперь каждый ресурс располагает собственными полнофункциональными страницами списка, создания, редактирования и удаления.

---

## Следующие шаги

* **[Концепции](concepts.md):** Ознакомьтесь с терминологией концепций, представленных здесь, чтобы увереннее ориентироваться в Руководстве пользователя.
* **[Admin](../user-guide/admin.md):** Изучите все параметры `Admin(...)`, включая брендинг, темы оформления, аутентификацию, безопасность и интернационализацию.
* **[Views](../user-guide/views.md):** Рассмотрите все доступные параметры конфигурации `ModelView` для настройки представления ваших данных.
