---
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

---
title: Основные концепции
description: Изучите архитектурные принципы проектирования starlette-admin: декларативные представления, состояние на основе URL и независимость от backend-моделей.
---

# Основные концепции

После того как вы пройдете Quickstart, создав `PostView` и смонтировав экземпляр admin, стоит изучить архитектурные принципы проектирования фреймворка. Эти базовые концепции закладывают фундамент для остальной документации.

## Один класс на ресурс

Каждый ресурс, которым управляет admin, предоставляется через один выделенный класс. Когда вы создаете подкласс `ModelView` и указываете на модель базы данных, автоматически генерируются пагинированные, сортируемые и фильтруемые представления для всех стандартных CRUD-операций (список, детальный просмотр, создание, редактирование и удаление).

Это избавляет от необходимости писать собственные маршруты или HTML-шаблоны. Все, что определяет внешний вид ресурса, его валидацию и поведение, сосредоточено в этом единственном классе представления.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## Одно представление, любой backend

Представления взаимодействуют с данными через адаптируемый слой backend. Независимо от того, использует ли ваше приложение SQLAlchemy, SQLModel, Beanie, MongoEngine или Tortoise ORM, конфигурационный API остается совершенно одинаковым.

Поля, фильтры, разрешения и lifecycle hooks работают единообразно независимо от того, где хранятся ваши данные. Знания, полученные при работе с одним backend, напрямую переносятся на остальные. Замена источника данных требует лишь обновления инструкций импорта.

```python
# Для backends на SQLAlchemy
from starlette_admin.contrib.sqla import ModelView

# Для backends на Beanie: идентичный API, другой путь импорта
from starlette_admin.contrib.beanie import ModelView
```

## Состояние списка на основе URL

Сортировка, фильтрация, пагинация и критерии поиска синхронизируются непосредственно со строкой запроса в URL. Поскольку сервер полностью формирует состояния списка из этих параметров URL, каждое состояние представления по своей природе можно добавить в закладки и поделиться им.

Если вы отправите коллеге конкретную ссылку административного интерфейса, он увидит ровно те же отфильтрованные строки и ту же конфигурацию сортировки, что и вы.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Поля сами умеют себя отображать

Поля являются саморендерящимися компонентами. Каждый тип поля управляет собственной логикой отображения в трех разных контекстах: ячейка в таблице списка, строка в представлении с деталями и элемент ввода внутри формы.

Создавая представление, вы объявляете экземпляры полей или передаете имена атрибутов, которые backend автоматически сопоставляет с полями. Выберите тип, соответствующий вашей модели данных, а рендерингом займется фреймворк:

* `StringField` для текстовых строк
* `IntegerField` для числовых данных
* `ImageField` для загрузки файлов

```python
from starlette_admin import StringField, IntegerField


class ProductView(ModelView):
    fields = [
        StringField("name"),
        IntegerField("price", help_text="In cents"),
    ]
```

## Декларативные макеты форм

По умолчанию атрибут `fields` отображает формы создания и редактирования как плоский вертикальный список. Чтобы реорганизовать пользовательский интерфейс, не изменяя определения данных, используйте атрибут `form_layout`.

### Краткая запись кортежем

Для простых сетевых макетов сгруппируйте имена полей в кортеж, чтобы они отображались бок о бок в одной строке. Это избавляет от необходимости импортировать сложные классы widget'ов.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" и "price" делят одну строку; "description" находится ниже
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Продвинутые layout-виджеты

Когда формы становятся сложнее, их можно структурировать с помощью layout-виджетов. Краткая запись кортежем нативно работает внутри этих компонентов:

* **`PanelWidget` или `FieldsetWidget`:** используйте эти компоненты, чтобы группировать связанные поля под понятным заголовком или делать секции сворачиваемыми.
* **`TabsWidget`:** используйте этот компонент, когда ресурс содержит отдельные категории данных (например, информация о доставке и SEO-метаданные), которым не обязательно быть видимыми одновременно.

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

## Фильтры привязаны к типам полей

Возможности фильтрации напрямую соответствуют типам данных, благодаря чему пользователи видят только релевантные варианты запросов. `StringField` предоставляет контекстные текстовые опции вроде *contains*, *starts with*, *equals* и *is null*. Целочисленное поле предоставляет числовые условия вроде *greater than* или *between*.

Вы можете ограничить или переопределить эти значения по умолчанию для конкретного поля с помощью параметра `filters`, а также зарегистрировать собственные фильтры для уникальных типов данных.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Используйте свою аутентификацию

Фреймворк остается полностью независимым от схемы ваших пользователей, не предоставляя встроенной модели пользователя. Аутентификация требует реализации единственного метода: `authenticate(request)`.

Подключите этот метод к существующей инфраструктуре аутентификации: локальной таблице базы данных, OAuth-провайдеру или заголовку прокси единого входа (SSO). Возврат объекта `AdminUser` открывает доступ к интерфейсу. Возврат `None` запрещает доступ.

```python
from starlette.requests import Request
from starlette_admin.auth import AdminUser, BaseAuthProvider


class MyAuthProvider(BaseAuthProvider):
    async def authenticate(self, request: Request) -> AdminUser | None:
        if request.session.get("user"):
            return AdminUser(username=request.session["user"])
        return None
```

## Действия выполняются над выбранными строками

