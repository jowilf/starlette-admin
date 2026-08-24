---
title: Представления
description: Узнайте, как настроить представления списка и деталей в starlette-admin,
  включая поиск, сортировку и пагинацию.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# Представления

`starlette-admin` формирует боковую панель из трёх видов представлений: `ModelView` открывает доступ к модели базы данных, `CustomView` отображает отдельную страницу, а `Link` добавляет гиперссылку.

## ModelView

Подкласс `ModelView` — это способ открыть модель базы данных в панели администрирования. Атрибуты класса и переопределённые методы этого представления определяют, как ресурс выглядит, ведёт себя и обрабатывает данные.

Все примеры в этом разделе используют следующую настройку SQLAlchemy:

```python
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    books: Mapped[list["Post"]] = relationship(back_populates="author")


class Post(Base):
    __tablename__ = "post"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    published: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    author_id: Mapped[int] = mapped_column(ForeignKey("author.id"))
    author: Mapped[Author] = relationship(back_populates="books")
```

### Базовое использование

Чтобы открыть модель `Post`, создайте подкласс `ModelView` и настройте его атрибуты.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

Класс представления ничего не делает, пока вы не зарегистрируете его в экземпляре `Admin`:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Register the view
admin.add_view(PostView(Post))
```

См. [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart) — там собран работающий пример панели администрирования на модели `Post`, построенный таким же способом.

Регистрация представления создаёт интерфейсы с пагинацией, сортировкой и поиском для просмотра списка, просмотра, создания, редактирования и удаления записей. Вам не нужно писать ни маршруты, ни шаблоны.

!!! note
    Вы импортируете `ModelView` из пакета contrib своего бэкенда, например `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` или `.tortoise`. **Все описанные ниже атрибуты одинаковы для всех бэкендов**, поэтому позже можно заменить модель SQLAlchemy на документ MongoEngine, не меняя логику представления.

### Основная конфигурация

#### Именование и маршрутизация

По умолчанию панель администрирования выводит маршрутизацию URL и подписи в интерфейсе из имени класса модели. Для модели `Post` используются:

* **Ключ:** `post` (URL: `/admin/post/list`)
* **Метка меню:** `Posts` (пункт боковой панели)
* **Отображаемое имя:** `Post` (кнопки интерфейса, такие как **New Post**)

Если автоматически выведенные значения не подходят, переопределите их при регистрации или в конструкторе.

| Атрибут | Описание | Пример переопределения | Результат в интерфейсе или URL |
| --- | --- | --- | --- |
| **`key`** | Внутренний слаг и базовый маршрут URL. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | Существительное во множественном числе для боковой панели. | `menu_label="Blog Posts"` | **Боковая панель:** Blog Posts |
| **`display_name`** | Существительное в единственном числе для действий и форм. | `display_name="Article"` | **Кнопки:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Выбор и настройка полей {#field-selection-and-customization}

Список `fields` задаёт, какие атрибуты модели отображаются в представлении списка, на странице деталей и в формах. Если его не указать, будут доступны все атрибуты модели.

Комбинируйте строковые имена и явные экземпляры `BaseField`, чтобы управлять виджетами, валидацией и метками:

```python
from starlette_admin.fields import (
    StringField,
    TextAreaField,
    BooleanField,
    DateTimeField,
)


class PostView(ModelView):
    fields = [
        "id",
        StringField("title", required=True, maxlength=200),
        TextAreaField("content", rows=10),
        BooleanField("published"),
        DateTimeField("created_at", exclude_from_create=True, exclude_from_edit=True),
    ]
