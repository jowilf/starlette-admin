---
title: Основные концепции
description: Изучите архитектурные принципы starlette-admin, включая декларативные
  представления, состояние на основе URL и модели, независимые от бэкенда.
source_hash: 3928a168b4a3ffb7f57c78a8e7eed9fd92a949aa93c59339e49c29cb8ccb8a8c
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/getting-started/concepts/)
<!-- translation-notice:end -->

# Основные концепции

После того как вы пройдёте раздел «Быстрый старт», создав `PostView` и подключив экземпляр панели администрирования, изучите архитектурные принципы фреймворка. Эти основные концепции закладывают фундамент для остальной документации.

## Один класс на ресурс

Каждый ресурс, которым управляет панель администрирования, доступен через один выделенный класс. Когда вы создаёте подкласс `ModelView` и указываете на модель базы данных, автоматически генерируются представления с пагинацией, сортировкой и фильтрацией для всех стандартных операций CRUD (список, детали, создание, редактирование и удаление).

Это избавляет от необходимости писать собственные маршруты или HTML-шаблоны. Всё, что определяет внешний вид ресурса, его валидацию и поведение, находится в этом единственном классе представления.

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
```

## Одно представление — любой бэкенд

Представления взаимодействуют с вашими данными через адаптируемый слой бэкенда. Использует ли ваше приложение SQLAlchemy, SQLModel, Beanie, MongoEngine или Tortoise ORM, конфигурационный API остаётся абсолютно одинаковым.

Поля, фильтры, права доступа и хуки жизненного цикла работают единообразно независимо от того, где хранятся ваши данные. Знания, полученные при работе с одним бэкендом, напрямую переносятся на остальные. Чтобы заменить источник данных, достаточно обновить операторы импорта.

```python
# Для бэкендов на SQLAlchemy
from starlette_admin.contrib.sqla import ModelView

# Для бэкендов на Beanie: идентичный API, другой путь импорта
from starlette_admin.contrib.beanie import ModelView
```

## Состояние списка на основе URL

Сортировка, фильтрация, пагинация и критерии поиска синхронизируются напрямую со строкой запроса URL. Поскольку сервер формирует состояния списка полностью из этих параметров URL, каждое состояние представления по своей природе можно сохранить в закладки и поделиться им.

Если вы отправите коллеге конкретную ссылку на страницу администрирования, он увидит те же отфильтрованные строки и ту же конфигурацию сортировки, что и вы.

```text
/admin/post/list?page=2&order_by=published_at%20desc&q=release

```

## Поля сами умеют себя отображать

Поля — это самостоятельные компоненты отображения. Каждый тип поля управляет собственной логикой отображения в трёх различных контекстах: ячейка в таблице списка, строка на странице деталей и элемент ввода внутри формы.

Когда вы создаёте представление, вы объявляете экземпляры полей или передаёте имена атрибутов, которые бэкенд автоматически сопоставляет с полями. Выберите тип, соответствующий вашей модели данных, а рендерингом займётся фреймворк:

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

## Декларативная компоновка формы

По умолчанию атрибут `fields` отображает формы создания и редактирования как плоский вертикальный список. Чтобы реорганизовать пользовательский интерфейс, не меняя определения данных, используйте атрибут `form_layout`.

### Краткая запись через кортежи

Для базовых сеточных макетов сгруппируйте имена полей в кортеж, чтобы отобразить их рядом в одной строке. Это избавляет от необходимости импортировать сложные классы виджетов.

```python
class ProductView(ModelView):
    fields = ["name", "price", "description"]

    # "name" и "price" делят одну строку; "description" находится ниже
    form_layout = [
        ("name", "price"),
        "description",
    ]
```

### Продвинутые виджеты компоновки

По мере усложнения форм вы можете структурировать их с помощью виджетов компоновки. Краткая запись через кортежи работает внутри этих компонентов нативно:

* **`PanelWidget` или `FieldsetWidget`:** используйте эти компоненты, чтобы сгруппировать связанные поля под понятным заголовком или сделать секции сворачиваемыми.
* **`TabsWidget`:** используйте этот компонент, когда ресурс содержит отдельные категории данных (например, данные доставки и SEO-метаданные), которые не нужно показывать одновременно.

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

Возможности фильтрации напрямую соответствуют типам данных, поэтому пользователи видят только подходящие варианты запросов. Поле `StringField` предоставляет контекстные текстовые опции вроде *contains*, *starts with*, *equals* и *is null*. Числовое поле предоставляет числовые ограничения вроде *greater than* или *between*.

Вы можете ограничить или переопределить эти значения по умолчанию для отдельного поля с помощью параметра `filters`, а также зарегистрировать пользовательские фильтры для уникальных типов данных.

```python
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla.filters import GreaterThanFilter, BetweenFilter


