---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# Добавляем админ-панель в FastAPI за 5 минут с помощью starlette-admin

_2026-07-13_

API готово. Теперь кому-то в команде нужно редактировать данные за ним: исправить опечатку в записи, снять публикацию с поста или проверить, что именно отправил пользователь. Стандартные варианты обычно обходятся дорого:

| Вариант                  | Недостаток                                                                                                 |
| ------------------------ | ---------------------------------------------------------------------------------------------------------- |
| **Собственный CRUD-frontend** | Требует недель разработки и последующего сопровождения.                                                    |
| **Прямой доступ к базе данных** | Создаёт серьёзные риски для безопасности и целостности данных.                                             |
| **Django Admin / Flask Admin** | Вынуждает переписывать приложение на другой framework или опирается на синхронный WSGI, который блокирует ваше асинхронное ASGI-приложение. |
| **starlette-admin**      | **Подключается к вашему приложению мгновенно и без единой строки frontend-кода.**                          |

`starlette-admin` работает с любым приложением на базе Starlette — а именно таким и является FastAPI.

Это руководство проведёт вас от пустого файла до работающей back office-панели за пять минут. Вы создадите списки с пагинацией, поиск, сортируемые колонки, формы создания и редактирования, проверяемые вашими существующими Pydantic-схемами, подтверждение удаления и экспорт в CSV — всё генерируется напрямую из SQLAlchemy-модели.

