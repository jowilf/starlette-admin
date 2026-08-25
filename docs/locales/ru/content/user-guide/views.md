---
title: Представления
description: Узнайте, как настраивать списочные и детальные представления в starlette-admin,
  включая поиск, сортировку и пагинацию.
source_hash: 33fc39d0f563908c141e8f5f8dc89dfdff925d4b959ed1d032ee685346daae57
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/views/)
<!-- translation-notice:end -->

# Представления

`starlette-admin` строит боковую панель из трёх видов представлений: `ModelView` открывает доступ к модели базы данных, `CustomView` отображает отдельную страницу, а `Link` добавляет гиперссылку.

## ModelView

Подкласс `ModelView` — это способ открыть доступ к модели базы данных в админ-панели. Атрибуты класса и переопределения методов этого представления определяют внешний вид ресурса, его поведение и обработку данных.

Все примеры в этом разделе используют следующую конфигурацию SQLAlchemy:

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

Чтобы открыть доступ к модели `Post`, создайте подкласс `ModelView` и настройте его атрибуты.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

Класс представления не выполняет никаких действий, пока вы не зарегистрируете его в экземпляре `Admin`:

```python
from sqlalchemy import create_engine
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///blog.db")
admin = Admin(engine, title="Blog Admin", secret_key="change-me")

# Регистрация представления
admin.add_view(PostView(Post))
```

