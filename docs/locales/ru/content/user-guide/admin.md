---
title: Конфигурация панели администрирования
description: Настройте свой экземпляр starlette-admin — темы, маршрутизацию и общие
  параметры безопасности.
source_hash: 9e9a48b9e7e2e565b504c6d831eaf0e7a911489399ffb480ea19e50d0f8ad843
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/admin/)
<!-- translation-notice:end -->

# Панель администрирования

Все настройки уровня администрирования вы передаёте как именованные аргументы в класс `Admin`: заголовок навигационной панели, путь монтирования, конфигурацию CSRF и аутентификации, а также используемую тему.

## Базовое использование

Начните с импорта класса `Admin` из пакета `contrib`, соответствующего вашему ORM:

```python
from starlette_admin.contrib.sqla import Admin  # SQLAlchemy
from starlette_admin.contrib.sqlmodel import Admin  # SQLModel
from starlette_admin.contrib.beanie import Admin  # Beanie
from starlette_admin.contrib.mongoengine import Admin  # MongoEngine
from starlette_admin.contrib.tortoise import Admin  # Tortoise ORM
```

Вот минимальная конфигурация с использованием SQLAlchemy:

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

* `title` задаёт текст на навигационной панели и HTML-тег `<title>`.
* `base_url` определяет префикс пути, по которому монтируется панель администрирования.
* `secret_key` подписывает CSRF- и flash-cookie.
* `add_view` регистрирует представление, а `mount_to` строит маршруты и middleware панели администрирования, прежде чем смонтировать их в ваше приложение.

Каждый класс `Admin` принимает все описанные ниже параметры конфигурации, а некоторые добавляют специфичное для бэкенда поведение:

* `contrib.sqla.Admin(session_provider, ...)` принимает первым позиционным аргументом `Engine`, `AsyncEngine`, `sessionmaker` или `async_sessionmaker` и автоматически добавляет `DBSessionMiddleware`. `contrib.sqlmodel.Admin` — это тот же класс, реэкспортированный. См. [SQLAlchemy](../integrations/sqlalchemy.md) и [SQLModel](../integrations/sqlmodel.md).
* `contrib.beanie.Admin`, `contrib.mongoengine.Admin` и `contrib.tortoise.Admin` не принимают дополнительных аргументов конструктора, потому что Beanie, MongoEngine и Tortoise ORM управляют своими подключениями вне панели администрирования. `mongoengine.Admin` также регистрирует маршрут раздачи файлов GridFS в `mount_to`. См. [Beanie](../integrations/beanie.md), [MongoEngine](../integrations/mongoengine.md) и [Tortoise ORM](../integrations/tortoise.md).

## Полный справочник

Конструктор `Admin` принимает все перечисленные ниже параметры как именованные аргументы.

### Идентификация и брендинг

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `title` | `str` | `"Admin"` | Текст на навигационной панели и тег `<title>`. |
| `logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Логотип на навигационной панели вместо `title`. Передайте обычный URL или функцию, которая определяет его для каждого запроса, например для брендинга по арендаторам. |
| `login_logo_url` | `str | Callable[[Request], str | None] | None` | `None` | Логотип на странице входа вместо `logo_url`. Если не задан, используется `logo_url`. |
| `favicon_url` | `str | Callable[[Request], str | None] | None` | `None` | Атрибут href тега `<link>` фавикона. |

Параметры `logo_url`, `login_logo_url` и `favicon_url` принимают либо строку, либо функцию вида `(request) -> str | None`. Используйте функцию, когда брендинг зависит от запроса, например в мультитенантном приложении или при обслуживании нескольких доменных имён:

```python
def logo_for_tenant(request):
    return f"https://cdn.example.com/{request.state.tenant}/logo.png"