```

!!! note
    Панель администрирования определяет первичный ключ автоматически. Задавайте `pk_attr` только тогда, когда определение не срабатывает, например в пользовательском бэкенде без первичного ключа из одного поля.

#### Контекстная видимость полей

Некоторые поля нужны в списке или на странице деталей, но не в форме создания, например временные метки и системные статусы. Используйте атрибуты `exclude_fields_from_*`, чтобы скрыть поле на конкретных экранах:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Hide from specific surfaces
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Доступные атрибуты исключения заканчиваются на `_create`, `_edit`, `_list`, `_detail`, `_export` и `_import`.

!!! important
    Чтобы пользователи могли задавать первичный ключ при создании записи (по умолчанию это отключено), установите `show_pk_in_forms = True`.

#### Компоновка формы

По умолчанию `fields` отображает формы создания и редактирования как плоский вертикальный список. Чтобы реорганизовать интерфейс, не трогая определения данных, используйте атрибут `form_layout`.

**Краткая запись через кортеж**

Для простой сетки не нужно импортировать классы виджетов. Сгруппируйте имена полей в кортеж, чтобы отобразить их рядом в одной строке.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" and "price" share a row; "description" sits below them
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Продвинутые виджеты компоновки**

Когда формы разрастаются, структурируйте их с помощью виджетов компоновки. Краткая запись через кортеж работает и внутри них:

* **`PanelWidget` или `FieldsetWidget`:** группируйте связанные поля под заголовком или сделайте секцию сворачиваемой.
* **`TabsWidget`:** разделяйте разные категории данных, например сведения о доставке и SEO-метаданные, которые не нужно показывать одновременно.

```python
from starlette_admin import TabsWidget


class ProductView(ModelView):
    fields = [
        "name",
        "price",
        "description",
        "sku",
        "weight",
        "shipping_class",
        "meta_title",
        "meta_description",
    ]

    form_layout = [
        TabsWidget(
            tabs=[
                ("Listing", [("name", "price"), "description"]),
                ("Shipping", [("sku", "weight"), "shipping_class"]),
                ("SEO", ["meta_title", "meta_description"]),
            ]
        ),
    ]
```

Подробнее о многостолбцовых строках с явной шириной, вкладках, статичном содержимом и управлении доступом см. в разделе [Компоновка формы](../advanced/form-layout.md).

### Возможности таблицы данных

#### Поиск и сортировка {#search-and-sort}

Управляйте тем, как пользователи находят и упорядочивают данные, с помощью `searchable_fields` и `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Sort newest first
```

* **`searchable_fields`**: включает конструктор фильтров и глобальное поле поиска. Глобальный поиск выполняет полнотекстовый запрос по этим полям.
* **`sortable_fields`**: ограничивает, по каким заголовкам столбцов пользователи могут выполнять сортировку. Запрос сортировки по другому полю, переданный через параметры URL, игнорируется.
* **`fields_default_sort`**: задаёт начальное состояние таблицы. Передайте строку для сортировки по возрастанию, кортеж с `True` для сортировки по убыванию или кортеж с `False` для явной сортировки по возрастанию. Укажите несколько элементов для сортировки по нескольким столбцам.

#### Пагинация и элементы управления интерфейсом {#pagination-and-ui-controls}

Тонко настройте макет страницы списка с помощью этих атрибутов:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 renders as "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` и `page_size_options`**: лимит пагинации по умолчанию и варианты в выпадающем списке.
* **`show_goto_page`**: добавляет поле «перейти к странице» для больших наборов данных.
* **`search_auto_submit`**: фильтрует данные по мере ввода.
* **`show_detail_search`**: добавляет поле поиска на страницу деталей для фильтрации встроенных таблиц связей.
* **`row_click_navigate`**: открывает страницу деталей при щелчке в любом месте строки таблицы. По умолчанию включено. Установите значение `False`, чтобы строки оставались некликабельными и пользователи переходили через действия над строкой. Строки никогда не кликабельны для пользователей, у которых проверка `can_view_detail` не проходит.

#### Инлайн-редактирование

Можно разрешить пользователям изменять отдельные поля прямо из представления списка, не открывая полную форму редактирования.

Используйте атрибут `inline_editable_fields`, чтобы объявить, какие столбцы это поддерживают. Щелчок по активированной ячейке открывает всплывающее окно для быстрого изменения.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Enable quick edits for short text and boolean toggles
    inline_editable_fields = ["title", "published"]
```

!!! note "Безопасность и доступ"
    Инлайн-редактирование отключено по умолчанию. При включении существующее разрешение `can_edit` представления по-прежнему его ограничивает.

О деталях конфигурации, поведении валидации и полной матрице поддерживаемых типов полей см. руководство [Инлайн-редактирование](inline-edit.md).

### Связанные данные

Панель администрирования обрабатывает связи данных за вас. Для связи «многие к одному» между `Post` и `Author` добавьте атрибут связи в список `fields`. Пока у обеих моделей зарегистрированы представления, интерфейс отображает нужные виджеты.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' is a Many relationship


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' is a One relationship


admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post))
```

#### Явное объявление связей