Пример работающей админ-панели, построенной таким же образом на модели `Post`, см. в [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

Регистрация представления автоматически создаёт интерфейсы с пагинацией, сортировкой и поиском для просмотра списка, просмотра деталей, создания, редактирования и удаления записей. Вам не нужно писать ни маршруты, ни шаблоны.

!!! note
    Класс `ModelView` импортируется из contrib-пакета вашего backend, например `starlette_admin.contrib.sqla`, `.beanie`, `.mongoengine`, `.sqlmodel` или `.tortoise`. **Все атрибуты, описанные ниже, идентичны для всех backend'ов**, поэтому вы сможете позже заменить модель SQLAlchemy на документ MongoEngine, не меняя логику представления.

### Основная конфигурация

#### Именование и маршрутизация

По умолчанию админ-панель формирует URL-маршрутизацию и подписи в интерфейсе на основе имени класса модели. Для модели `Post` используются:

* **Key:** `post` (URL: `/admin/post/list`)
* **Menu label:** `Posts` (пункт в боковой панели)
* **Display name:** `Post` (кнопки интерфейса, такие как **New Post**)

Если сгенерированные значения вас не устраивают, переопределите их при регистрации или в конструкторе.

| Атрибут | Описание | Пример переопределения | Результат в интерфейсе или URL |
| --- | --- | --- | --- |
| **`key`** | Внутренний slug и базовый URL-маршрут. | `key="blog-post"` | `/admin/blog-post/list` |
| **`menu_label`** | Существительное во множественном числе для боковой панели. | `menu_label="Blog Posts"` | **Боковая панель:** Blog Posts |
| **`display_name`** | Существительное в единственном числе для действий и форм. | `display_name="Article"` | **Кнопки:** New Article |

```python
admin.add_view(
    PostView(Post, key="blog-post", menu_label="Blog Posts", display_name="Article")
)
```

#### Выбор и настройка полей {#field-selection-and-customization}

Список `fields` определяет, какие атрибуты модели отображаются в списочном представлении, на странице деталей и в формах. Если его опустить, будут доступны все атрибуты модели.

Комбинируйте строковые имена и явные экземпляры `BaseField`, чтобы управлять widget'ами, валидацией и подписями:

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
    Админ-панель определяет первичный ключ автоматически. Определяйте `pk_attr` только тогда, когда автоматическое определение не срабатывает, например, для кастомного backend без первичного ключа из одного поля.

#### Контекстная видимость полей

Некоторые поля нужны в списке или на странице деталей, но не в форме создания — например, метки времени и системные статусы. Используйте атрибуты `exclude_fields_from_*`, чтобы скрыть поле на определённых поверхностях:

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Скрыть на определённых поверхностях
    exclude_fields_from_create = ["published", "created_at"]
    exclude_fields_from_export = ["content"]
```

Доступные атрибуты исключения заканчиваются на `_create`, `_edit`, `_list`, `_detail`, `_export` и `_import`.

!!! important
    Чтобы разрешить пользователям задавать первичный ключ при создании записи (по умолчанию это отключено), установите `show_pk_in_forms = True`.

#### Компоновка формы

По умолчанию `fields` отображает ваши формы создания и редактирования как плоский вертикальный список. Чтобы реорганизовать интерфейс, не затрагивая определения данных, используйте атрибут `form_layout`.

**Краткая запись через кортежи**

Для простой сетки не нужно импортировать классы widget'ов. Сгруппируйте имена полей в кортеж, чтобы отобразить их рядом в одной строке.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" и "price" делят одну строку; "description" находится под ними
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

**Продвинутые layout-widget'ы**

По мере роста форм структурируйте их с помощью layout-widget'ов. Краткая запись через кортежи работает внутри них:

* **`PanelWidget` или `FieldsetWidget`:** Группируют связанные поля под заголовком или делают секцию сворачиваемой.
* **`TabsWidget`:** Разделяет различные категории данных, например сведения о доставке и SEO-метаданные, которые не нужно показывать одновременно.

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

О многостолбцовых строках с явной шириной, вкладках, статическом содержимом и поведении контроля доступа см. раздел [Компоновка форм](../advanced/form-layout.md).

### Возможности таблицы данных

#### Поиск и сортировка {#search-and-sort}

Управляйте тем, как пользователи находят и упорядочивают данные, с помощью `searchable_fields` и `sortable_fields`.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    searchable_fields = ["title", "content"]
    sortable_fields = ["title", "created_at"]
    fields_default_sort = [("created_at", True)]  # Сначала новые записи
```

* **`searchable_fields`**: Включает конструктор фильтров и глобальное поле поиска. Глобальный поиск выполняет полнотекстовый запрос по этим полям.
* **`sortable_fields`**: Ограничивает столбцы, по заголовкам которых пользователи могут выполнять сортировку. Запрос сортировки по другому полю, переданный через параметры URL, игнорируется.
* **`fields_default_sort`**: Задаёт начальное состояние таблицы. Передайте простую строку для сортировки по возрастанию, кортеж со значением `True` для сортировки по убыванию или кортеж со значением `False` для явной сортировки по возрастанию. Укажите несколько элементов для многостолбцовой сортировки.

#### Пагинация и элементы управления интерфейсом {#pagination-and-ui-controls}

Тонко настройте макет страницы списка с помощью этих атрибутов:

```python
class PostView(ModelView):
    page_size = 25
    page_size_options = [25, 50, 100, -1]  # -1 отображается как "All"
    show_goto_page = True
    search_auto_submit = True
    show_detail_search = True
    row_click_navigate = False
```

* **`page_size` и `page_size_options`**: Лимит пагинации по умолчанию и варианты в выпадающем списке.
* **`show_goto_page`**: Добавляет поле «перейти к странице» для больших наборов данных.
* **`search_auto_submit`**: Фильтрует данные по мере ввода пользователем.
* **`show_detail_search`**: Добавляет поле поиска на страницу деталей для фильтрации встроенных таблиц связей.
* **`row_click_navigate`**: Открывает страницу деталей при выборе любой области строки таблицы. По умолчанию включено. Установите значение `False`, чтобы строки были неактивными, и пользователи переходили к деталям через действия строки. Строки никогда не являются кликабельными для пользователей, у которых проверка `can_view_detail` завершается неудачей.

#### Встроенное редактирование

Вы можете разрешить пользователям изменять определённые поля прямо из списочного представления, не открывая полную форму редактирования.

Используйте атрибут `inline_editable_fields`, чтобы объявить, какие столбцы это поддерживают. При выборе активированной ячейки открывается popover для быстрого обновления.

```python
class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]

    # Включить быстрое редактирование короткого текста и логических переключателей
    inline_editable_fields = ["title", "published"]
```

!!! note "Безопасность и доступ"
    Встроенное редактирование по умолчанию отключено. Когда вы его включаете, существующее разрешение `can_edit` представления по-прежнему контролирует доступ.

Подробности о конфигурации, поведении валидации и полной матрице поддерживаемых типов полей см. в руководстве [Встроенное редактирование](inline-edit.md).

### Связанные данные

Админ-панель обрабатывает связи между данными за вас. Для связи «многие к одному» между `Post` и `Author` добавьте атрибут связи в список `fields`. Пока у обеих моделей зарегистрированы представления, интерфейс отобразит подходящие widget'ы.

```python
class AuthorView(ModelView):
    fields = ["id", "name", "books"]  # 'books' — связь Many


class PostView(ModelView):
    fields = ["id", "title", "author"]  # 'author' — связь One


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


# Author использует ключ по умолчанию ("author"), Post — пользовательский ключ ("post-article")
admin.add_view(AuthorView(Author))
admin.add_view(PostView(Post, key="post-article"))
```

### Строковое представление объекта

Когда админ-панели нужно показать запись как одно значение, она прибегает к первичному ключу. Тогда `Post`, связанный с `Author #3`, отображается как «3» в столбцах связей, что почти ничего не говорит пользователю. Два необязательных метода, определённых на **модели**, а не на представлении, заменяют это значение по умолчанию на что-то осмысленное. Оба принимают текущий `Request` и могут быть синхронными или асинхронными.

#### `__admin_repr__`

Возвращает обычную строку; используется везде, где запись отображается как текст: в столбцах связей на страницах списка и деталей, в хлебных крошках и в сообщениях подтверждения действий.

```python
class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))

    def __admin_repr__(self, request: Request) -> str:
        return self.name
```

При наличии этого метода автор записи отобразится как «Gabriel Garcia Marquez» вместо «3».

#### `__admin_select2_repr__`

Возвращает HTML-фрагмент, который отображает варианты в выпадающих списках `select2`, используемых полями форм для связей, что позволяет дополнить варианты изображениями, значками или дополнительным текстом. Без этого метода админ-панель прибегает к экранированному выводу `__admin_repr__`. Если нет ни одного из методов, используется автоматически сгенерированная сводка полей записи, не являющихся связями.

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

Ограничьте доступ, переопределяя методы проверки разрешений в вашем `ModelView`. Каждый из них возвращает логическое значение, а базовые реализации всегда возвращают `True`.

Этот шаблон напрямую подключается к вашему `AuthProvider`. В примере ниже каждая проверка читает список `roles` из объекта `admin_user` сессии:

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        # Если этот метод возвращает False, представление полностью скрыто из интерфейса
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
        # Изменить объект до записи в базу данных
        obj.title = obj.title.strip()

    async def after_create(self, request: Request, obj: Any) -> None:
        # Запустить побочные эффекты после создания
        print(f"Created post #{obj.id}")
```

Доступные хуки: `before_create`, `after_create`, `after_create_committed`, `before_edit`, `after_edit`, `after_edit_committed`, `before_delete`, `after_delete` и `after_delete_committed`.

#### Хуки после коммита

Хуки `after_create_committed`, `after_edit_committed` и `after_delete_committed` выполняются только после коммита транзакции базы данных. Используйте их для побочных эффектов, которые не должны происходить при откате записи, например отправки электронной почты или постановки фоновых задач в очередь:

```python
class PostView(ModelView):
    async def after_create_committed(self, request: Request, obj: Any) -> None:
        await send_new_post_notification(obj.id)
```

!!! warning
    К моменту выполнения этих хуков сессия запроса уже закоммичена и закрыта. Не записывайте данные в базу через `request.state.session` внутри них. Используйте внешний ввод-вывод или откройте новую сессию базы данных.

!!! important
    В `after_delete_committed` объект `obj` отсоединён от любой сессии. Атрибуты, загруженные до удаления, остаются доступными для чтения, но чтение незагруженного атрибута завершится ошибкой, поскольку строка уже удалена.

!!! note "Поддержка backend'ов"
    Эти хуки генерируют только те backend'ы, которые откладывают коммит до конца запроса. Сегодня это backend SQLAlchemy.

!!! tip
    Для логики, охватывающей несколько представлений, например журнала аудита, используйте вместо этого [события](../advanced/events.md).

### Настройка интерфейса

#### Организация боковой панели {#sidebar-organization}

Группируйте связанные представления в сворачиваемую папку с помощью `DropDown`. Папка может содержать элементы `ModelView`, `CustomView` и `Link`.

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

Атрибуты `exporters` и `importers` определяют, какие форматы доступны для передачи данных. О встроенных вариантах и о написании собственных см. руководство [Экспорт и импорт](export-import.md).

```python
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["json"]
```

### Действия, встроенные формы и шаблоны

Для сложных случаев `ModelView` предлагает ещё три набора возможностей, каждый из которых описан в отдельном руководстве:

* **Действия и действия строки:** Атрибуты `actions` и `row_actions` добавляют пользовательские пакетные и построчные операции помимо CRUD. См. [Действия](actions.md).
* **Встроенные формы:** Атрибут `inlines` встраивает формы создания и редактирования связанной модели внутрь родительского представления. См. [Встроенные формы](inline-forms.md).
* **Шаблоны и ресурсы:** Замените страницы по умолчанию собственными Jinja-шаблонами через `list_template`, `detail_template`, `create_template` или `edit_template`. См. [Шаблоны](../advanced/templates.md).

## CustomView

Не каждая страница админ-панели соответствует модели базы данных. `CustomView` создаёт отдельную страницу в боковой панели на основе widget'ов, пользовательских шаблонов или пользовательских маршрутов.

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

Полный каталог widget'ов, инструкции по созданию дашбордов и пользовательских маршрутов см. в разделе [Пользовательские представления](custom-views.md).

## Link

`Link` добавляет гиперссылку в боковую панель, ведущую на рабочий сайт, внешнюю документацию или другой внутренний инструмент.

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

* **`label`** и **`icon`**: Текст и значок пункта в боковой панели.
* **`url`** и **`target`**: Адрес назначения и атрибут target ссылки.

`admin.add_link(link)` — это тонкая обёртка над `admin.add_view(link)`. Используйте тот вариант, который лучше читается в вашей кодовой базе. Вы также можете вложить `Link` внутрь `DropDown`, как показано в разделе [Организация боковой панели](#sidebar-organization).

---

## Что дальше

* **[Поля](fields.md)**: Полный каталог типов полей.
* **[Компоновка форм](../advanced/form-layout.md)**: Организация форм создания и редактирования с помощью строк, панелей, fieldset'ов и вкладок.
* **[Пользовательские представления](custom-views.md)**: Создание дашбордов и отдельных страниц с помощью widget'ов, шаблонов и пользовательских маршрутов.
* **[Действия и действия строки](actions.md)**: Добавление пакетных и построчных операций помимо CRUD.
* **[Встроенное редактирование](inline-edit.md)**: Позвольте пользователям редактировать отдельное поле строки прямо со страницы списка.
* **[Встроенные формы](inline-forms.md)**: Встраивание форм создания и редактирования связанной модели внутрь родительского представления.
* **[Шаблоны](../advanced/templates.md)**: Подключение собственных Jinja-шаблонов и добавление пользовательских ресурсов.
