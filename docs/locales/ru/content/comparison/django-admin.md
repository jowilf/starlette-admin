---
title: Переход с Django Admin
description: Подробное руководство по миграции, сопоставляющее концепции Django Admin
  с эквивалентами starlette-admin для создания декларативных административных интерфейсов.
source_hash: a6ce6a3317c78ccc26347c432872c69131a6677381bb4750eb4380f6fb0ba094
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/comparison/django-admin/)
<!-- translation-notice:end -->

# Переход с Django Admin

Если вы знакомы с Django Admin, starlette-admin покажется вам привычным инструментом. Оба решения генерируют административный интерфейс на основе декларативной конфигурации для каждой модели, а также поддерживают инлайн-редактирование, пакетные действия и разрешения на уровне каждого запроса.

Различия носят структурный характер. starlette-admin работает поверх любого ASGI-приложения вместо обязательного использования Django, поддерживает несколько ORM и позволяет подключить собственную аутентификацию, не навязывая встроенную модель пользователя.

В этом руководстве каждая основная концепция `ModelAdmin` сопоставлена со своим эквивалентом в starlette-admin, с примерами кода рядом.

## Концептуальная модель

| Концепция Django Admin | Эквивалент в starlette-admin |
| --- | --- |
| `AdminSite` | экземпляр [`Admin`](../api/admin.md), подключённый к вашему приложению |
| `ModelAdmin` | подкласс [`ModelView`](../user-guide/views.md) |
| `admin.site.register(Model, ModelAdmin)` | `admin.add_view(MyView(Model))` |
| `admin.site.urls` в `urlpatterns` | `admin.mount_to(app)` |
| Django ORM | SQLAlchemy, SQLModel, MongoEngine, Beanie или Tortoise ORM через `starlette_admin.contrib.*` |
| `__str__` на модели | `__admin_repr__(self, request)` — асинхронный метод, учитывающий запрос |
| Поля формы, выводимые из полей модели | [Поля](../user-guide/fields.md), выводимые конвертером backend'а, с возможностью настройки для каждого поля |

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

Обратите внимание на два структурных отличия:

1. **Один список полей управляет всеми страницами.** Атрибут `fields` — единственный источник истины. Для вариаций по страницам используются [`exclude_fields_from_list`, `exclude_fields_from_detail`, `exclude_fields_from_create` и `exclude_fields_from_edit`](../user-guide/views.md#field-selection-and-customization).
2. **Экземпляр `Admin` владеет движком базы данных.** Вам не нужно передавать сессию каждому представлению.

## Настройки страницы списка

| Django Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `list_display` | `fields` минус [`exclude_fields_from_list`](../user-guide/views.md#field-selection-and-customization) | Один список полей управляет всеми страницами. |
| `list_display` с callable или `@admin.display` | [`ComputedField`](../user-guide/fields.md#computedfield) либо `getter=` у любого поля | Например, `ComputedField("full_name", getter=lambda request, obj: ...)`. Используйте `getter=` у типизированного поля, например поля даты или изображения, чтобы сохранить его способ отображения. |
| Переформатирование реального столбца для отображения | [`formatter=`](../user-guide/fields.md#computing-formatting-and-parsing-values) у поля | Это `dict[RequestAction, callable]`, поэтому список, детальная страница и экспорт могут форматировать данные по-разному. В Django требуется callable плюс `admin_order_field`, чтобы сохранить сортировку; здесь столбец остаётся сортируемым. |
| `search_fields` | [`searchable_fields`](../user-guide/views.md#search-and-sort) | Обеспечивает как полнотекстовый поиск, так и конструктор фильтров. |
| `list_filter` | `searchable_fields` в сочетании с `filters=` для каждого поля | Пользователи получают визуальный конструктор с вложенными группами `AND`/`OR` вместо фиксированной боковой панели. См. раздел [Фильтры](../user-guide/filters.md). |
| `ordering` | [`fields_default_sort`](../user-guide/views.md#search-and-sort) | Например, `fields_default_sort = [("created_at", True)]` выполняет сортировку по убыванию. |
| `admin_order_field` / возможность сортировки | [`sortable_fields`](../user-guide/views.md#search-and-sort) | По умолчанию каждое поле можно сортировать. |
| `list_editable` | [`inline_editable_fields`](../user-guide/inline-edit.md) | Пользователи выделяют ячейку и редактируют её прямо на месте. |
| `list_per_page` | [`page_size`, `page_size_options`](../user-guide/views.md#pagination-and-ui-controls) | Управляет ограничениями пагинации. |
| `date_hierarchy` | Фильтры по датам, такие как `between` и `in the past` | Отдельной панели drill-down нет; этот сценарий покрывается конструктором фильтров. |
| `empty_value_display` | Запись `formatter=` или `null_template` | Formatter'ы получают значения `None`, поэтому могут подставлять заполнитель. `null_template` заменяет сам отрисованный HTML-код. |

## Формы

| Django Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `fields` / `exclude` | `fields`, `exclude_fields_from_create`, `exclude_fields_from_edit` | Управляют видимостью полей формы. |
| `fieldsets` | [`form_layout`](../advanced/form-layout.md) | Свободная компоновка с помощью `FieldsetWidget`, `TabsWidget`, `GridWidget` и `RowWidget`. |
| `readonly_fields` | `read_only=True` у поля | Поле также можно исключить из представлений создания и редактирования. |
| `prepopulated_fields` | [`SlugField("slug", populate_from="title")`](../user-guide/fields.md#slugfield) | То же поведение живой slug-генерации. |
| `autocomplete_fields`, `raw_id_fields` | Стандартное поведение [`HasOne` / `HasMany`](../user-guide/fields.md#hasone-hasmany) | Виджеты отношений — это Select2-поля с серверным поиском «из коробки». |
| `filter_horizontal` / `filter_vertical` | [`HasMany`](../user-guide/fields.md#hasone-hasmany) | Отображается как компонент множественного выбора с поиском. |
| `formfield_overrides` | Явные записи в списке `fields` | Заменяет автоматически определённое поле напрямую: `fields = ["id", TextAreaField("bio")]` |
| Кастомная валидация формы | Field `validators=` или `FormValidationError` в hook'ах | См. [Валидаторы](../api/validators.md). |
| Form field `to_python()` / кастомное приведение типов | [`parser=`](../user-guide/fields.md#computing-formatting-and-parsing-values) у поля | Заменяет стандартное парсинг-поведение поля при отправке форм или импорте для конкретного `RequestAction`. |
| Help text поля модели | `help_text=` | Доступно в любом определении поля. |

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

Возможности `form_layout` шире, чем у fieldsets: можно создавать вкладки, адаптивные сетки и вложенные макеты. См. [Form Layout](../advanced/form-layout.md).

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

starlette-admin определяет внешний ключ автоматически, если он однозначен, и поддерживает составные внешние ключи. Расширенные конфигурации описаны в разделе [Inline Forms](../user-guide/inline-forms.md).

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

Там, где Django Admin передаёт `QuerySet`, обработчик starlette-admin получает объект [`ActionSelection`](../user-guide/actions.md). Он лениво разрешает строки, первичные ключи и активные фильтры и ведёт себя одинаково, когда пользователь выбирает все совпадающие записи.

Действия также могут отрисовывать собственную HTML-форму внутри диалога подтверждения — в Django Admin для этого пришлось бы создавать промежуточную страницу. Для операций над отдельными строками используйте [`@row_action` и `@link_row_action`](../user-guide/actions.md#row-actions); аналогов в Django Admin у них нет.

## Разрешения и аутентификация

Django Admin делегирует эти задачи модулю `django.contrib.auth`. starlette-admin разделяет проблему на две части: [`AuthProvider`](../user-guide/auth.md) отвечает на вопрос «кто этот пользователь», а [методы представлений](../user-guide/views.md#security-and-authorization) — на вопрос «что он может делать».

| Django Admin | starlette-admin |
| --- | --- |
| вход через `django.contrib.auth` | `AuthProvider` (встроенная страница входа) или `OAuthProvider` (redirect-процесс OIDC) |
| `request.user` | `request.state.admin_user` |
| `has_module_permission` | `is_accessible(request)` у представления |
| `has_view_permission` | `can_view_detail(request)` |
| `has_add_permission` | `can_create(request)` |
| `has_change_permission` | `can_edit(request)` |
| `has_delete_permission` | `can_delete(request)` |
| `get_readonly_fields` для каждого пользователя | `can_access_field(request, field)` |
| Аналог отсутствует | `can_export(request)`, `can_import(request)`, `is_action_allowed(request, name)` |

Следующее представление разрешает удаление только пользователям с ролью `admin`:

```python
class ArticleView(ModelView):
    def can_delete(self, request: Request) -> bool:
        return "admin" in request.state.admin_user.roles
```

Каждый метод `can_*` получает запрос, поэтому ваши решения об авторизации могут опираться на текущего пользователя, HTTP-заголовки или любые другие данные запроса.

## Hook'и сохранения и сигналы

| Django Admin | starlette-admin | Примечания |
| --- | --- | --- |
| `save_model(request, obj, form, change)` | [`before_create` / `before_edit`](../user-guide/views.md#lifecycle-hooks) у представления | Изначально асинхронные; получают разобранные данные формы вместе с экземпляром модели. |
| `delete_model` | `before_delete` | Обрабатывает логику, предшествующую удалению. |
| `post_save` и другие сигналы | [События](../advanced/events.md) | Например, `admin.events.on(AdminEvent.AFTER_CREATE, handler)` рассылает уведомление всем представлениям. |
| История изменений `LogEntry` | Реализуется через систему событий | Подпишитесь на `AFTER_CREATE`, `AFTER_EDIT` и `AFTER_DELETE`, чтобы заполнять собственную таблицу аудита. |
| `messages.success(request, ...)` | `flash(request, ...)` | См. [Flash Messages](../user-guide/flash-messages.md). |

## Конфигурация уровня всего сайта

| Django Admin | starlette-admin |
| --- | --- |
| `admin.site.site_header`, `site_title` | `Admin(title="...")` |
| Собственный логотип через переопределение шаблона | `Admin(logo_url="...", login_logo_url="...", favicon_url="...")` |
| `AdminSite.index_template` | `Admin(index_view=...)` с [widget'ами](../user-guide/custom-views.md) для полноценной dashboard-страницы |
| Переопределения шаблонов в `templates/admin/` | `Admin(templates_dir="...")`, см. [Templates](../advanced/templates.md) |
| Несколько экземпляров `AdminSite` | Несколько экземпляров `Admin`, подключённых по разным путям приложения |
| `ModelAdmin.get_queryset` | `get_list_query`, `get_count_query` или `get_detail_query` для backend'а SQLAlchemy |
| `USE_I18N`, `LANGUAGES` | `Admin(i18n_config=I18nConfig(default_locale="fr"))` |
| `TIME_ZONE` | `Admin(timezone_config=TimezoneConfig(...))`, см. [i18n and Timezones](../user-guide/i18n.md) |

## Что вы получаете при переходе

* **Сквозная асинхронность:** Обработчики, lifecycle hook'и и callback'и widget'ов могут быть корутинами, выполняющимися в вашем существующем event loop рядом с endpoint'ами FastAPI.
* **Гибкость в выборе БД:** Одна и та же конфигурация админ-панели работает независимо от того, используете ли вы SQLAlchemy, SQLModel, MongoDB через MongoEngine или Beanie либо Tortoise ORM.
* **Встроенный экспорт и импорт:** CSV, JSON и PDF, плюс Excel и другие форматы через `tablib`. Экспортируйте записи напрямую или импортируйте данные пакетно с помощью wizard'а, который сначала показывает предпросмотр, обеспечивает валидацию на уровне строк и поддерживает опциональный upsert по первичному ключу. См. [Export and Import](../user-guide/export-import.md).
* **Widget'ы для дашборда:** Карточки статистики, ApexCharts и сетки макетов компонуются в index-страницы и custom view, поэтому для создания дашборда не нужен внешний пакет с темой. См. [Custom Views and Widgets](../user-guide/custom-views.md).
* **Современный пользовательский интерфейс:** Tabler (Bootstrap 5) даёт тёмную тему, переключатели видимости столбцов и подсветку результатов поиска по умолчанию.

## Что нужно реализовать самостоятельно

* **Аутентификация:** Встроенной модели пользователя или базы разрешений нет. Реализуйте `AuthProvider.authenticate()`, опираясь на хранилище данных, которое уже используется вашим приложением.
* **Журналирование аудита:** starlette-admin не генерирует таблицу `LogEntry`. Подключите [систему событий](../advanced/events.md) к собственной таблице аудита.
* **Конфигурация UI на уровне модели:** Удобства Django вроде модельных `choices`, `verbose_name` и валидаторов автоматически не переносятся. Задайте их на уровне поля starlette-admin с помощью `EnumField`, `label=` и `validators=`.
