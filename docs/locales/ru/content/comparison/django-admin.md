---
title: Переход с Django Admin
description: Подробное руководство по миграции, сопоставляющее концепции Django Admin
  с эквивалентами starlette-admin для создания декларативных интерфейсов администрирования.
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# Переход с Django Admin

Если вы знакомы с Django Admin, starlette-admin покажется вам привычным. Оба инструмента генерируют интерфейс администрирования на основе декларативной конфигурации для каждой модели, и оба поддерживают инлайн-редактирование, групповые действия и права доступа для каждого запроса.

Различия носят структурный характер. starlette-admin работает поверх любого ASGI-приложения, не требуя Django, поддерживает несколько ORM и позволяет подключить собственную аутентификацию вместо навязывания встроенной модели пользователя.

Это руководство сопоставляет каждую ключевую концепцию `ModelAdmin` с её эквивалентом в starlette-admin, приводя код рядом для сравнения.

## Базовая модель

| Концепция Django Admin | Эквивалент в starlette-admin |
| --- | --- |
| `AdminSite` | экземпляр [`Admin`](../api/admin.md), смонтированный в вашем приложении |
| `ModelAdmin` | подкласс [`ModelView`](../user-guide/views.md) |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` в `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie или Tortoise ORM через `starlette_admin.contrib.*` |
| `__str__` у модели | `__admin_repr__(self, request)`, который асинхронный и учитывает запрос |
| Поля формы, выводимые из полей модели | [поля](../user-guide/fields.md), выводимые конвертером бэкенда; настраиваются для каждого поля |

## Регистрация модели

=== "Django Admin"

    ```python
    from django.contrib import admin
    from .models import Post


    @admin.register(Post)
    class PostAdmin(admin.ModelAdmin):
        list_display = ["title", "published", "created_at"]
        search_fields = ["title", "content"]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin.contrib.sqla import Admin, ModelView


    class PostView(ModelView):
        fields = ["id", "title", "content", "published", "created_at"]
        exclude_fields_from_list = ["content"]
        searchable_fields = ["title", "content"]


    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)  # app is your FastAPI or Starlette instance
    ```

Здесь выделяются два структурных отличия:

1. **Один список полей управляет всеми страницами.** `fields` — единственный источник истины. Затем вы используете [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create` и `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization) для вариаций на отдельных страницах.
2. **Экземпляр `Admin` владеет движком базы данных.** Сессию не нужно передавать в каждое представление.

## Настройки страницы списка