Объявляйте поля `HasOne` или `HasMany` самостоятельно только тогда, когда целевое представление зарегистрировано под пользовательским `key`.

```python
from starlette_admin import HasMany, HasOne, StringField


class AuthorView(ModelView):
    fields = ["id", "name", HasMany("books", key="post-article")]


class PostView(ModelView):
    fields = ["id", "title", HasOne("author", key="author")]


# Author uses default key ("author"), Post uses custom key ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Представление объекта

Когда панели администрирования нужно показать запись одним значением, она использует первичный ключ. Тогда запись `Post`, связанная с автором №3, отображается в столбцах связей как «3», что почти ничего не говорит пользователю. Два необязательных метода, определяемых на **модели**, а не на представлении, заменяют это значение по умолчанию на осмысленное. Оба принимают текущий `Request` и могут быть синхронными или асинхронными.

#### `__admin_repr__`

Возвращает обычную строку; используется везде, где запись отображается как текст: в столбцах связей на странице списка и странице деталей, в навигационной цепочке и в сообщениях подтверждения действий.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

С этим методом автор записи отображается как «Gabriel Garcia Marquez», а не «3».

#### `__admin_select2_repr__`

Возвращает HTML-фрагмент, который отображает варианты в выпадающих списках `select2`, используемых полями форм со связями, поэтому можно дополнить варианты изображениями, бейджами или дополнительным текстом. Без этого метода панель администрирования использует экранированный вывод `__admin_repr__`. Если нет ни одного из методов, используется автоматически созданная сводка по несвязанным полям записи.

```python
from jinja2 import Template


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    avatar_url: Mapped[str] = mapped_column(String(255))

    def __admin_select2_repr__(self, request: Request) -> str:
        template = Template(
            '<div class="d-flex align-items-center">'
            '<span class="avatar me-2" style="background-image: url({{ obj.avatar_url }})"></span>'
            "<span>{{ obj.name }}</span>"
            "</div>",
            autoescape=True,
        )
        return template.render(obj=self)
```

!!! note
    Возвращаемое значение должно быть корректным HTML.

!!! warning
    Экранируйте значения из базы данных, чтобы предотвратить атаки межсайтового скриптинга (XSS). Отображайте фрагмент с помощью Jinja2 и `autoescape=True`, как показано выше, либо экранируйте каждое значение самостоятельно с помощью `html.escape`. Подробнее см. [документацию OWASP](https://owasp.org/www-community/attacks/xss/).

### Безопасность и авторизация {#security-and-authorization}

Ограничивайте доступ, переопределяя методы проверки разрешений в своём `ModelView`. Каждый метод возвращает логическое значение, а базовые реализации всегда возвращают `True`.

Этот шаблон напрямую подключается к вашему `AuthProvider`. В примере ниже каждая проверка читает список `roles` из объекта `admin_user` сессии:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # If this returns False, the view is entirely hidden from the UI
        return any(":post" in role for role in request.state.admin_user.roles)

    def can_create(self, request: Request) -> bool:
        return "create:post" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit:post" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete:post" in request.state.admin_user.roles

    def can_view_detail(self, request: Request) -> bool:
        return "read:post" in request.state.admin_user.roles
```

Подробнее о настройке `AuthProvider` и заполнении объекта `admin_user` см. раздел [Аутентификация](auth.md).

!!! note
    Переопределяйте только те методы, которые хотите ограничить. Не переопределённые методы продолжают разрешать доступ.

### Хуки жизненного цикла {#lifecycle-hooks}

Используйте хуки жизненного цикла, чтобы запускать побочные эффекты или изменять данные непосредственно до или после транзакции с базой данных.

```python
from typing import Any
from starlette.requests import Request


class PostView(ModelView):
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        # Mutate the object before it hits the database
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Trigger post-creation side effects
        print(f"Created post #{obj.id}")
```

Доступные хуки: `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete` и `after_delete_committed`.

#### Хуки после фиксации

`after_create_committed`, `after_edit_committed` и `after_delete_committed` выполняются только после фиксации транзакции базы данных. Используйте их для побочных эффектов, которые не должны происходить при откате записи, например отправки электронной почты или постановки фоновых задач в очередь:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    К моменту выполнения этих хуков сессия запроса уже зафиксирована и закрыта. Не пишите в базу данных через `request.state.session` внутри них. Используйте внешний ввод-вывод или откройте новую сессию базы данных.

