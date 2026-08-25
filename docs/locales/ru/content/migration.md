---
title: Руководство по миграции
description: Инструкция по обновлению со старых версий starlette-admin до последнего
  релиза, включая критические изменения и новые возможности.
source_hash: ab21a9a074813e4119d3ed92fac60944916811ca4846b7fa75f56d3d0a74489b
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/migration/)
<!-- translation-notice:end -->

# Руководство по миграции

На этой странице собраны инструкции по обновлению между релизами `starlette-admin`. Перейдите к разделу, соответствующему версии, с которой вы выполняете обновление.

---

## С 0.17.x до 1.0.0 {#from-017x-to-100}

В этом релизе переработана внутренняя архитектура `starlette-admin` и добавлен большой набор новых возможностей. Хотя высокоуровневый API в целом остался прежним, наиболее значимым изменением стала переработка отрисовки страницы списка: мы отказались от DataTables в пользу таблицы, формируемой на сервере. Большинство остальных изменений сводится к переименованиям или незначительным изменениям сигнатур.

Это руководство охватывает все критические изменения в порядке, в котором вы с наибольшей вероятностью с ними столкнётесь. В каждом разделе старый API сравнивается с его заменой. Если ваша реализация опирается на базовые функции или лёгкие кастомизации (например, экземпляр `Admin`, несколько подклассов `ModelView`, `fields` и `searchable_fields`), миграция, скорее всего, ограничится разделами [Требования](#требования) и [Конструктор Admin](#конструктор-admin), а также несколькими переименованиями.

Кастомизации старой страницы списка требуют наибольшего внимания. Опции DataTables и JavaScript-функции отрисовки не имеют прямых аналогов и должны быть перенесены в серверные шаблоны (см. раздел [Удаление DataTables](#удаление-datatables)).

!!! tip
    Обновите зависимости за один шаг и запустите приложение. Большинство удалённых или переименованных атрибутов вызывают понятные ошибки при запуске, а не молча ломают работу во время выполнения.

### Что нового

Помимо критических изменений, описанных ниже, этот релиз включает:

* **Нативные таблицы списков:** DataTables удалён в пользу встроенной реализации с отрисовкой на сервере. Состояние таблицы теперь полностью определяется URL, то есть все настройки страницы, фильтров и сортировки можно сразу передавать по ссылке и сохранять в закладки.
* **[Фильтры](user-guide/filters.md):** вложенный конструктор фильтров `AND`/`OR` заменяет SearchBuilder из DataTables. Фильтры выводятся из типов полей и полностью расширяемы на чистом Python. Вы можете написать класс фильтра без какого-либо JavaScript.
* **[Импорт и экспорт на стороне сервера](user-guide/export-import.md):** импорт данных из CSV, JSON, Excel и других форматов с отчётом об ошибках по каждой строке, а также серверные экспортёры (CSV, JSON, Excel, PDF и т. д.), заменяющие клиентские кнопки DataTables.
* **[События](advanced/events.md):** подписка на хуки жизненного цикла, такие как `before_create`, `after_edit_committed`, `after_login`, и на различные события действий.
* **[Темы](advanced/custom-themes.md) и [плагины](advanced/plugins.md):** упаковка и повторное использование пользовательского оформления и поведения. Доступны шаблоны Cookiecutter, чтобы быстро начать работу.
* **[Виджеты и дашборды](user-guide/custom-views.md):** создание индексных страниц и пользовательских представлений с помощью `StatWidget`, `ChartWidget`, `TableWidget` и других.
* **[Компоновка форм](advanced/form-layout.md):** логичное расположение форм создания/редактирования с помощью строк, колонок, fieldset'ов и вкладок.
* **[Инлайн-редактирование](user-guide/inline-edit.md):** редактирование отдельного поля прямо со страницы списка.
* **[Инлайн-формы](user-guide/inline-forms.md):** редактирование связанных моделей внутри родительской формы с помощью `InlineModelView`.
* **Прочие улучшения:** [flash-сообщения](user-guide/flash-messages.md), [вход через OAuth](user-guide/auth.md), [backend для Tortoise ORM](integrations/tortoise.md), новые поля (`ComputedField`, `SlugField`, `UUIDField`, `IPAddressField`), валидаторы на уровне полей и копирование в буфер обмена для любого поля.
* **[Логирование](user-guide/admin.md#debugging):** пакет теперь ведёт внутренние логи в пространстве имён `starlette_admin`, по умолчанию отключённые. Передайте `Admin(debug=True)` или вызовите `starlette_admin.logging.configure_logging()`, чтобы видеть маршрутизацию запросов, работу middleware и решения о правах доступа в консоли — это особенно удобно при миграции.
* **Расширенное тестовое покрытие:** набор тестов существенно вырос, включая end-to-end тесты на Playwright, проверяющие ключевые сценарии работы административного интерфейса.
* **Более лёгкий пакет:** размер публикуемого пакета на PyPI сокращён примерно на 50%.

### Требования {#требования}

* **Поддержка Python:** требуется Python 3.11 или новее. Поддержка Python 3.9 и 3.10 прекращена.
* **Основные зависимости:** `itsdangerous` теперь является основной зависимостью, используемой для подписи cookie административной панели (CSRF-токены и flash-сообщения).
* **Новые необязательные extras:**

    | Extra | Что включает |
    | --- | --- |
    | `starlette-admin[email]` | серверная валидация `EmailField` через `email-validator` |
    | `starlette-admin[pdf]` | экспорт PDF через `reportlab` |
    | `starlette-admin[s3]` | файловое хранилище S3 через `aiobotocore` |
    | `starlette-admin[tinymce]` | санитизация HTML в `TinyMCEEditorField` через `nh3` |
    | `starlette-admin[i18n]` | переводы через `babel` (без изменений) |

* **Backend Beanie:** требуется Beanie 2.0+.
* **Backend Odmantic:** удалён. Если вы от него зависите, оставайтесь на `starlette-admin<=0.17.1` и выразите заинтересованность, [создав issue](https://github.com/jowilf/starlette-admin/issues); поддержка может быть возвращена при достаточном спросе.

### Конструктор Admin {#конструктор-admin}

```python
# Before
admin = Admin(engine, statics_dir="statics")

# After
admin = Admin(engine, static_dir="statics", secret_key=os.environ["ADMIN_SECRET_KEY"])
```

* Параметр `statics_dir` переименован в `static_dir`.
* **Задайте `secret_key`.** Этот ключ подписывает cookie CSRF и flash-сообщений. Если он не указан, при запуске генерируется случайный ключ (что допустимо для разработки). Однако подписанные значения будут инвалидироваться при каждом перезапуске и между несколькими воркерами. В продакшене всегда передавайте стабильный секретный ключ.
* `logo_url`, `login_logo_url` и `favicon_url` теперь принимают callable вида `(request) -> str | None`. Это заменяет брендирование per-request, которое ранее предоставлялось через `AdminConfig`.
* **Новые необязательные параметры:** `theme`, `plugins`, `additional_loaders`, `import_config` и `export_config`.
* **Особенности SQLAlchemy:** первый аргумент теперь называется `session_provider`. Он принимает `Engine` или `AsyncEngine`, а также `sessionmaker` или `async_sessionmaker`. Существующие вызовы вида `Admin(engine)` продолжат работать.
* `timezone_config` по умолчанию равен `TimezoneConfig()` вместо `None`. Значения datetime теперь по умолчанию отображаются в локальном часовом поясе пользователя. Передайте `timezone_config=None`, чтобы сохранить исходные значения.

### Переименованные идентификаторы представлений

Соглашение об именовании представлений унифицировано. Обновите конструкторы `ModelView` и атрибуты классов соответствующим образом:

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

### Удаление DataTables {#удаление-datatables}

Страница списка больше не использует DataTables. Атрибуты, которые ранее его настраивали, полностью удалены:

| Удалено | Замена |
| --- | --- |
| `datatables_options` | Нет. Таблица формируется на сервере. Настраивайте через шаблоны. |
| `search_builder` | Новый [конструктор фильтров](user-guide/filters.md), включаемый через `searchable_fields`. |
| `responsive_table` | Нет. Таблица нативно обрабатывает переполнение. |
| `save_state` | Всегда включено. Состояние списка (страница, сортировка, фильтры, поиск, видимые колонки) теперь хранится в URL. |
| `BaseField.search_builder_type` | `BaseField.filters` (список классов фильтров). |
| `BaseField.render_function_key` | `BaseField.list_template` (серверный шаблон Jinja). |

Если вы ранее писали собственные JavaScript-функции отрисовки или плагины DataTables, перенесите их в переопределения `list_template`. Теперь каждая ячейка списка рендерится напрямую из шаблона `templates/fields/list/*.html`.

### Действия

Обработчики batch-действий теперь получают объект `ActionSelection` вместо списка первичных ключей. Это поддерживает новый баннер «выбрать все подходящие», позволяющий применить действие ко всем строкам, соответствующим текущему фильтру, без их материализации на клиенте.

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
* Свойства вроде `selection.is_select_all`, `selection.filters` и `selection.q` позволяют выполнить операцию одним bulk-запросом.
* Возврат строки с сообщением об успехе заменён [flash-сообщениями](user-guide/flash-messages.md).
* Обработчики row action сохраняют исходную сигнатуру `(request, pk)`.
* **Новые опции `@action`:** `header`, `allow_empty_selection`, `dedicated_button`, `modal_size` и callable-параметр `form` для каждого запроса.

### Аутентификация {#аутентификация}

Модуль `starlette_admin/auth.py` теперь является пакетом `starlette_admin.auth`. Существующие импорты из `starlette_admin.auth` продолжат работать, однако контракт провайдера изменился.

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
* `AdminConfig` удалён. Управляйте заголовками и логотипами для каждого запроса через callable-формы параметров `logo_url` и `login_logo_url` экземпляра `Admin`.
* Встроенный [`OAuthProvider`](user-guide/auth.md#oauthprovider-oauth2oidc-redirect-flow) поддерживает сценарии входа OAuth2/OIDC «из коробки».
* Декоратор `login_not_required` остался без изменений.

### Экспорт и импорт

Экспорт переехал с клиентских кнопок DataTables на серверные streaming-endpoint'ы. Функциональность импорта совершенно новая, а `ExportType` больше не существует.

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

* `export_types` заменён на `exporters`. Он принимает список названий форматов или экземпляров `BaseExporter`. Из встроенных поддерживаются `csv`, `json`, `tsv`, `xlsx`, `ods`, `html`, `yaml` и `pdf`. Для форматов, отличных от `csv` или `json`, требуется `tablib`, а для PDF — extra `pdf`.
* `importers` принимает список названий форматов или экземпляров `BaseImporter`. Из встроенных поддерживаются `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` и `html`. Для форматов, отличных от `csv`, `tsv` или `json`, требуется `tablib`.
* `export_fields` (список включения) заменён на `exclude_fields_from_export` (список исключения). Это соответствует соглашению об именовании остальных атрибутов `exclude_fields_from_*`.
* Отдельные поля также принимают параметры `exclude_from_export` и `exclude_from_import`.
* Настройте глобальные лимиты с помощью `ExportConfig` и `ImportConfig` на экземпляре `Admin`. Подробности см. в документации [Export & Import](user-guide/export-import.md).

### Пользовательские поля и переопределение шаблонов

Шаблоны полей реорганизованы. Обновите пути, если вы переопределяете встроенные шаблоны или поставляете собственные поля:

| Было | Стало |
| --- | --- |
| `templates/displays/*.html` | `templates/fields/detail/*.html` |
| `templates/forms/*.html` | `templates/fields/form/*.html` |
| (клиентская функция отрисовки) | `templates/fields/list/*.html` |
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

Среди новых возможностей на уровне полей стоит изучить `validators`, `filters`, `default`, хуки (`getter`, `formatter`, `parser`), `copy_to_clipboard` и словарь `extra` для произвольных метаданных. Подробнее см. документацию [Custom Fields](advanced/custom-fields.md).

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

Декоратор `@route` также позволяет любому представлению предоставлять дополнительные endpoint'ы для таких задач, как JSON-данные для графиков или webhooks.

### Пользовательские backend'ы

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

* Строковый параметр `where` разделён на `q` (термины полнотекстового поиска) и `filters` (типизированное дерево `FilterGroup`, формируемое конструктором фильтров).
* Параметр `order_by` (ранее список строк вида `"field direction"`) заменён на `sorts`, который принимает список кортежей `(field_name, direction)`.
* Каждый backend теперь поставляется с реестром фильтров, сопоставляющим типы полей реализациям фильтров. Полный контракт и рабочий пример см. в документации [Custom Backend](integrations/custom-backend.md).

### Изменения поведения, которые стоит проверить

* **Часовые пояса:** значения datetime по умолчанию отображаются в локальном часовом поясе пользователя (см. примечание о `timezone_config` в разделе «Конструктор Admin»).
* **Состояние в URL:** состояние списка теперь хранится в URL. Сохранённые в закладки URL админки из предыдущих версий будут открываться с состоянием списка по умолчанию, поскольку сохранённые состояния DataTables не переносятся.
* **Валидация email:** `EmailField` теперь валидируется на сервере, если установлен `email-validator`.
* **Защита CSRF:** защита CSRF встроена и основана на cookie. Если вы ранее оборачивали админку собственным CSRF-middleware, его можно безопасно удалить. Убедитесь, что задан `secret_key`, чтобы токены переживали перезапуск сервера.
* **Размер загрузки FileField:** `FileField.max_size` теперь по умолчанию равен 50 МБ вместо неограниченного размера. Передайте `max_size=None`, чтобы вернуть прежнее поведение без ограничений, или задайте явное значение, чтобы изменить лимит.

### Удалено без замены

* `AdminConfig` (см. раздел [Аутентификация](#аутентификация)).
* `datatables_options`, `responsive_table` и `save_state` (см. раздел [Удаление DataTables](#удаление-datatables)).
* Backend Odmantic (см. раздел [Требования](#требования)).

## Как получить помощь

Если вы столкнулись с проблемой миграции, не описанной в этом руководстве, пожалуйста, [создайте issue](https://github.com/jowilf/starlette-admin/issues). Приложите минимальный пример воспроизведения проблемы и укажите версию, с которой выполняется обновление. Запуск с [`Admin(debug=True)`](user-guide/admin.md#debugging) часто сразу выявляет причину, а полученные логи станут отличным дополнением к вашему отчёту.