admin = Admin(engine, title="My Admin", logo_url=logo_for_tenant)
```

### Монтирование

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `base_url` | `str` | `"/admin"` | Префикс URL, под которым монтируется панель администрирования. |
| `route_name` | `str` | `"admin"` | Имя монтирования Starlette. Все внутренние ссылки (`list`, `edit`, экспорт, статические файлы) генерируются вызовом `request.url_for(route_name + ":list", ...)`. |

Чтобы запустить несколько экземпляров `Admin` в одном приложении, задайте каждому уникальные `base_url` и `route_name`. Иначе ссылки, сгенерированные одной панелью, могут указывать на другую. См. [Несколько экземпляров Admin](../advanced/multiple-admin.md).


### Шаблоны, статические файлы и тема

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `templates_dir` | `str` | `"templates"` | Каталог, который проверяется на переопределения шаблонов до обращения к встроенным шаблонам. |
| `static_dir` | `str | None` | `None` | Каталог дополнительных статических файлов, которые раздаются вместе со встроенными CSS и JS. |
| `theme` | `BaseTheme` | `DefaultTheme()` | Подкласс темы, определяющий шаблоны компоновки, набор значков и статические ресурсы. |

Разделы [Пользовательские темы](../advanced/custom-themes.md) и [Шаблоны](../advanced/templates.md) подробно описывают эти параметры.

### Главная страница

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `index_view` | `CustomView | None` | `None` (создаётся `DefaultIndexView` на основе зарегистрированных представлений) | Страница, отображаемая по адресу `base_url`. |

Главная страница по умолчанию — это приветственный баннер плюс одна панель для каждого зарегистрированного представления модели, показывающая количество записей. Чтобы заменить её, передайте собственный `CustomView` — обычно подкласс `DefaultIndexView` или любой `CustomView` с виджетом. См. [Пользовательские представления и виджеты](custom-views.md).

### Аутентификация, безопасность и защита данных

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `auth_provider` | `BaseAuthProvider | None` | `None` (панель доступна всем) | Ограничивает доступ ко всем маршрутам. См. [Аутентификация](auth.md). |
| `secret_key` | `str | None` | `None` (при запуске генерируется случайный ключ с предупреждением `UserWarning`) | Подписывает CSRF- и flash-cookie. |
| `middlewares` | `Sequence[Middleware] | None` | `None` | Дополнительное middleware Starlette, которое выполняется помимо CSRF-, flash- и auth-middleware, добавляемых самой панелью. |
| `import_config` | `ImportConfig | None` | `None` (значения по умолчанию `ImportConfig()`) | Ограничения на размер загрузки и защиту от ZIP-бомб для эндпоинта импорта. |
| `export_config` | `ExportConfig | None` | `None` (значения по умолчанию `ExportConfig()`) | Ограничение количества строк и лимиты скачивания по URL-файлам для эндпоинта экспорта. |

Руководство [Безопасность](security.md) подробно рассматривает все пять параметров.

### Локаль и часовой пояс

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `i18n_config` | `I18nConfig | None` | `None` (только английский язык, без `LocaleMiddleware`) | Включает переведённые строки интерфейса. |
| `timezone_config` | `TimezoneConfig | None` | `TimezoneConfig()` (включено) | Преобразует отображаемые дату и время в часовой пояс пользователя. |

Полное руководство см. в разделе [Интернационализация и часовые пояса](i18n.md).

### Отладка {#debugging}

| Параметр | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `debug` | `bool` | `False` | Если значение равно `True`, перед запуском вызывается `starlette_admin.logging.configure_logging()`, которая включает цветной вывод журнала уровня DEBUG для пакета `starlette_admin` в консоль. |

```python
admin = Admin(
    session_provider=engine, title="My Admin", secret_key="a-long-random-string", debug=True
)
```

Журналирование отладки помогает при разработке. Для каждого запроса записывается выполненное middleware, представление, сопоставленное с URL, а также причина успешного или неуспешного прохождения проверки прав доступа.

!!! warning
    В рабочей среде используйте `debug=False`. Журналирование уровня DEBUG многословно и создаёт значительную нагрузку на каждый запрос.

Для более лёгкого подхода вызовите `starlette_admin.logging.configure_logging(level=logging.INFO)` самостоятельно вместо передачи `debug=True`. Вы получите обработчик без полной многословности DEBUG.

## Регистрация представлений и монтирование

После создания экземпляра `Admin` зарегистрируйте свои представления и смонтируйте панель администрирования в приложение.

```python
admin.add_view(ModelView(Post))  # Регистрация представления (BaseModelView, CustomView и так далее)
admin.mount_to(app)  # Монтирование панели администрирования в приложение Starlette или FastAPI
```

### Регистрация представлений

Используйте `add_view`, чтобы добавить компоненты на дашборд. Метод принимает либо экземпляр представления, либо класс представления; можно регистрировать представления моделей, пользовательские страницы, выпадающие списки и внешние ссылки.

### Монтирование приложения

После регистрации всех представлений вызовите `mount_to(app)` ровно один раз, чтобы подключить панель администрирования к приложению Starlette или FastAPI. На этом шаге завершается настройка маршрутизации и безопасности.

!!! important "Порядок действий важен"
    Монтирование фиксирует конфигурацию панели, чтобы каждое представление было корректно связано с маршрутом.

    * Обращение к `admin.app` до монтирования вызывает исключение `RuntimeError`.
    * Регистрация ещё одного представления или повторный вызов `mount_to` после первого монтирования также вызывают исключение `RuntimeError`.

```python
admin.app  # Вызывает RuntimeError: панель ещё не смонтирована

admin.mount_to(app)
admin.app  # Возвращает смонтированное вложенное приложение

admin.add_view(ModelView(Comment))  # Вызывает RuntimeError: панель уже смонтирована
```

---

**Что дальше**

* **[Безопасность](security.md):** параметр `secret_key`, CSRF и ограничения экспорта и импорта.
* **[Аутентификация](auth.md):** подключение `auth_provider`.
* **[Несколько экземпляров Admin](../advanced/multiple-admin.md):** запуск нескольких экземпляров `Admin` в одном приложении.
