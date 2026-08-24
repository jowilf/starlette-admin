---
title: Переход с Flask-Admin
description: Прямое руководство по миграции с Flask-Admin на starlette-admin — как
  перенести конфигурации ModelView в экосистему ASGI.
source_hash: ad0da51ce11a7345cd5466d5073fadf2c43c53c310dcd65e4291d9ec6e457447
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/comparison/flask-admin/)
<!-- translation-notice:end -->

# Переход с Flask-Admin

starlette-admin начинался как перенос концепций Flask-Admin в экосистему ASGI, поэтому миграция происходит напрямую. Вы по-прежнему создаёте подкласс `ModelView`, настраиваете его атрибутами класса и регистрируете в экземпляре `Admin`. Большая часть работы сводится к переименованию атрибутов и переходу от неявного контекста запроса Flask к явному объекту `request` в Starlette.

Это руководство сопоставляет API Flask-Admin, атрибут за атрибутом, с его эквивалентом в starlette-admin.

## Общая модель

| Концепция Flask-Admin | Эквивалент в starlette-admin |
| --- | --- |
| `Admin(app, name="...")` | `Admin(engine, title="...")`, затем `admin.mount_to(app)` |
| `ModelView(Model, db.session)` | `ModelView(Model)`; экземпляр `Admin` владеет движком и сессиями базы данных |
| `flask_admin.contrib.sqla` | `starlette_admin.contrib.sqla` |
| `flask_admin.contrib.mongoengine` | `starlette_admin.contrib.mongoengine` |
| бэкенды peewee / pymongo | Beanie, Tortoise ORM, SQLModel или [пользовательский бэкенд](../integrations/custom-backend.md) |
| `BaseView` + `@expose` | [`CustomView`](../user-guide/custom-views.md) |
| `AdminIndexView` | `Admin(index_view=...)`, `DefaultIndexView` |
| Контекст запроса Flask (`flask.request`) | Явный параметр `request: Request` в каждом хуке |
| Синхронные методы | Асинхронные (`async`) методы; синхронные по-прежнему работают там, где допускаются вызываемые объекты |

## Настройка

=== "Flask-Admin"

    ```python
    from flask import Flask
    from flask_admin import Admin
    from flask_admin.contrib.sqla import ModelView

    app = Flask(__name__)
    admin = Admin(app, name="My Admin", template_mode="bootstrap4")
    admin.add_view(ModelView(Post, db.session))
    ```

=== "starlette-admin"

    ```python
    from starlette.applications import Starlette
    from starlette_admin.contrib.sqla import Admin, ModelView

    app = Starlette()  # or FastAPI()
    admin = Admin(engine, title="My Admin", secret_key="change-me")
    admin.add_view(ModelView(Post))
    admin.mount_to(app)
    ```

