---
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

---
title: Конфигурация Admin
description: Настройте свой экземпляр starlette-admin: кастомизируйте темы, маршрутизацию и общие параметры безопасности.
---

# Admin

Все настройки уровня всего админ-панеля передаются как именованные аргументы в класс `Admin`: заголовок в навигационной панели, путь монтирования, конфигурация CSRF и аутентификации, а также используемая тема оформления.

## Базовое использование

Начните с импорта класса `Admin` из пакета `contrib`, соответствующего вашей объектно-реляционной проекции (ORM):

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

Вот минимальная конфигурация на основе SQLAlchemy:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()

admin = Admin(
    session_provider=engine,
    title="My Admin",
    base_url="/admin",
    secret_key="a-long-random-string",
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

* `title` задаёт текст в навигационной панели и содержимое HTML-тега `<title>`.
* `base_url` определяет префикс пути, по которому монтируется админ-панель.
* `secret_key` подписывает cookie для CSRF и flash-сообщений.
* `add_view` регистрирует представление, а `mount_to` формирует маршруты и middleware админ-панели перед монтированием их в ваше приложение.

Каждый класс `Admin` принимает все описанные ниже параметры конфигурации, а некоторые добавляют поведение, специфичное для конкретного backend:

* `contrib.sqla.Admin(session_provider, ...)` принимает в качестве первого позиционного аргумента `Engine`, `AsyncEngine`, `sessionmaker` или `async_sessionmaker` и автоматически добавляет `DBSessionMiddleware`. `contrib.sqlmodel.Admin` — это тот же класс, реэкспортированный повторно. Подробнее см. [SQLAlchemy](../integrations/sqlalchemy.md) и [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` и `contrib.tortoise.Admin` не принимают дополнительных аргументов конструктора, поскольку Beanie, MongoEngine и Tortoise ORM управляют собственными подключениями вне админ-панели. `mongoengine.Admin` также регистрирует маршрут для раздачи файлов GridFS внутри `mount_to`. Подробнее см. [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) и [Tortoise ORM](../integrations/tortoise.md).

## Полный справочник

Конструктор `Admin` принимает все перечисленные ниже параметры в качестве именованных аргументов.

### Идентичность и брендинг

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Текст в навигационной панели и тег `<title>`. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Логотип в навигационной панели вместо `title`. Передайте обычный URL или функцию, вычисляющую его для каждого запроса, например, для брендинга по арендаторам. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Логотип на странице входа вместо `logo_url`. Если не задан, используется `logo_url`. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | Значение `href` тега `<link>` для favicon. |

`logo_url`, `login_logo_url` и `favicon_url` принимают либо строку, либо функцию вида `(request) -> str | None`. Используйте функцию, если брендинг зависит от запроса, например, в мультитенантном приложении или при обслуживании нескольких доменных имён:

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Монтирование

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | URL-префикс, под которым монтируется админ-панель. |
| `route_name` | `str` | `"admin"` | Имя монтирования в Starlette. Все внутренние ссылки (`list`, `edit`, экспорт, статические файлы) генерируются вызовом `request.url_for(route_name + ":list", ...)`. |

Чтобы запустить несколько экземпляров `Admin` в одном приложении, задайте каждому из них уникальные `base_url` и `route_name`. В противном случае ссылки, сгенерированные одной панелью, могут указывать на другую. См. [Несколько экземпляров Admin](../advanced/multiple-admin.md).


### Шаблоны, статические файлы и тема

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Каталог, в котором сначала ищутся переопределения шаблонов, прежде чем используются встроенные шаблоны. |
| `static_dir` | `str | None` | `None` | Каталог дополнительных статических файлов, раздаваемых вместе со встроенными CSS и JS. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Подкласс темы, определяющий шаблоны макета, набор иконок и статические ресурсы. |

Разделы [Свои темы](../advanced/custom-themes.md) и [Шаблоны](../advanced/templates.md) подробно раскрывают эти параметры.

### Главная страница

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (создаётся `DefaultIndexView` на основе зарегистрированных представлений) | Страница, отображаемая по адресу `base_url`. |

Главная страница по умолчанию — приветственный баннер плюс одна панель для каждого зарегистрированного представления модели с указанием количества записей. Чтобы заменить её, передайте собственный `CustomView`, как правило, подкласс `DefaultIndexView` или любой `CustomView` с `widget`. См. [Свои представления и виджеты](custom-views.md).

### Аутентификация, безопасность и защита данных

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (админ-панель доступна всем) | Контролирует доступ ко всем маршрутам. См. [Аутентификация](auth.md). |
| `secret_key` | `str | None` | `None` (при запуске генерируется случайный ключ с выдачей `UserWarning`) | Подписывает cookie для CSRF и flash-сообщений. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Дополнительное middleware Starlette, выполняемое помимо CSRF-, flash- и auth-middleware, которые админ-панель добавляет самостоятельно. |
| `import_config` | `ImportConfig | None` | `None` (значения по умолчанию `ImportConfig()`) | Ограничения на размер загрузки и защиту от ZIP-бомб для endpoint импорта. |
| `export_config` | `ExportConfig | None` | `None` (значения по умолчанию `ExportConfig()`) | Ограничения на количество строк и скачивание файлов по URL для endpoint экспорта. |

Руководство [Безопасность](security.md) подробно описывает все пять параметров.

### Локаль и часовой пояс

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (только английский язык, без `LocaleMiddleware`) | Включает переведённые строки интерфейса. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (включён) | Преобразует отображаемые дату и время к часовому поясу пользователя. |

Полное руководство см. в разделе [Интернационализация и часовые пояса](i18n.md).

### Отладка {#debugging}

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | При значении `True` вызывает `starlette_admin.logging.configure_logging()` перед запуском, что включает цветной консольный логгирование уровня DEBUG для пакета `starlette_admin`. |

```python
admin = Admin(
    session_provider=engine,
    title="My Admin",
    secret_key="a-long-random-string",
    debug=True,
)
```

Отладочное логирование помогает при разработке. Для каждого запроса логируется выполненное middleware, представление, обработавшее URL, а также причина успешного или неудачного прохождения проверки прав доступа.

!!! warning
    В production держите `debug=False`. Логирование уровня DEBUG многословно и создаёт заметную нагрузку на каждый запрос.

Для более лёгкого варианта вызовите `starlette_admin.logging.configure_logging(level=logging.INFO)` самостоятельно вместо передачи `debug=True`. Вы получите обработчик без подробностей уровня DEBUG.

## Регистрация представлений и монтирование

После создания экземпляра `Admin` зарегистрируйте свои представления и подключите админ-панель к приложению.

```python
admin.add_view(
    ModelView(Post)
)  # Register a view (BaseModelView, CustomView, and so on)
admin.mount_to(app)  # Mount the admin onto your Starlette or FastAPI app
```

### Регистрация представлений

Используйте `add_view`, чтобы добавить компоненты на панель управления. Метод принимает как экземпляр представления, так и его класс; вы можете регистрировать представления моделей, пользовательские страницы, выпадающие меню и внешние ссылки.

### Монтирование приложения

После регистрации всех представлений вызовите `mount_to(app)` ровно один раз, чтобы подключить админ-панель к вашему приложению на Starlette или FastAPI. На этом шаге финализируются конфигурация маршрутизации и безопасности.

!!! important "Порядок действий имеет значение"
    Монтирование фиксирует конфигурацию админ-панели, чтобы каждое представление было корректно связано с маршрутами.

    * Обращение к `admin.app` до монтирования вызывает `RuntimeError`.
    * Регистрация ещё одного представления или повторный вызов `mount_to` после первого монтирования также вызывают `RuntimeError`.

```python
admin.app  # Raises RuntimeError: not mounted yet

admin.mount_to(app)
admin.app  # Returns the mounted sub-application

admin.add_view(ModelView(Comment))  # Raises RuntimeError: already mounted
```

---

**Что дальше**

* **[Безопасность](security.md):** параметр `secret_key`, CSRF и ограничения на экспорт и импорт.
* **[Аутентификация](auth.md):** подключение `auth_provider`.
* **[Несколько экземпляров Admin](../advanced/multiple-admin.md):** запуск более одного `Admin` в одном приложении.