Массовые действия (batch actions) работают с несколькими строками, выбранными на верхней панели инструментов, а действия строки (row actions) выполняются инлайн для отдельных записей. Декорирование метода представления с помощью `@action` или `@row_action` автоматически делает метод доступным в пользовательском интерфейсе без ручной регистрации маршрутов.

Вместо возврата строки сообщения из метода действия вызывайте уведомления пользователей напрямую через встроенную утилиту `flash()`.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin import action, flash
from starlette_admin.contrib.sqla import ModelView


class ArticleView(ModelView):
    actions = ["make_published"]

    @action(
        name="make_published",
        text="Mark as published",
        confirmation="Publish selected articles?",
    )
    async def make_published_action(self, request: Request, pks: list[Any]) -> None:
        for article in await self.find_by_pks(request, pks):
            article.status = "published"
        flash(request, f"{len(pks)} article(s) published.", "success")
```

## Нативный экспорт и импорт данных

На каждой странице списка есть диалог экспорта, позволяющий пользователям выбрать область (выбранные строки или текущая страница), поля, формат и имя файла. Активные фильтры и поисковые запросы сохраняются, поэтому экспортированный файл точно совпадает с тем, что отображается на экране.

Фреймворк нативно поддерживает форматы CSV, JSON и PDF. Для дополнительных форматов, таких как Excel (`xlsx`), фреймворк интегрируется с `tablib`, чтобы поддерживать любой совместимый тип файлов. Форматы объявляются как обычные строки расширений. Контроль доступа настраивается на детальном уровне с помощью hook'а `can_export`.

Мастер импорта безопасно загружает массовые данные в этих же форматах. Мастер сначала проверяет загруженный файл на этапе предпросмотра, выделяя ошибки построчно до записи в базу данных, и поддерживает опциональные upsert-операции по первичному ключу. Ограничить доступ к этой функции можно с помощью hook'а `can_import`.

```python
from starlette.requests import Request
from starlette_admin.contrib.sqla import ModelView


class OrderView(ModelView):
    exporters = ["csv", "xlsx"]

    def can_export(self, request: Request) -> bool:
        return request.state.user.is_staff

    def can_import(self, request: Request) -> bool:
        return request.state.user.is_admin
```

## Гибкое файловое хранилище

Управление медиафайлами через `FileField` и `ImageField` опирается на лежащий в основе уровень абстракции `Storage`. Используйте `LocalStorage` для записи на локальный диск или установите опциональную S3-интеграцию командой `pip install starlette-admin[s3]`.

После того как вы укажете полю выбранную конфигурацию хранилища, оно автоматически координирует загрузку файлов, валидацию на backend и отображение на frontend.

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/", name="local")


class AuthorView(ModelView):
    fields = [
        "name",
        ImageField("avatar", storage=local, upload_folder="avatars"),
    ]
```

## Пользовательские представления и dashboard-виджеты

Страницы, не связанные явно с моделью базы данных, например панели метрик или кастомные отчеты, создаются с помощью `CustomView`. Содержимое наполняется через параметр `widget`. Этот параметр принимает либо статический экземпляр `BaseWidget`, либо динамическую функцию, которая вызывается, когда содержимое зависит от входящего запроса.

Вы можете создавать сложные пользовательские интерфейсы, располагая примитивы макета и виджеты визуализации данных в аккуратной иерархии.

```python
from starlette.requests import Request
from starlette_admin import CustomView, CardRowWidget, Col, Breakpoints, StatWidget


async def count_users(request: Request) -> int:
    from sqlalchemy import func, select
    from myapp.models import User

    result = await request.state.session.execute(select(func.count(User.id)))
    return result.scalar()


dashboard = CustomView(
    menu_label="Dashboard",
    path="/",
    widget=CardRowWidget(
        children=[
            Col(
                StatWidget(title="Users", value_callback=count_users),
                breakpoints=Breakpoints(default=12, md=6),
            ),
        ]
    ),
)
```

## События и method hooks

Фреймворк предоставляет две разные точки расширения для выполнения кода во время циклов создания, обновления и удаления:

1. **Lifecycle-методы:** для логики, ограниченной конкретной сущностью, переопределяйте локальные методы вроде `before_create` прямо в вашем классе представления.
2. **Обработчики событий:** для глобальных задач, таких как журналы аудита, инвалидация кеша или webhooks, подписывайтесь на систему `admin.events`.

Оба подхода срабатывают в одних и тех же точках выполнения, что позволяет выбрать вариант, лучше всего подходящий архитектуре вашего приложения.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Ограничен только этим классом представления
    async def before_create(
        self, request: Request, data: dict[str, Any], obj: Any
    ) -> None:
        obj.slug = data["title"].lower().replace(" ", "-")


# Глобальный системный обработчик, охватывающий все классы представлений
async def log_create(ctx: AfterCreateContext) -> None:
    print(f"created {ctx.view_key} #{ctx.pk}")


admin.events.on(AdminEvent.AFTER_CREATE, log_create)
```

---

**Что дальше**

* **[Представления](../user-guide/views.md):** все опции конфигурации `ModelView`.
* **[Поля](../user-guide/fields.md):** полный каталог типов полей.
* **[Макеты форм](../advanced/form-layout.md):** компоновка форм создания и редактирования с помощью строк, панелей и вкладок.
* **[Действия](../user-guide/actions.md):** подробнее о batch- и row-действиях.