| Django Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `list_display` | `fields` минус [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | Один список полей управляет всеми страницами. |
| `list_display` с вызываемым объектом или `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield) либо `getter=` у любого поля | Например, `ComputedField("full_name", getter=lambda request, obj: ...)`. Используйте `getter=` у типизированного поля, например даты или изображения, чтобы сохранить его формат отображения. |
| Переформатирование реального столбца для отображения | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) у поля | Это `dict[RequestAction, callable]`, поэтому список, страница деталей и экспорт могут форматировать значения по-разному. В Django требуется вызываемый объект плюс `admin_order_field`, чтобы сохранить сортировку; здесь столбец остаётся сортируемым. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | Используется как для полнотекстового поиска, так и для конструктора фильтров. |
| `list_filter` | `searchable_fields` в сочетании с `filters=` для каждого поля | Пользователи получают визуальный конструктор с вложенными группами `AND`/`OR` вместо фиксированной боковой панели. См. [Фильтры](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Например, `fields_default_sort = [("created_at", True)]` задаёт сортировку по убыванию. |
| `admin_order_field` / возможность сортировки | [`sortable_fields`](../user-guide/views.md#search-and-sort) | По умолчанию любое поле можно сортировать. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Пользователи выбирают ячейку и редактируют её прямо на месте. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Управляет ограничениями пагинации. |
| `date_hierarchy` | Фильтры по датам, такие как `between` и `in the past` | Отдельной панели детализации нет; эту задачу решает конструктор фильтров. |
| `empty_value_display` | Запись в `formatter=` либо `null_template` | Форматтеры получают значения `None`, поэтому могут подставить заполнитель. `null_template` заменяет саму разметку. |

## Формы

| Django Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Управляет видимостью полей формы. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Свободная компоновка с помощью `FieldsetWidget`, `TabsWidget`, `GridWidget` и `RowWidget`. |
| `readonly_fields` | `read_only=True` у поля | Поле также можно исключить из представлений создания и редактирования. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | То же поведение живой генерации слага. |
| `autocomplete_fields`, `raw_id_fields` | Поведение [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) по умолчанию | Виджеты связей — это Select2-поля с серверным поиском «из коробки». |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Отображается как компонент множественного выбора с поиском. |
| `formfield_overrides` | Явные записи в списке `fields` | Замените автоматически определённое поле напрямую: `fields = ["id", TextAreaField("bio")]` |
| Собственная валидация формы | `validators=` у поля либо `FormValidationError` в хуках | См. [Валидаторы](../api/validators.md). |
| `to_python()` у поля формы / собственное приведение типов | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) у поля | Заменяет стандартный парсинг формы или импорта для конкретного `RequestAction`. |
| Текст подсказки у поля формы модели | `help_text=` | Доступно в любом определении поля. |

### Пример fieldsets

=== "Django Admin"

    ```python
    class PostAdmin(admin.ModelAdmin):
        fieldsets = [
            ("Content", {"fields": ["title", "body"]}),
            ("Publication", {"fields": ["published", "created_at"]}),
        ]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import FieldsetWidget


    class PostView(ModelView):
        fields = ["id", "title", "body", "published", "created_at"]
        form_layout = [
            FieldsetWidget(legend="Content", children=["title", "body"]),
            FieldsetWidget(legend="Publication", children=["published", "created_at"]),
        ]
    ```

`form_layout` даёт больше возможностей, чем fieldsets: можно строить вкладки, адаптивные сетки и вложенные компоновки. См. [Компоновка формы](../advanced/form-layout.md).

## Инлайны

=== "Django Admin"

    ```python
    class CommentInline(admin.TabularInline):
        model = Comment
        extra = 1


    class ArticleAdmin(admin.ModelAdmin):
        inlines = [CommentInline]
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

starlette-admin определяет внешний ключ, когда он однозначен, и поддерживает составные внешние ключи. Расширенные настройки описаны в разделе [Инлайн-формы](../user-guide/inline-forms.md).

## Действия

=== "Django Admin"

    ```python
    @admin.action(description="Mark selected articles as published")
    def make_published(modeladmin, request, queryset):
        queryset.update(published=True)


    class ArticleAdmin(admin.ModelAdmin):
        actions = [make_published]
    ```

=== "starlette-admin"

    ```python
    from starlette_admin import ActionSelection, action, flash


    class ArticleView(ModelView):
        actions = ["make_published", "delete"]

        @action(
            name="make_published",
            text="Mark selected articles as published",
            confirmation="Publish the selected articles?",
        )
        async def make_published(
            self, request: Request, selection: ActionSelection
        ) -> None:
            for article in await selection.rows():
                article.published = True
            flash(request, "Articles published")
    ```

Там, где Django Admin передаёт `QuerySet`, обработчик starlette-admin получает объект [`ActionSelection`](../user-guide/actions.md). Он лениво разрешает строки, первичные ключи и активные фильтры и ведёт себя одинаково, когда пользователь выбирает все подходящие записи.

Действия также могут отображать произвольную HTML-форму внутри диалога подтверждения — в Django Admin для этого пришлось бы строить промежуточную страницу. Для операций над отдельными строками используйте [`@row_action` и `@link_row_action`](../user-guide/actions.md#row-actions); аналогов им в Django Admin нет.

## Права доступа и аутентификация

Django Admin полагается на `django.contrib.auth`. starlette-admin разделяет задачу на две: [`AuthProvider`](../user-guide/auth.md) отвечает на вопрос «кто этот пользователь», а [методы представления](../user-guide/views.md#security-and-authorization) — на вопрос «что он может делать».

| Django Admin | starlette-admin |
| --- | --- |
| вход через `django.contrib.auth` | `AuthProvider` (встроенная страница входа) или `OAuthProvider` (редирект по OIDC) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` у представления |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` для конкретного пользователя | `can_access_field(request, field)` |
| Аналога нет | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

Следующее представление разрешает удаление только пользователям с ролью `admin`:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Каждый метод `can_*` получает запрос, поэтому решения об авторизации могут опираться на текущего пользователя, HTTP-заголовки или любые другие данные запроса.

## Хуки сохранения и сигналы

| Django Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) у представления | Нативно асинхронные; получают разобранные данные формы вместе с экземпляром модели. |
| `delete_model` | `before_delete` | Обрабатывает логику перед удалением. |
| `post_save` и другие сигналы | [События](../advanced/events.md) | Например, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` рассылает событие всем представлениям. |
| История изменений `LogEntry` | Реализуется через систему событий | Подпишитесь на `AFTER_CREATE`, `AFTER_EDIT` и `AFTER_DELETE`, чтобы заполнять собственную таблицу аудита. |
| `messages.success(request, ...)` | `flash(request, ...)` | См. [Флеш-сообщения](../user-guide/flash-messages.md). |

## Конфигурация всего сайта

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Собственный логотип через переопределение шаблона | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` с [виджетами](../user-guide/custom-views.md) для полноценного дашборда |
| Переопределение шаблонов в `templates/admin/` | `Admin(templates_dir="...")`, см. [Шаблоны](../advanced/templates.md) |
| Несколько экземпляров `AdminSite` | Несколько экземпляров `Admin`, смонтированных по разным путям приложения |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query` или `get_detail_query` для бэкенда SQLAlchemy |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, см. [i18n и часовые пояса](../user-guide/i18n.md) |

## Что вы получаете при переходе

* **Асинхронность от начала до конца:** обработчики, хуки жизненного цикла и колбэки виджетов могут быть корутинами, выполняющимися в вашем существующем цикле событий рядом с эндпоинтами FastAPI.
* **Гибкость выбора базы данных:** одна и та же конфигурация администрирования работает с SQLAlchemy, SQLModel, MongoDB через MongoEngine или Beanie, а также с Tortoise ORM.
* **Встроенные экспорт и импорт:** CSV, JSON и PDF, а также Excel и другие форматы через `tablib`. Экспортируйте записи напрямую или импортируйте данные пакетами через мастер с предварительным просмотром, который применяет валидацию на уровне строк и поддерживает необязательные upsert'ы по первичному ключу. См. [Экспорт и импорт](../user-guide/export-import.md).
* **Виджеты дашборда:** карточки статистики, ApexCharts и сетки компоновки собираются в индексные страницы и пользовательские представления, поэтому внешний пакет тем для построения дашборда не нужен. См. [Пользовательские представления и виджеты](../user-guide/custom-views.md).
* **Современный пользовательский интерфейс:** Tabler (Bootstrap 5) даёт тёмную тему, переключатели видимости столбцов и подсветку результатов поиска по умолчанию.

## Что придётся реализовать самостоятельно

* **Аутентификация:** встроенной модели пользователя или базы прав нет. Реализуйте `AuthProvider.authenticate()` поверх того хранилища данных, которое уже использует ваше приложение.
* **Журналирование аудита:** starlette-admin не создаёт таблицу `LogEntry`. Подключите [систему событий](../advanced/events.md) к собственной таблице аудита.
* **Конфигурация UI на уровне модели:** удобства Django вроде `choices`, `verbose_name` и валидаторов на уровне модели не переносятся автоматически. Задайте их в поле starlette-admin с помощью `EnumField`, `label=` и `validators=`.
