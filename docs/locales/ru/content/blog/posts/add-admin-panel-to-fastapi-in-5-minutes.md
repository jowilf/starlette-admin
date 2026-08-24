---
source_hash: e3296a30419e22b9def685804be98cc6f9b065e152edce097f750f28d339bfc2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/blog/posts/add-admin-panel-to-fastapi-in-5-minutes/)
<!-- translation-notice:end -->

# Добавьте панель администрирования в FastAPI за 5 минут с помощью starlette-admin

_2026-07-13_

API готово и выпущено. Теперь кому-то из вашей команды нужно редактировать данные за ним: исправить опечатку в записи, снять публикацию с поста или проверить, что именно отправил пользователь. Стандартные варианты обычно обходятся дорого:

| Вариант                  | Недостаток                                                                                                  |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- |
| **Собственный CRUD-фронтенд** | Требует недель разработки и последующей поддержки.                                                          |
| **Прямой доступ к базе данных** | Создаёт серьёзные риски для безопасности и целостности данных.                                              |
| **Django Admin / Flask Admin** | Вынуждает переписывать приложение на другой фреймворк или полагается на синхронный WSGI, который блокирует ваше асинхронное ASGI-приложение. |
| **starlette-admin**      | **Подключается к вашему приложению мгновенно и без единой строки фронтенд-кода.**                           |

`starlette-admin` работает с любым приложением на базе Starlette, а FastAPI — именно такое приложение.

Это руководство проведёт вас от пустого файла до работающей административной части за пять минут. Вы создадите списки с пагинацией, поиск, сортируемые столбцы, формы создания и редактирования, валидируемые вашими существующими схемами Pydantic, подтверждение удаления и экспорт в CSV — всё это генерируется напрямую из модели SQLAlchemy.

