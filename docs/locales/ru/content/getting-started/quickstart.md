---
title: Быстрый старт
description: Создайте полнофункциональный CRUD-интерфейс администрирования для FastAPI
  и Starlette за считанные минуты с помощью нашего подробного руководства по быстрому
  старту.
source_hash: 19c9639af6caf311e19b134a5042588a3329ca1c3eeb005f000e63d8ac92c7bc
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/getting-started/quickstart/)
<!-- translation-notice:end -->

# Быстрый старт

Создайте полнофункциональный CRUD-интерфейс администрирования для блога за считанные минуты: формы, списки, поиск, импорт и экспорт генерируются автоматически непосредственно из ваших моделей данных.

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

В боковой панели выберите **Posts**, а затем **Create**. Теперь вам доступны страницы списка с пагинацией, деталей, создания, редактирования и удаления. Все эти интерфейсы система генерирует автоматически на основе определения вашей модели.

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

Этот код использует стандартный SQLAlchemy 2.0. Пакет starlette-admin читает метаданные столбцов, сопоставленные с этими атрибутами, чтобы определить, какой именно HTML-элемент ввода нужно сгенерировать. Например, для `str` создаётся текстовое поле, для `bool` — флажок, а для `datetime` — виджет выбора даты и времени.

### Представление

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ("title", "content")
```

`PostView` — это центральный объект для данного ресурса. Атрибут `fields` определяет, какие столбцы отображаются в списке и форме, а `searchable_fields` включает строку поиска. Все настройки внешнего вида и поведения `Post` в панели администрирования находятся в этом единственном классе.

!!! note
    В примере `ModelView` импортируется из `starlette_admin.contrib.sqla`, потому что он использует SQLAlchemy. Если вы работаете с другим бэкендом, например Beanie, MongoEngine или Tortoise ORM, необходимо импортировать `ModelView` из соответствующего contrib-пакета. Конфигурационный API одинаков для всех поддерживаемых бэкендов.

### Панель администрирования

```python
admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(PostView(Post, icon="fa fa-newspaper"))
admin.mount_to(app)
```

Класс `Admin` связывает движок базы данных с пользовательским интерфейсом.

* `add_view` регистрирует ваше представление в боковой панели. Необязательный параметр `icon` принимает любой корректный класс [Font Awesome](https://fontawesome.com/icons).
* `mount_to` подключает приложение панели администрирования к вашему приложению FastAPI или Starlette по пути `/admin`.

!!! warning
    Параметр `secret_key` подписывает cookie-файлы для данных сессии, включая флеш-сообщения и защиту от CSRF. В рабочем окружении обязательно замените пример значения длинной случайной строкой, сгенерированной безопасным способом. Никогда не используйте заглушку в реальном развёртывании.

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

Обновите окно браузера, чтобы увидеть **Posts** и **Tags** в боковой панели. Теперь у каждого ресурса есть собственные полнофункциональные страницы списка, создания, редактирования и удаления.

---

## Следующие шаги

* **[Концепции](concepts.md):** изучите терминологию концепций, представленных здесь, чтобы легче ориентироваться в руководстве пользователя.
* **[Admin](../user-guide/admin.md):** ознакомьтесь со всеми параметрами `Admin(...)`, включая брендинг, темы, аутентификацию, безопасность и интернационализацию.
* **[Views](../user-guide/views.md):** изучите все параметры конфигурации `ModelView`, доступные для настройки отображения ваших данных.