Переключателя `template_mode` нет. Интерфейс использует [Tabler](https://tabler.io) (Bootstrap 5) и включает тёмную тему. Чтобы изменить внешний вид, напишите пользовательскую [`BaseTheme`](../advanced/custom-themes.md) или [переопределите шаблоны](../advanced/templates.md).

## Атрибуты страницы списка

| Flask-Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `column_list` | `fields` | Также управляет страницами деталей и форм. Используйте атрибуты `exclude_fields_from_*` для вариаций на отдельных страницах. |
| `column_exclude_list` | `exclude_fields_from_list` |  |
| `column_labels` | `label=` | Например, `StringField("title", label="Headline")` |
| `column_descriptions` | `help_text=` | Относится к определению поля. |
| `column_formatters` | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) у поля | Например, `StringField("title", formatter={RequestAction.LIST: lambda request, value: value[:40]})`. |
| `column_formatters_detail` / экспортные форматтеры | Тот же словарь `formatter=`, ключами которого являются значения `RequestAction` | Одно соответствие покрывает форматирование для списка, деталей и экспорта. Действия без записи сохраняют исходное значение. |
| `column_type_formatters` | `formatter=` для каждого поля или пользовательский подкласс поля | Реестра по типам нет. Прикрепите форматтер к каждому полю либо [создайте подкласс поля](../advanced/custom-fields.md) и используйте его повторно. |
| Свойства модели или вызываемые объекты в `column_list` | [`ComputedField`](../user-guide/fields.md#computedfield) или `getter=` у любого поля | Добавляет виртуальные столбцы или переопределяет получение значения существующего поля без создания подкласса. |
| Пользовательские поля WTForms (преобразование значений) | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) у поля | Заменяет стандартный парсинг формы или импорта для поля в зависимости от `RequestAction`. |
| `column_searchable_list` | [`searchable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_filters` | `searchable_fields` в сочетании с `filters=` для каждого поля | Заменяет плоский список фильтров [визуальным конструктором](../user-guide/filters.md), поддерживающим вложенные группы `AND`/`OR`. |
| `column_sortable_list` | [`sortable_fields`](../user-guide/views.md#search-and-sort) |  |
| `column_default_sort` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Например, `[("created_at", True)]` задаёт сортировку по убыванию. |
| `column_editable_list` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Пользователи выбирают ячейку и редактируют её прямо на месте. |
| `page_size` | [`page_size`](../user-guide/views.md#pagination-and-ui-controls) |  |
| `can_set_page_size` | [`page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | По умолчанию `[10, 25, 50, 100]`. Пользователи выбирают из этих вариантов. |
| `column_display_pk` | Включите первичный ключ в `fields` |  |
| `column_details_list` | `fields` минус `exclude_fields_from_detail` | Страница деталей встроена. Опции `can_view_details` не требуется. |

## Атрибуты форм

| Flask-Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `form_columns` | `fields` минус `exclude_fields_from_create` и `exclude_fields_from_edit` |  |
| `form_excluded_columns` | `exclude_fields_from_create`, `exclude_fields_from_edit` | Раздельное управление видимостью для каждой формы. |
| `form_overrides` | Явные экземпляры полей в `fields` | Например, `fields = ["id", TextAreaField("bio")]` |
| `form_args` | Аргументы конструктора поля | Например, `StringField("title", required=True, help_text="...")` |
| `form_choices` | [`EnumField`](../user-guide/fields.md#enumfield) | Например, `EnumField("status", choices=[("draft", "Draft"), ("live", "Live")])` |
| `form_extra_fields` | Дополнительные записи в `fields` | Поддерживает любое поле, не привязанное к столбцу базы данных, например [`ComputedField`](../user-guide/fields.md#computedfield). |
| `form_widget_args` | Атрибуты поля | Задайте `read_only`, `disabled` или `placeholder` непосредственно у поля. |
| `form_rules` | [`form_layout`](../advanced/form-layout.md) | Заменяет плоские правила наборами полей (fieldset), вкладками и адаптивными сетками. |
| `create_modal` / `edit_modal` | Недоступно | Представления создания и редактирования отображаются как полноценные страницы. |
| `on_form_prefill` | Хук `before_edit` |  |

## Экспорт и импорт

=== "Flask-Admin"

    ```python
    class PostView(ModelView):
        can_export = True
        export_types = ["csv", "xlsx"]
        export_max_rows = 10000
    ```

=== "starlette-admin"

    ```python
    class PostView(ModelView):
        exporters = ["csv", "xlsx", "pdf"]
        importers = ["csv", "xlsx"]
        exclude_fields_from_export = ["internal_notes"]
    ```

Экспорт в CSV и JSON включён по умолчанию. Ограничения на количество строк применяются автоматически, а экранирование формул в электронных таблицах — это опция, которую нужно включить у экспортёра. Импорт, которого нет во Flask-Admin, включает шаг предпросмотра с валидацией каждой строки и необязательным обновлением существующих записей по первичному ключу. См. раздел [Экспорт и импорт](../user-guide/export-import.md).

## Действия

=== "Flask-Admin"

    ```python
    from flask_admin.actions import action


    class PostView(ModelView):
        @action("publish", "Publish", "Publish selected posts?")
        def action_publish(self, ids):
            query = Post.query.filter(Post.id.in_(ids))
            for post in query.all():
                post.published = True
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class PostView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Publish",
            confirmation="Publish selected posts?",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            for post in await selection.rows():
                post.published = True
            flash(request, "Posts published")
    ```

Обработчик получает объект [`ActionSelection`](../user-guide/actions.md) вместо «сырых» идентификаторов. Он лениво загружает строки, предоставляет доступ к активным фильтрам и работает одинаково, когда пользователь выбирает все подходящие записи на всех страницах. Действия также могут отображать пользовательскую HTML-форму внутри диалогового окна подтверждения. Для операций над отдельными строками [`@row_action` и `@link_row_action`](../user-guide/actions.md#row-actions) заменяют пользовательские форматтеры столбцов.

## Права доступа и контроль доступа

Флаги класса `can_*` из Flask-Admin превращаются в starlette-admin в [методы, вызываемые для каждого запроса](../user-guide/views.md#security-and-authorization), поэтому решения об авторизации могут зависеть от вошедшего пользователя.

| Flask-Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `is_accessible()` | `is_accessible(request)` | Скрывает представление из меню и блокирует прямой доступ. |
| `inaccessible_callback()` | Обрабатывается механизмом аутентификации | Неаутентифицированные запросы перенаправляются на страницу входа. |
| `can_create = False` | `def can_create(self, request): return False` | `can_edit` и `can_delete` следуют тому же шаблону. |
| `can_view_details` | `can_view_detail(request)` | Страница деталей существует по умолчанию. |
| `can_export` | `can_export(request)`, плюс `can_import(request)` |  |
| Нет эквивалента | `can_access_field(request, field)` | Управляет видимостью на уровне полей для каждого пользователя. |
| Нет эквивалента | `is_action_allowed(request, name)` | Предоставляет авторизацию для каждого действия. |

Во Flask-Admin вы интегрируете Flask-Login самостоятельно. В starlette-admin входит [`AuthProvider`](../user-guide/auth.md) с готовой страницей входа; вам достаточно реализовать методы `login`, `logout` и `authenticate` для вашего хранилища пользователей. `OAuthProvider` покрывает сценарии перенаправления OIDC. Вошедший пользователь доступен везде как `request.state.admin_user`.

## Хуки жизненного цикла модели

| Flask-Admin | starlette-admin |
| --- | --- |
| `on_model_change(form, model, is_created)` | [`before_create(request, data, obj)` / `before_edit(request, data, obj)`](../user-guide/views.md#lifecycle-hooks) |
| `after_model_change` | `after_create` / `after_edit` |
| `on_model_delete` | `before_delete` |
| `after_model_delete` | `after_delete` |
| `get_query` / `get_count_query` | `get_list_query` / `get_count_query`, специфичны для бэкенда SQLAlchemy |
| `handle_view_exception` | Возбудите исключение `FormValidationError` или `ActionFailed` |

Помимо хуков отдельных представлений, [система событий](../advanced/events.md) позволяет одному обработчику наблюдать за всеми представлениями. Во Flask-Admin аналога нет.

```python
from starlette_admin.events import AdminEvent, AfterCreateContext


async def audit(ctx: AfterCreateContext) -> None: ...


admin.events.on(AdminEvent.AFTER_CREATE, audit)
```

## Пользовательские представления и главная страница

| Flask-Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `BaseView` + `@expose("/")` | `CustomView(menu_label=..., path=..., widget=...)` | Собирайте страницы из [виджетов](../user-guide/custom-views.md), не создавая шаблоны вручную. |
| Рендеринг пользовательских шаблонов | Подкласс `CustomView` | Даёт полный контроль над маршрутами и ответами. |
| `AdminIndexView` | `Admin(index_view=...)` | Создавайте дашборды из `StatWidget`, `ChartWidget`, `TableWidget` и виджетов компоновки. |
| `MenuLink` | Представление [`Link`](../user-guide/views.md#link) | Например, `admin.add_link(Link(menu_label="Docs", url="https://..."))` |
| Категории в меню | Представление [`DropDown`](../user-guide/views.md#sidebar-organization) | Группирует представления в боковой панели. |
| `FileAdmin` | Недоступно | Поля файлов и изображений с [локальным хранилищем или S3](../user-guide/file-storage.md) обрабатывают вложения. Браузера файлов сервера нет. |

## Инлайн-модели

=== "Flask-Admin"

    ```python
    class ArticleView(ModelView):
        inline_models = [Comment]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import InlineModelView, ModelView


    class CommentInline(InlineModelView):
        model = Comment
        fields = ["author", "body"]


    class ArticleView(ModelView):
        inlines = [CommentInline]
    ```

Явный класс даёт каждой инлайн-модели полный набор возможностей конфигурации `ModelView`: выбор полей, валидацию и поддержку составных внешних ключей. См. раздел [Инлайн-формы](../user-guide/inline-forms.md).

## Интернационализация

Flask-Admin зависит от Flask-Babel и окружения Flask. starlette-admin использует объект конфигурации:

```python
from starlette_admin import I18nConfig

admin = Admin(engine, i18n_config=I18nConfig(default_locale="fr"))
```

Отображение дат и времени с учётом часового пояса работает так же — через `TimezoneConfig`. См. раздел [Интернационализация и часовые пояса](../user-guide/i18n.md).

## Что вы получаете при переходе

* **Асинхронный стек.** Нативно работает на FastAPI и Starlette с поддержкой асинхронных SQLAlchemy, Beanie и Tortoise ORM. Flask-Admin синхронный.
* **Встроенные средства безопасности.** Защита от CSRF, очистка имён загружаемых файлов, проверка содержимого изображений и ограничения на количество строк при экспорте включаются сразу после создания экземпляра `Admin`; экранирование формул в электронных таблицах можно включить у экспортёров. См. раздел [Безопасность](../user-guide/security.md).
* **Импорт данных.** Шаг предпросмотра проверяет каждую строку до того, как что-либо будет записано. Во Flask-Admin функции импорта нет.
* **Система виджетов дашборда.** Создавайте главные страницы и пользовательские представления на Python вместо ручного написания шаблонов.
* **Современный дизайн.** Активно развиваемая кодовая база с аккуратным интерфейсом, встроенной тёмной темой и полноценными аннотациями типов.

## Что придётся адаптировать

* **Явные объекты запроса.** Окружающего контекста запроса нет. Каждый хук и метод проверки прав получает `request` как параметр.
* **Асинхронные обработчики.** Хуки и действия являются корутинами, поэтому не выполняйте в них блокирующие вызовы либо выносите такую работу в отдельный поток.
* **Нет `FileAdmin`.** Если ваш рабочий процесс зависит от просмотра файловой системы сервера, starlette-admin этого не покрывает.
* **Нет модальных окон создания и редактирования.** Формы отображаются как полноценные страницы, а не всплывающие модальные окна.
