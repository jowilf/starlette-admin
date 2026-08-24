---
title: Руководство по миграции
description: Инструкция по обновлению со старых версий starlette-admin до последнего
  релиза, включая критические изменения и новые возможности.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Руководство по миграции

На этой странице собраны инструкции по обновлению между релизами `starlette-admin`. Перейдите к разделу, соответствующему версии, с которой вы обновляетесь.

---

## С 0.17.x до 1.0.0

В этом релизе переработана внутренняя архитектура `starlette-admin` и добавлен большой набор новых возможностей. Хотя высокоуровневый API в целом остался прежним, самое значительное изменение — это переписанный рендеринг страницы списка. Мы отказались от DataTables в пользу таблицы, отрисовываемой на сервере. Большинство остальных изменений сводится к переименованиям или небольшим изменениям сигнатур.

Это руководство описывает все критические изменения в порядке, в котором вы, скорее всего, с ними столкнётесь. В каждом разделе старый API сравнивается с его заменой. Если ваша реализация опирается на базовые функции или лёгкие настройки (например, экземпляр `Admin`, несколько подклассов `ModelView`, `fields` и `searchable_fields`), миграция, скорее всего, ограничится разделами [Требования](#requirements) и [Конструктор Admin](#the-admin-constructor), а также несколькими переименованиями.

Больше всего внимания потребуют настройки старой страницы списка. Опции DataTables и JavaScript-функции рендеринга не имеют прямых аналогов, и их нужно перенести на серверные шаблоны (см. раздел [Удаление DataTables](#datatables-removal)).

!!! tip
    Обновите зависимости за один шаг и запустите приложение. Большинство удалённых или переименованных атрибутов вызывают понятные ошибки при запуске, а не молча ломают работу во время выполнения.

### Что нового

Помимо критических изменений, описанных ниже, этот релиз включает:

* **Нативные таблицы списка:** DataTables удалён в пользу встроенной реализации с серверным рендерингом. Состояние таблицы теперь полностью определяется URL: конфигурациями страницы, фильтров и сортировки можно сразу делиться и сохранять в закладки.
* **[Фильтры](user-guide/filters.md):** вложенный конструктор фильтров `AND`/`OR` заменяет SearchBuilder из DataTables. Фильтры выводятся из типов полей и полностью расширяемы на чистом Python. Вы можете написать класс фильтра без какого-либо JavaScript.
* **[Импорт и экспорт на стороне сервера](user-guide/export-import.md):** импорт данных из CSV, JSON, Excel и других форматов с отчётом об ошибках по каждой строке, а также серверные экспортёры (CSV, JSON, Excel, PDF и т. д.), которые заменяют клиентские кнопки DataTables.
* **[События](advanced/events.md):** подписка на хуки жизненного цикла, такие как `before_create`, `after_edit_committed`, `after_login` и различные события действий.
* **[Темы](advanced/custom-themes.md) и [плагины](advanced/plugins.md):** упаковывайте и повторно используйте собственное оформление и поведение. Доступны шаблоны Cookiecutter, чтобы быстро начать работу.
* **[Виджеты и дашборды](user-guide/custom-views.md):** создавайте индексные страницы и пользовательские представления с помощью `StatWidget`, `ChartWidget`, `TableWidget` и других.
* **[Компоновка формы](advanced/form-layout.md):** логично располагайте формы создания/редактирования с помощью строк, колонок, fieldset'ов и вкладок.
* **[Инлайн-редактирование](user-guide/inline-edit.md):** редактируйте отдельное поле прямо на странице списка.
* **[Инлайн-формы](user-guide/inline-forms.md):** редактируйте связанные модели внутри родительской формы с помощью `InlineModelView`.
* **Другие улучшения:** [флеш-сообщения](user-guide/flash-messages.md), [вход через OAuth](user-guide/auth.md), [бэкенд Tortoise ORM](integrations/tortoise.md), новые поля (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), валидаторы на уровне полей (`validators`) и копирование в буфер обмена для любого поля.
* **[Логирование](user-guide/admin.md#debugging):** пакет теперь пишет внутренние логи в пространстве имён `starlette_admin`, по умолчанию отключённые. Передайте `Admin(debug=True)` или вызовите `starlette_admin.logging.configure_logging()`, чтобы видеть маршрутизацию запросов, middleware и решения о правах доступа в консоли — это особенно удобно при миграции.
* **Расширенное тестовое покрытие:** набор тестов стал значительно больше, включая сквозные тесты на Playwright, проверяющие ключевые сценарии работы интерфейса администрирования.
* **Меньший размер пакета:** размер публикуемого пакета на PyPI уменьшен примерно на 50 %.

### Требования {#requirements}

* **Поддержка Python:** требуется Python 3.11 или новее. Поддержка Python 3.9 и 3.10 прекращена.
* **Основные зависимости:** `itsdangerous` теперь является основной зависимостью и используется для подписи cookie панели администрирования (CSRF-токены и флеш-сообщения).
* **Новые необязательные extras:**

    | Extra | Что включает |
    | --- | --- |
    | `starlette-admin[email]` | серверная валидация `EmailField` через `email-validator` |
    | `starlette-admin[pdf]` | экспорт в PDF через `reportlab` |
    | `starlette-admin[s3]` | файловое хранилище S3 через `aiobotocore` |
    | `starlette-admin[tinymce]` | санитизация HTML для `TinyMCEEditorField` через `nh3` |
    | `starlette-admin[i18n]` | переводы через `babel` (без изменений) |

* **Бэкенд Beanie:** требуется Beanie 2.0+.
* **Бэкенд Odmantic:** удалён. Если вы от него зависите, оставайтесь на `starlette-admin<=0.17.1` и выразите заинтересованность, [создав issue](https://github.com/jowilf/starlette-admin/issues); поддержку можно вернуть при достаточном спросе.

### Конструктор Admin {#the-admin-constructor}

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* `statics_dir` переименован в `static_dir`.
* **Задайте `secret_key`.** Этот ключ подписывает cookie CSRF и флеш-сообщений. Если его не указать, при запуске генерируется случайный ключ (для разработки это допустимо). Однако подписанные значения будут недействительны после каждого перезапуска и между несколькими воркерами. В продакшене всегда передавайте стабильный секрет.
* `logo_url`, `login_logo_url` и `favicon_url` теперь принимают вызываемый объект `(request) -> str | None`. Это заменяет брендинг по каждому запросу, который раньше предоставлялся через `AdminConfig`.
* **Новые необязательные параметры:** `theme`, `plugins`, `additional_loaders`, `import_config` и `export_config`.
* **Особенности SQLAlchemy:** первый аргумент теперь называется `session_provider`. Он принимает `Engine` или `AsyncEngine`, а теперь также `sessionmaker` или `async_sessionmaker`. Существующие вызовы вида `Admin(engine)` продолжат работать.
* `timezone_config` по умолчанию равен `TimezoneConfig()` вместо `None`. Значения datetime теперь по умолчанию отображаются в локальном часовом поясе просматривающего. Передайте `timezone_config=None`, чтобы сохранить исходные значения.

### Переименованные идентификаторы представлений

Соглашение об именах представлений унифицировано. Обновите конструкторы `ModelView` и атрибуты классов:

| Было | Стало |
| --- | --- |
| `identity` | `key` |
| `name` | `display_name` |
| `label` | `menu_label` |
| `form_include_pk` | `show_pk_in_forms` |

```python
# Before
admin.add_view(PostView(Post, identity="post", name="Post", label="Posts"))

# After
admin.add_view(PostView(Post, key="post", display_name="Post", menu_label="Posts"))
```

Обратите внимание, что `Link` и `DropDown` также используют `menu_label` вместо `label`.

### Удаление DataTables {#datatables-removal}

Страница списка больше не использует DataTables. Атрибуты, которые ранее его настраивали, полностью удалены:

| Удалено | Замена |
| --- | --- |
| `datatables_options` | Нет. Таблица отрисовывается на сервере. Настраивайте через шаблоны. |
| `search_builder` | Новый [конструктор фильтров](user-guide/filters.md), включаемый через `searchable_fields`. |
| `responsive_table` | Нет. Таблица сама обрабатывает переполнение. |
| `save_state` | Всегда включено. Состояние списка (страница, сортировка, фильтры, поиск, видимые колонки) теперь хранится в URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (список классов фильтров). |
| `BaseField.render_function_key` | `BaseField.list_template` (серверный шаблон Jinja). |

Если вы ранее писали собственные JavaScript-функции рендеринга или плагины DataTables, перенесите их в переопределения `list_template`. Теперь каждая ячейка списка поля отрисовывается напрямую из шаблона `templates/fields/list/*.html`.

### Действия

Обработчики групповых действий теперь получают объект `ActionSelection` вместо списка первичных ключей. Это поддерживает новый баннер «выбрать всё подходящее», который охватывает каждую строку, соответствующую текущему фильтру, без материализации их на клиенте.

```python
# Before
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, pks: List[Any]) -> str:
    for article in await self.find_by_pks(request, pks):
        ...
    return f"{len(pks)} articles were published"


# After
@action(name="publish", text="Publish")
async def publish_action(self, request: Request, selection: ActionSelection) -> None:
    for article in await selection.rows():
        ...
    flash(request, f"{await selection.count()} articles were published")
```

* Методы вроде `selection.rows()`, `selection.pks()` и `selection.count()` разрешают целевые строки лениво. Это работает как при индивидуальной отметке строк пользователем, так и при выборе всех подходящих строк.
* Свойства вроде `selection.is_select_all`, `selection.filters` и `selection.q` позволяют выполнить операцию одним массовым запросом.
* Возврат строки с сообщением об успехе заменён [флеш-сообщениями](user-guide/flash-messages.md).
* Обработчики действий над строкой сохраняют исходную сигнатуру `(request, pk)`.
* **Новые опции `@action`:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` и вызываемые объекты `form` для каждого запроса.

### Аутентификация {#authentication}

Модуль `starlette_admin/auth.py` теперь является пакетом `starlette_admin.auth`. Существующие импорты из `starlette_admin.auth` продолжат работать, но контракт провайдера изменился.

```python
# Before
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request, response):
        request.session.update({"username": username})
        return response

    async def logout(self, request, response):
        request.session.clear()
        return response

    async def is_authenticated(self, request) -> bool:
        request.state.user = my_users_db.get(request.session.get("username"))
        return request.state.user is not None

    def get_admin_user(self, request) -> AdminUser:
        return AdminUser(username=request.state.user["name"])

    def get_admin_config(self, request) -> AdminConfig:
        return AdminConfig(app_title="My Admin")


# After
class MyAuthProvider(AuthProvider):
    async def login(self, username, password, remember_me, request):
        if username in my_users_db:
            request.session.update({"username": username})
            return None  # default redirect (`next` param or admin index)
        raise LoginFailed("Invalid username or password")

    async def logout(self, request):
        request.session.clear()

    async def authenticate(self, request) -> AdminUser | None:
        user = my_users_db.get(request.session.get("username"))
        return AdminUser(username=user["name"]) if user else None
```

* Методы `is_authenticated`, `get_admin_user` и `get_admin_config` объединены в один метод `authenticate(request) -> AdminUser | None`. Возврат `None` означает неаутентифицированное состояние.
* Методы `login` и `logout` больше не получают и не возвращают подготовленный `response`. Верните `None` для стандартного редиректа или верните собственный `Response`, чтобы переопределить это поведение.
* `AdminConfig` удалён. Заголовки и логотипы для каждого запроса обрабатывайте с помощью вызываемой формы `logo_url` и `login_logo_url` на экземпляре `Admin`.
* Встроенный [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) поддерживает сценарии входа OAuth2/OIDC «из коробки».
* Декоратор `login_not_required` остался без изменений.

### Экспорт и импорт

Экспорт переехал с клиентских кнопок DataTables на серверные стриминговые эндпоинты. Функциональность импорта совершенно новая, а `ExportType` больше не существует.

```python
# Before
from starlette_admin import ExportType


class PostView(ModelView):
    export_types = [ExportType.CSV, ExportType.EXCEL]
    export_fields = ["id", "title"]


# After
class PostView(ModelView):
    exporters = ["csv", "xlsx"]
    importers = ["csv", "json"]
    exclude_fields_from_export = ["content"]
    exclude_fields_from_import = ["id"]
```

* `export_types` теперь называется `exporters`. Он принимает список названий форматов или экземпляров `BaseExporter`. Поддерживаемые встроенные форматы: `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` и `pdf`. Для форматов, отличных от `csv` или `json`, требуется `tablib`, а для PDF — extra `pdf`.
* `importers` принимает список названий форматов или экземпляров `BaseImporter`. Поддерживаемые встроенные форматы: `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` и `html`. Для форматов, отличных от `csv`, `tsv` или `json`, требуется `tablib`.
* `export_fields` (список включения) заменён на `exclude_fields_from_export` (список исключения). Это соответствует соглашению об именах остальных атрибутов `exclude_fields_from_*`.
* Поля также могут по отдельности принимать `exclude_from_export` и `exclude_from_import`.
* Глобальные ограничения настраивайте с помощью `ExportConfig` и `ImportConfig` на экземпляре `Admin`. Подробнее см. документацию [Экспорт и импорт](user-guide/export-import.md).

### Пользовательские поля и переопределение шаблонов

Шаблоны полей реорганизованы. Обновите пути, если вы переопределяете встроенные шаблоны или поставляете пользовательские поля:

| Было | Стало |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (клиентская функция рендеринга) | `templates/fields/list/*.html` |
| `BaseField.display_template` | `BaseField.detail_template` |
| `BaseField.form_template` (путь) | То же имя атрибута, новый префикс пути `fields/form/` |

```python
# Before
@dataclass
class RatingField(BaseField):
    display_template: str = "displays/rating.html"
    form_template: str = "forms/rating.html"
    render_function_key: str = "rating"


# After
@dataclass
class RatingField(BaseField):
    detail_template: str = "fields/detail/rating.html"
    form_template: str = "fields/form/rating.html"
    list_template: str = "fields/list/rating.html"
```

Среди новых возможностей на уровне полей стоит изучить `validators`, `filters`, `default`, хуки (`getter`, `formatter`, `parser`), `copy_to_clipboard` и словарь `extra` для произвольных метаданных. Подробнее см. документацию [Пользовательские поля](advanced/custom-fields.md).

### CustomView

Класс `CustomView` больше не принимает `template_path` и `methods`. Простые страницы создавайте с помощью [виджетов](user-guide/custom-views.md). Для страниц, требующих полного контроля, создайте подкласс `CustomView` и объявите маршруты напрямую.

```python
# Before
admin.add_view(CustomView(label="Home", path="/home", template_path="home.html"))

# After: widget-based page
admin.add_view(
    CustomView(
        menu_label="System Status",
        path="/status",
        widget=StatWidget(title="Pending jobs", value_callback=count_pending_jobs),
    )
)


# After: full control
class HomeView(CustomView):
    menu_label = "Home"
    path = "/home"

    @route("")
    async def index(self, request: Request) -> Response:
        return self.templates.TemplateResponse(request=request, name="home.html")
```

Декоратор `@route` также позволяет любому представлению предоставлять дополнительные эндпоинты для таких задач, как JSON-данные для графиков или вебхуки.

### Пользовательские бэкенды

Если вы реализовали `BaseModelView` поверх собственного источника данных, обратите внимание на обновлённый контракт доступа к данным:

```python
# Before
async def find_all(self, request, skip=0, limit=100, where=None, order_by=None): ...
async def count(self, request, where=None): ...


# After
async def find_all(
    self, request, skip=0, limit=100, q=None, sorts=None, filters=None
): ...
async def count(self, request, q=None, filters=None): ...
```

* Строковый параметр `where` разделён на `q` (термины полнотекстового поиска) и `filters` (типизированное дерево `FilterGroup`, предоставляемое конструктором фильтров).
* Параметр `order_by` (ранее список строк вида `"field direction"`) теперь называется `sorts` и принимает список кортежей `(field_name, direction)`.
* Каждый бэкенд теперь поставляется с реестром фильтров, сопоставляющим типы полей с реализациями фильтров. Полный контракт и рабочий пример см. в документации [Пользовательский бэкенд](integrations/custom-backend.md).

### Изменения поведения, которые стоит проверить

* **Часовые пояса:** значения datetime по умолчанию отображаются в локальном часовом поясе просматривающего (см. примечание о `timezone_config` в разделе «Конструктор Admin»).
* **Состояние в URL:** состояние списка теперь хранится в URL. Сохранённые в закладки URL панели администрирования из предыдущих версий приведут к состоянию списка по умолчанию, поскольку сохранённые состояния DataTables не переносятся.
* **Валидация email:** `EmailField` теперь выполняет валидацию на сервере, если установлен `email-validator`.
* **Защита CSRF:** защита CSRF встроена и основана на cookie. Если вы ранее оборачивали панель администрирования собственным CSRF-middleware, его можно безопасно удалить. Убедитесь, что задан `secret_key`, чтобы токены переживали перезапуск сервера.
* **Размер загрузки FileField:** `FileField.max_size` теперь по умолчанию равен 50 МБ вместо неограниченного размера. Передайте `max_size=None`, чтобы вернуть прежнее поведение без ограничений, или задайте явное значение, чтобы изменить лимит.

### Удалено без замены

* `AdminConfig` (см. раздел [Аутентификация](#authentication)).
* `datatables_options`, `responsive_table` и `save_state` (см. раздел [Удаление DataTables](#datatables-removal)).
* Бэкенд Odmantic (см. раздел [Требования](#requirements)).

## Как получить помощь

Если вы столкнулись с проблемой миграции, не описанной в этом руководстве, пожалуйста, [создайте issue](https://github.com/jowilf/starlette-admin/issues). Приложите минимальный пример, воспроизводящий проблему, и укажите версию, с которой вы обновляетесь. Запуск с [`Admin(debug=True)`](user-guide/admin.md#debugging) часто сразу выявляет причину, а полученные логи станут отличным дополнением к вашему отчёту.