class OrderView(ModelView):
    fields = [
        IntegerField("total", filters=[GreaterThanFilter, BetweenFilter]),
    ]
```

## Подключайте собственную аутентификацию

Фреймворк полностью независим от схемы ваших пользователей, так как не включает встроенную модель пользователя. Аутентификация требует реализации одного метода: `authenticate(request)`.

Подключите этот метод к вашей существующей инфраструктуре аутентификации: локальной таблице базы данных, провайдеру OAuth или заголовку вышестоящего прокси единого входа (SSO). Возврат объекта `AdminUser` открывает доступ к интерфейсу; возврат `None` запрещает его.

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

Групповые действия работают с несколькими строками, выбранными на верхней панели инструментов, а действия над строкой выполняются инлайн-редактированием отдельных записей. Декорирование метода представления с помощью `@action` или `@row_action` автоматически делает метод доступным в пользовательском интерфейсе без ручной регистрации маршрутов.

Вместо возврата строки сообщения из метода действия вызывайте уведомления для пользователей напрямую с помощью встроенной утилиты `flash()`.

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

На каждой странице списка есть диалог экспорта, позволяющий выбрать область (выбранные строки или текущая страница), поля, формат и имя файла. Активные фильтры и условия поиска сохраняются, поэтому экспортированный файл точно соответствует тому, что видно на экране.

Фреймворк нативно поддерживает форматы CSV, JSON и PDF. Для дополнительных форматов, например Excel (`xlsx`), фреймворк интегрируется с `tablib` и поддерживает любой совместимый тип файлов. Форматы объявляются как обычные строки расширений. Управление доступом осуществляется на детальном уровне с помощью хука `can_export`.

Мастер импорта безопасно принимает массовые данные в тех же форматах. Сначала мастер проверяет загруженный файл на этапе предпросмотра, подсвечивая ошибки построчно до записи в базу данных, и поддерживает необязательные операции upsert по первичному ключу. Доступ к этой функции можно ограничить с помощью хука `can_import`.

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

Управление медиафайлами через `FileField` и `ImageField` опирается на абстрактный слой `Storage`. Используйте `LocalStorage` для записи на локальный диск или установите необязательную интеграцию с S3, выполнив команду `pip install starlette-admin[s3]`.

После того как вы укажете полю выбранную конфигурацию хранилища, оно автоматически координирует загрузку файлов, валидацию на бэкенде и отображение на фронтенде.

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

## Пользовательские представления и виджеты дашборда

Страницы, не привязанные явно к модели базы данных, например дашборды метрик или пользовательские отчёты, создаются с помощью `CustomView`. Содержимое заполняется через параметр `widget`. Этот параметр принимает либо статический экземпляр `BaseWidget`, либо динамическую вызываемую функцию, которая выполняется, когда содержимое зависит от входящего запроса.

Вы можете создавать сложные пользовательские интерфейсы, выстраивая примитивы компоновки и виджеты визуализации данных в аккуратную иерархию.

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

## События и хуки методов

Фреймворк предоставляет две различные точки расширения для выполнения кода во время циклов создания, обновления и удаления:

1. **Методы жизненного цикла:** для логики, изолированной в рамках конкретной сущности, переопределите локальные методы вроде `before_create` непосредственно в вашем классе представления.
2. **Обработчики событий:** для глобальных задач, таких как журналы аудита, инвалидация кеша или вебхуки, подпишитесь на систему `admin.events`.

Оба шаблона срабатывают в одних и тех же точках выполнения, что позволяет выбрать подход, лучше всего подходящий для архитектуры вашего приложения.

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.events import AdminEvent, AfterCreateContext


class PostView(ModelView):
    # Изолировано только в рамках этого класса представления
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

* **[Представления](../user-guide/views.md):** все параметры конфигурации `ModelView`.
* **[Поля](../user-guide/fields.md):** полный каталог типов полей.
* **[Компоновка формы](../advanced/form-layout.md):** упорядочивайте формы создания и редактирования с помощью строк, панелей и вкладок.
* **[Действия](../user-guide/actions.md):** подробнее о групповых действиях и действиях над строкой.