Полный исполняемый код доступен в [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Минута 1: Установка

Понадобятся три пакета: сам admin-framework, ORM и FastAPI.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic поставляется вместе с FastAPI, что станет важным позже: админ-панель сможет переиспользовать ровно те же схемы, которые ваш API применяет для валидации.

## Минуты 2 и 3: Готовое приложение

Создайте файл `main.py`. Это всё приложение целиком:

```python title="main.py" hl_lines="36-38"
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from sqlalchemy import String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine(
    "sqlite:///blog.db", connect_args={"check_same_thread": False}
)


class Base(DeclarativeBase):
    pass


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str | None] = mapped_column(String(120))
    slug: Mapped[str | None] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    published_at: Mapped[datetime | None]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="dev-only-change-me")
admin.add_view(ModelView(Post, icon="fa fa-blog"))
admin.mount_to(app)

```

Обратите внимание на то, чего здесь нет. Ни шаблонов, ни обработчиков маршрутов для страниц панели, ни сериализаторов, ни конфигурации полей. `starlette-admin` считывает метаданные колонок SQLAlchemy и автоматически выводит весь интерфейс: текстовые поля ограниченной длины для двух колонок типа `String`, textarea для содержимого `Text` и виджет выбора даты и времени для `published_at`.

Три выделенные строки — единственные точки интеграции. Конструктор `Admin` привязывает engine базы данных, метод `add_view` регистрирует модель в боковом меню, а `mount_to` подключает всё это к вашему существующему FastAPI-приложению по пути `/admin`. Ваши API-маршруты остаются нетронутыми: админ-панель работает как смонтированное sub-application.

## Минута 4: Запуск

=== "pip"

    ```bash
    fastapi dev
    ```

=== "uv"

    ```bash
    uv run -- fastapi dev
    ```

Откройте [http://127.0.0.1:8000/admin](http://127.0.0.1:8000/admin) и нажмите **Post** в боковом меню. Из коробки вы получаете:

- Список всех постов с пагинацией и сортировкой.
- Формы создания и редактирования с корректным widget для каждого типа колонки.
- Страницу детального просмотра каждой записи.
- Пакетное удаление с диалогом подтверждения.
- Экспорт текущего списка в CSV и Excel.

Ваш API продолжает обслуживать трафик в штатном режиме. Проверьте [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), чтобы убедиться, что всё работает как прежде.

## Минута 5: Делаем панель по-настоящему своей

Вид по умолчанию предоставляет полноценный CRUD-интерфейс, но настоящая back office-панель заслуживает индивидуальной настройки: вашего порядка полей, вашей компоновки форм и вашего поведения поиска. Именно при наследовании от `ModelView` раскрывается весь потенциал `starlette-admin`. Замените вызов `add_view` на настроенное представление:

```python title="main.py" hl_lines="8 9-13 17 22"
from starlette_admin import ComputedField, SlugField


class PostView(ModelView):
    fields = [
        "id",
        "title",
        SlugField("slug", populate_from="title"),
        ComputedField(
            "word_count",
            label="Word Count",
            getter=lambda request, post: len((post.content or "").split()),
        ),
        "content",
        "published_at",
    ]
    form_layout = [("title", "slug"), "content", "published_at"]
    exclude_fields_from_create = ("word_count",)
    exclude_fields_from_edit = ("word_count",)
    searchable_fields = ("title", "slug", "content", "published_at")
    fields_default_sort = (("published_at", True),)
    search_auto_submit = True


admin.add_view(PostView(Post, icon="fa fa-blog", menu_label="Blog Posts"))

```

В одном этом классе происходят четыре мощных улучшения:

- **`SlugField(populate_from="title")`**: slug генерируется автоматически по мере ввода заголовка оператором — без единой строки собственного JavaScript.
- **`ComputedField`**: отображает значение, которого нет в базе данных. Количество слов вычисляется обычной Python-функцией в момент отрисовки.
- **`form_layout`**: раскладывает форму по логическим строкам: заголовок и slug рядом, содержимое на всю ширину, дата публикации ниже.
- **`search_auto_submit`**: фильтрует список динамически по мере ввода во всех колонках, перечисленных в `searchable_fields`.

## Отсекаем некорректные данные: используйте уже готовую схему

Операторы ошибаются, а значит, админ-панель обязана применять ваши правила на стороне сервера. Преимущество в том, что эти правила вы уже написали. Каждый проект на FastAPI валидирует тела запросов моделями Pydantic, поэтому где-то в вашей кодовой базе наверняка есть схема вроде такой:

```python title="main.py"
from pydantic import BaseModel, Field, field_validator


class PostIn(BaseModel):
    id: int | None = None
    title: str = Field(min_length=3, max_length=120)
    slug: str = Field(
        min_length=3, max_length=160, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    content: str = Field(min_length=10)
    published_at: datetime | None = None

    @field_validator("content")
    @classmethod
    def validate_word_count(cls, v: str) -> str:
        if len(v.split()) < 3:
            raise ValueError("Must contain at least 3 words")
        return v

```

Вместо того чтобы писать логику валидации дважды, передайте админ-панели вашу существующую модель. Расширение `ext.pydantic` предоставляет класс `ModelView`, который пропускает каждую отправленную форму через Pydantic-модель до того, как она попадёт в базу данных. Направьте импорт `ModelView` на расширение, оставьте `Admin` как есть и укажите схему:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

Тело класса `PostView` остаётся ровно тем же; меняется лишь его базовый класс благодаря новому импорту.

Интеграция бесшовна. При создании и редактировании срабатывают все ограничения: границы длины, регулярное выражение для slug и собственный `field_validator`. Каждая ошибка Pydantic отображается непосредственно у соответствующего поля формы прямо внутри неё, неотличимо от формы, написанной вручную. Не забудьте оставить поле `id` необязательным в схеме, чтобы формы создания, у которых изначально нет ID, тоже проходили валидацию.

Так устанавливается единый источник истины. Когда в схему вашего API добавляется новое правило, админ-панель начинает применять его уже со следующего запроса — без каких-либо изменений в её собственном коде.

## Есть свободная минута? Даём постам автора

Реальные данные строятся на связях, и админ-панель обрабатывает их с тем же подходом «ноль конфигурации». Добавьте модель `User` и свяжите её с `Post`:

```python title="main.py"
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))

    posts: Mapped[list["Post"]] = relationship(back_populates="user")

```

```python title="main.py" hl_lines="4 5"
class Post(Base):
    # ... columns from before ...

    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship(back_populates="posts")

```

Зарегистрируйте модель пользователя по той же схеме, основанной на схемах Pydantic. Валидация форматов `EmailStr` и `HttpUrl` выполняется автоматически, а пакет `email-validator` уже входит в состав `fastapi[standard]`:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Поскольку на этот раз настраивать нечего, расширение `ModelView` используется напрямую, без наследования.

Наконец, сделайте автора обязательным, добавив две строки в `PostIn`:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

У поля `user: User` нет значения по умолчанию, поэтому пост без автора будет отклонён так же, как любая другая ошибка валидации. Типом выступает сам класс `User` из SQLAlchemy, потому что админ-панель преобразует выбранный ID в ORM-экземпляр ещё до запуска валидации. Именно поэтому требуется параметр `arbitrary_types_allowed` (`ConfigDict` импортируется из `pydantic`).

Далее добавьте `"user"` в `PostView.fields` и `form_layout`, чтобы автор появился в форме поста. Это поле — не обычный выпадающий список. Это select с автодополнением на стороне сервера, который ищет ваших пользователей по мере ввода, а страница пользователя содержит обратные ссылки на все связанные посты.

!!! note
Функция `create_all` не изменяет существующие таблицы, поэтому перед перезапуском придётся удалить файл `blog.db`, чтобы появилась новая колонка `user_id`.

## Перед развёртыванием

!!! warning
Параметр `secret_key` подписывает session cookie, используемый для защиты от CSRF и flash-сообщений. Замените значение-заглушку длинным случайным значением из настроек перед развёртыванием и обязательно загружайте его из переменных окружения, а не прописывайте в исходном коде.

!!! note
Вызов `Base.metadata.create_all(engine)` в lifespan — это удобство для быстрого старта. В производственном проекте таблицами управляют миграции (например, Alembic). Уберите этот вызов и направьте `Admin` напрямую на ваш существующий engine. `starlette-admin` никогда не изменяет вашу схему — он только читает и записывает строки.

## Это масштабируется далеко за пределы демо

Всё описанное выше использует две модели, но те же механики `ModelView` способны поддерживать огромную back office-панель. Легко реализуются загрузка файлов и изображений, [аутентификация с ролевым доступом](../../user-guide/auth.md), [пользовательские фильтры](../../user-guide/filters.md), [действия над строками и пакетные действия](../../user-guide/actions.md) и полноценная [i18n](../../user-guide/i18n.md). Везде, где встроенного поведения недостаточно, каждый запрос и каждый этап жизненного цикла предоставляет hook для переопределения. Именно так строятся такие паттерны, как [мягкое удаление с корзиной](soft-deletes-trash-view.md).

---

## Что дальше

- **[Концепции](../../getting-started/concepts.md):** терминология всего, что вы только что создали, благодаря которой остальная документация будет читаться легко.
- **[Представления](../../user-guide/views.md):** подробный разбор всех возможностей `ModelView`, включая permission hooks.
- **[Мягкое удаление и корзина для FastAPI](soft-deletes-trash-view.md):** первый продвинутый рецепт, построенный непосредственно на override hooks, представленных здесь.