Полный исполняемый код доступен по адресу [`examples/11-sqla-pydantic-fastapi`](<%5Bhttps://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi%5D(https://github.com/jowilf/starlette-admin/tree/main/examples/11-sqla-pydantic-fastapi)>).

## Минута 1: установка

Понадобятся три пакета: сам фреймворк администрирования, ORM и FastAPI.

=== "pip"

    ```bash
    pip install starlette-admin sqlalchemy "fastapi[standard]"
    ```

=== "uv"

    ```bash
    uv add starlette-admin sqlalchemy "fastapi[standard]"
    ```

Pydantic поставляется вместе с FastAPI, что пригодится позже: панель администрирования сможет использовать те же самые схемы, которые ваш API применяет для валидации.

## Минуты 2 и 3: приложение целиком

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

Обратите внимание на то, чего здесь нет. Нет ни шаблонов, ни обработчиков маршрутов для страниц администрирования, ни сериализаторов, ни конфигураций полей. `starlette-admin` читает метаданные столбцов SQLAlchemy и автоматически строит весь интерфейс: текстовые поля с ограничением длины для двух столбцов `String`, многострочное поле для содержимого типа `Text` и выбор даты и времени для `published_at`.

Три выделенные строки — единственные точки интеграции. `Admin` привязывает движок базы данных, `add_view` регистрирует модель в боковом меню, а `mount_to` подключает всё к вашему существующему приложению FastAPI по пути `/admin`. Маршруты вашего API остаются нетронутыми; панель администрирования просто работает как смонтированное субприложение.

## Минута 4: запуск

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
- Формы создания и редактирования с подходящим виджетом ввода для каждого типа столбца.
- Страницу деталей для каждой записи.
- Групповое удаление с диалогом подтверждения.
- Экспорт текущего списка в CSV и Excel.

Ваш API продолжает обслуживать запросы как обычно. Проверьте [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs), чтобы убедиться, что всё работает.

## Минута 5: настройте под себя

Представление по умолчанию даёт полноценный CRUD-интерфейс, но настоящая административная часть заслуживает индивидуальной настройки: свой порядок полей, свою компоновку формы и своё поведение поиска. Именно при наследовании от `ModelView` раскрывается весь потенциал `starlette-admin`. Замените вызов `add_view` настроенным представлением:

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

В этом одном классе происходит четыре мощных улучшения:

- **`SlugField(populate_from="title")`**: автоматически генерирует слаг по мере ввода заголовка — вам не понадобится ни одной строки собственного JavaScript.
- **`ComputedField`**: отображает значение, которого нет в базе данных. Количество слов вычисляется обычной функцией Python во время отрисовки.
- **`form_layout`**: располагает поля формы логичными рядами: заголовок и слаг рядом, содержимое на всю ширину, дата публикации ниже.
- **`search_auto_submit`**: фильтрует список динамически по мере ввода по всем столбцам, перечисленным в `searchable_fields`.

## Отклонение некорректных данных: используйте уже написанную схему

Операторы ошибаются, поэтому панель администрирования должна применять ваши правила на стороне сервера. Преимущество в том, что эти правила вы уже написали. Каждый проект на FastAPI валидирует тела запросов моделями Pydantic, значит где-то в вашей кодовой базе уже есть схема вроде такой:

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

Вместо того чтобы писать логику валидации дважды, передайте панели вашу существующую модель. Расширение `ext.pydantic` предоставляет класс `ModelView`, который пропускает каждую отправленную форму через модель Pydantic до того, как данные попадут в базу. Укажите в импорте `ModelView` расширение, оставьте `Admin` как есть и передайте схему:

```python title="main.py" hl_lines="1 9"
from starlette_admin.contrib.sqla.ext.pydantic import ModelView


class PostView(ModelView):
    ...  # configuration from Minute 5, unchanged


admin.add_view(
    PostView(Post, pydantic_model=PostIn, icon="fa fa-blog", menu_label="Blog Posts")
)

```

Тело класса `PostView` остаётся прежним; меняется только его базовый класс благодаря новому импорту.

Интеграция бесшовная. Все ограничения срабатывают при создании и редактировании: границы длины, регулярное выражение слага и собственный `field_validator`. Каждая ошибка Pydantic сопоставляется с соответствующим полем формы и отображается прямо в нём — неотличимо от формы, собранной вручную. Не забудьте оставить `id` необязательным в схеме, чтобы формы создания, у которых изначально нет идентификатора, проходили валидацию.

Так создаётся единый источник истины. Когда в схему API добавляется новое правило, панель начинает применять его со следующего запроса — без каких-либо изменений кода на стороне администрирования.

## Есть свободная минута? Добавьте авторов к постам

Реальные данные строятся на связях, и панель обрабатывает их с тем же подходом «ноль конфигурации». Добавьте модель `User` и свяжите её с `Post`:

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

Зарегистрируйте модель пользователя по тому же шаблону со схемой Pydantic. `EmailStr` и `HttpUrl` автоматически проверяют формат, а пакет `email-validator` уже входит в состав `fastapi[standard]`:

```python title="main.py" hl_lines="11"
from pydantic import EmailStr, HttpUrl


class UserIn(BaseModel):
    id: int | None = None
    full_name: str = Field(min_length=3)
    email: EmailStr
    website: HttpUrl


admin.add_view(ModelView(User, pydantic_model=UserIn, icon="fa fa-users"))

```

Поскольку на этот раз настраивать нечего, `ModelView` из расширения используется напрямую, без наследования.

Наконец, сделайте автора обязательным, добавив две строки в `PostIn`:

```python title="main.py" hl_lines="2 3 6"
class PostIn(BaseModel):
    # validation runs after relations are resolved, so user is an ORM instance
    model_config = ConfigDict(arbitrary_types_allowed=True)

    # ... fields from before ...
    user: User

```

У `user: User` нет значения по умолчанию, поэтому пост без автора будет отклонён так же, как любая другая ошибка валидации. Типом выступает сам класс SQLAlchemy `User`, потому что панель преобразует выбранный идентификатор в экземпляр ORM до запуска валидации. Именно поэтому требуется `arbitrary_types_allowed` (`ConfigDict` импортируется из `pydantic`).

Затем добавьте `"user"` в `PostView.fields` и `form_layout`, чтобы автор появился в форме поста. Это поле — не обычный выпадающий список. Это элемент выбора с автодополнением на стороне сервера, который ищет пользователей по мере ввода, а страница деталей пользователя ссылается на все связанные посты.

!!! note
`create_all` не изменяет существующие таблицы, поэтому перед перезапуском нужно удалить `blog.db`, чтобы появилась новая колонка `user_id`.

## Перед развёртыванием

!!! warning
Параметр `secret_key` подписывает cookie сессии, используемый для защиты от CSRF и флеш-сообщений. Перед развёртыванием замените заполнитель длинным случайным значением из ваших настроек и убедитесь, что загружаете его из переменных окружения, а не хардкодите в исходном коде.

!!! note
Вызов `Base.metadata.create_all(engine)` в lifespan — удобство для быстрого старта. В производственном проекте таблицами управляют миграции (например, Alembic). Уберите этот вызов и передайте `Admin` ваш существующий движок напрямую. `starlette-admin` никогда не изменяет вашу схему; он только читает и записывает строки.

## Это масштабируется далеко за пределы демо

Во всём примере выше используются две модели, но те же самые механики `ModelView` способны поддерживать большой бэк-офис. Вы легко реализуете загрузку файлов и изображений, [аутентификацию с доступом на основе ролей](../../user-guide/auth.md), [пользовательские фильтры](../../user-guide/filters.md), [действия над строками и групповые действия](../../user-guide/actions.md) и полноценную [i18n](../../user-guide/i18n.md). Когда встроенного поведения недостаточно, каждый запрос и этап жизненного цикла предоставляет хук для переопределения. Именно на этой гибкости построены такие решения, как [мягкое удаление с корзиной](soft-deletes-trash-view.md).

---

## Что дальше

- **[Концепции](../../getting-started/concepts.md):** терминология, стоящая за тем, что вы только что создали, чтобы остальная документация читалась легко.
- **[Представления](../../user-guide/views.md):** подробный разбор всех опций `ModelView`, включая хуки прав доступа.
- **[Мягкое удаление и корзина для FastAPI](soft-deletes-trash-view.md):** первый продвинутый рецепт, построенный прямо на хуках переопределения, описанных здесь.