!!! important
    В `after_delete_committed` объект `obj` отсоединён от любой сессии. Атрибуты, загруженные до удаления, остаются читаемыми, но обращение к незагруженному атрибуту завершится ошибкой, так как строка уже удалена.

!!! note "Поддержка бэкендов"
    Эти хуки генерируют только бэкенды, откладывающие фиксацию до конца запроса. Сегодня это бэкенд SQLAlchemy.

!!! tip
    Для логики, охватывающей несколько представлений, например журнала аудита, используйте вместо этого [события](../advanced/events.md).

### Настройка интерфейса

#### Организация боковой панели {#sidebar-organization}

Группируйте связанные представления в сворачиваемую папку с помощью `DropDown`. Папка может одновременно содержать элементы `ModelView`, `CustomView` и `Link`.

```python
from starlette_admin import DropDown, Link

admin.add_view(
    DropDown(
        "Content Management",
        icon="fa fa-folder",
        views=[
            PostView(Post, icon="fa fa-newspaper"),
            AuthorView(Author, icon="fa fa-user"),
            Link(
                menu_label="View Live Site",
                icon="fa fa-external-link",
                url="/",
                target="_blank",
            ),
        ],
    )
)
```

#### Экспортёры и импортёры

Атрибуты `exporters` и `importers` задают, какие форматы доступны для передачи данных. О встроенных вариантах и о написании собственных см. руководство [Экспорт и импорт](export-import.md).

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Действия, инлайн-формы и шаблоны

У `ModelView` есть ещё три набора возможностей для сложных случаев, каждый со своим руководством:

* **Действия и действия над строкой:** атрибуты `actions` и `row_actions` добавляют пользовательские групповые операции и операции над строками помимо CRUD. См. [Действия](actions.md).
* **Инлайн-формы:** атрибут `inlines` вкладывает формы создания и редактирования связанной модели внутрь родительского представления. См. [Инлайн-формы](inline-forms.md).
* **Шаблоны и ресурсы:** замените страницы по умолчанию своими шаблонами Jinja через `list_template`, `detail_template`, `create_template` или `edit_template`. См. [Шаблоны](../advanced/templates.md).

## CustomView

Не каждая страница панели администрирования соответствует модели базы данных. `CustomView` создаёт отдельную страницу боковой панели на основе виджетов, пользовательских шаблонов или пользовательских маршрутов.

```python
from starlette_admin import CustomView, StatWidget

admin.add_view(
    CustomView(
        menu_label="System Status",
        icon="fa fa-heart-pulse",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)
```

Полный каталог виджетов, инструкции по дашбордам и пользовательским маршрутам см. в разделе [Пользовательские представления](custom-views.md).

## Link

`Link` добавляет гиперссылку в боковую панель, направляя пользователей на рабочий сайт, внешнюю документацию или другой внутренний инструмент.

```python
from starlette_admin import Link

admin.add_link(
    Link(
        menu_label="View Live Site",
        icon="fa fa-external-link",
        url="/",
        target="_blank",
    )
)
```

* **`label`** и **`icon`**: текст и значок пункта боковой панели.
* **`url`** и **`target`**: адрес назначения и атрибут target ссылки.

`admin.add_link(link)` — тонкая обёртка над `admin.add_view(link)`. Используйте тот вариант, который лучше читается в вашем коде. Можно также вложить `Link` внутрь `DropDown`, как показано в разделе [Организация боковой панели](#sidebar-organization).

---

## Что дальше

* **[Поля](fields.md)**: полный каталог типов полей.
* **[Компоновка формы](../advanced/form-layout.md)**: располагайте формы создания и редактирования с помощью строк, панелей, групп полей и вкладок.
* **[Пользовательские представления](custom-views.md)**: создавайте дашборды и отдельные страницы с помощью виджетов, шаблонов и пользовательских маршрутов.
* **[Действия и действия над строкой](actions.md)**: добавляйте групповые операции и операции над строками помимо CRUD.
* **[Инлайн-редактирование](inline-edit.md)**: позвольте пользователям редактировать одно поле строки прямо со страницы списка.
* **[Инлайн-формы](inline-forms.md)**: вкладывайте формы создания и редактирования связанной модели внутрь родительского представления.
* **[Шаблоны](../advanced/templates.md)**: подключите свои шаблоны Jinja и добавьте собственные ресурсы.
