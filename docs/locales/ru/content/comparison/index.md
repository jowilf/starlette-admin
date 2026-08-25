---
source_hash: 7d6cd31a303552e61610bea128e3774a750ae1b417d7633fbffbf94df239a4cf
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/comparison/)
<!-- translation-notice:end -->

---
title: Сравнение starlette-admin, Django Admin и Flask-Admin
description: Сравнение starlette-admin, Django Admin и Flask-Admin бок о бок: веб-стеки, поддерживаемые ORM, глубина функциональности и компромиссы.
---

# Сравнение starlette-admin, Django Admin и Flask-Admin

Django Admin, Flask-Admin и starlette-admin решают одну и ту же задачу: они генерируют готовый к использованию в продакшене административный интерфейс на основе ваших моделей данных, избавляя от необходимости писать экраны CRUD вручную. Различаются они целевыми веб-стеками, поддерживаемыми ORM и тем, сколько функциональности встроено изначально, а что остаётся реализовать вам.

Эта страница сравнивает все три инструмента. Если вы уже знакомы с Django Admin или Flask-Admin и хотите получить прямое соответствие API, обратитесь к соответствующему руководству по миграции:

* [Переход с Django Admin](django-admin.md)
* [Переход с Flask-Admin](flask-admin.md)

## Краткое сравнение

| | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| **Веб-фреймворк** | Только Django | Только Flask | Starlette, FastAPI и любое ASGI-приложение, способное монтировать субприложения |
| **Модель выполнения** | Синхронная (WSGI-first) | Синхронная (WSGI) | Async-first (ASGI) |
| **Слой данных** | Только Django ORM | SQLAlchemy, MongoEngine, peewee, pymongo | SQLAlchemy, SQLModel, MongoEngine, Beanie, Tortoise ORM или [собственный backend](../integrations/custom-backend.md) |
| **UI-инструментарий** | Шаблоны Django, классическая тема админки | Bootstrap 2/3/4 | [Tabler](https://tabler.io) (Bootstrap 5), тёмная тема, [собственные темы](../advanced/custom-themes.md) |
| **Входит в состав фреймворка** | Да, часть Django | Нет, отдельный пакет | Нет, отдельный пакет |
| **Аутентификация** | Встроена через `django.contrib.auth` | Своя собственная (`is_accessible`) | Подключаемый [`AuthProvider` / `OAuthProvider`](../user-guide/auth.md), собственное хранилище пользователей |

## Когда подходит каждый из фреймворков

### Django Admin

Django Admin подходит для нативных Django-приложений. Он зрелый и интегрируется с `django.contrib.auth`, поэтому вы получаете пользователей, группы, разрешения на уровне моделей и историю изменений без какой-либо настройки. Работает он только внутри Django.

### Flask-Admin

Flask-Admin принёс автогенерацию во Flask и популяризировал стиль конфигурации через `ModelView`. Он синхронный и привязан к Flask, поэтому не работает на асинхронном стеке.

### starlette-admin

starlette-admin ориентирован на асинхронный Python-стек. Если ваше приложение использует FastAPI или Starlette, вы просто монтируете админку в своё приложение, и она выполняется в том же event loop. Он работает как с SQL-, так и с NoSQL-слоями данных, сохраняет стиль конфигурации `ModelView`, пришедший из Flask-Admin, и покрывает глубину функциональности, которую ожидают пользователи Django Admin: инлайны, пакетные действия, разрешения на уровне запроса и интернационализацию.

## Матрица возможностей

**Обозначения:**

* **Да:** встроено
* **Частично:** возможно через сторонние пакеты или собственный код
* **Нет:** недоступно

| Возможность | Django Admin | Flask-Admin | starlette-admin |
| --- | --- | --- | --- |
| Автогенерация CRUD-представлений | **Да** | **Да** | **Да** |
| Полнотекстовый поиск | **Да** `search_fields` | **Да** `column_searchable_list` | **Да** [`searchable_fields`](../user-guide/filters.md) |
| Фильтры по столбцам | **Да** `list_filter` | **Да** `column_filters` | **Да** [Визуальный конструктор фильтров](../user-guide/filters.md) с группами `AND`/`OR` |
| Сортировка и порядок по умолчанию | **Да** | **Да** | **Да** [`sortable_fields`, `fields_default_sort`](../user-guide/views.md#search-and-sort) |
| Инлайн-редактирование в списке | **Да** `list_editable` | **Да** `column_editable_list` | **Да** [`inline_editable_fields`](../user-guide/inline-edit.md) |
| Инлайн-формы для связанных моделей | **Да** `TabularInline` / `StackedInline` | **Да** `inline_models` | **Да** [`InlineModelView`](../user-guide/inline-forms.md) |
| Пакетные действия | **Да** `actions` | **Да** `@action` | **Да** [`@action`](../user-guide/actions.md) с диалогами подтверждения и пользовательскими формами |
| Действия для отдельной строки | **Частично** пользовательские шаблоны | **Частично** пользовательские форматтеры | **Да** [`@row_action`, `@link_row_action`](../user-guide/actions.md#row-actions) |
| Экспорт данных | **Частично** `django-import-export` | **Да** CSV и другие форматы | **Да** [CSV, JSON, Excel, PDF](../user-guide/export-import.md) |
| Импорт данных | **Частично** `django-import-export` | **Нет** | **Да** [CSV, JSON, Excel](../user-guide/export-import.md) с проверкой предпросмотра и upsert |
| Загрузка файлов и изображений | **Да** `FileField` / `ImageField` | **Частично** требуется дополнительная настройка | **Да** [Локальное хранилище и S3](../user-guide/file-storage.md) |
| Виджеты панели управления | **Частично** сторонние темы | **Частично** собственная index view | **Да** [Встроенная система виджетов](../user-guide/custom-views.md) |
| Собственные отдельные страницы | **Да** собственные URL у `AdminSite` | **Да** `BaseView` + `@expose` | **Да** [`CustomView`](../user-guide/custom-views.md) |
| Управление раскладкой формы | **Да** `fieldsets` | **Да** `form_rules` | **Да** [`form_layout`](../advanced/form-layout.md) с вкладками и сетками |
| Аутентификация | **Да** `django.contrib.auth` | **Нет** своя собственная | **Да** [`AuthProvider`](../user-guide/auth.md) или `OAuthProvider` |
| Разрешения на уровне модели | **Да** система разрешений | **Да** переопределение флагов `can_*` | **Да** [методы на уровне запроса](../user-guide/views.md#security-and-authorization) |
| Разрешения на уровне поля | **Частично** `get_readonly_fields` | **Нет** | **Да** [`can_access_field`](../user-guide/views.md#security-and-authorization) |
| Хуки жизненного цикла | **Да** `save_model`, signals | **Да** `on_model_change` | **Да** [Хуки жизненного цикла](../user-guide/views.md#lifecycle-hooks) и [events](../advanced/events.md) |
| Защита от CSRF | **Да** middleware Django | **Да** через Flask-WTF | **Да** [Встроена в `Admin`](../user-guide/security.md) |
| История изменений / журнал аудита | **Да** `LogEntry` | **Нет** | **Частично** реализуйте самостоятельно с помощью [events](../advanced/events.md) |
| Интернационализация | **Да** | **Да** через Flask-Babel | **Да** [`I18nConfig`](../user-guide/i18n.md) |
| Несколько экземпляров админки | **Да** несколько `AdminSite` | **Да** | **Да** [Несколько монтирований `Admin`](../advanced/multiple-admin.md) |
| Поддержка async ORM | **Частично** | **Нет** | **Да** асинхронные SQLAlchemy, Beanie, Tortoise ORM |

## Компромиссы

* **Полноценная система пользователей:** Django Admin поставляется с целостной системой управления пользователями. `django.contrib.auth` берёт на себя пользователей, группы, разрешения и управление паролями. В starlette-admin вы реализуете `authenticate()` поверх собственного хранилища данных — это больше работы на старте, зато больше архитектурной свободы впоследствии.
* **Автоматизированная история изменений:** Django Admin записывает историю изменений в `LogEntry`. В starlette-admin вы создаёте журнал аудита самостоятельно, подписываясь на [events](../advanced/events.md) жизненного цикла. Это занимает несколько строк кода, но не происходит автоматически.
* **Экосистема сторонних пакетов:** у Django Admin обширная экосистема сторонних пакетов для тем, виджетов и рабочих процессов с данными. starlette-admin покрывает многие из этих функций нативно, однако специфичное расширение, на которое вы рассчитываете, может пока отсутствовать.
* **Управление файлами:** Flask-Admin поставляется с `FileAdmin` — обозревателем файловой системы сервера. starlette-admin работает с файлами, привязанными к полям моделей, через [локальный диск или S3](../user-guide/file-storage.md), но универсального обозревателя файлов сервера у него нет.

## Дальнейшие шаги

* Переходите с Django? Прочитайте [Переход с Django Admin](django-admin.md).
* Переходите с Flask-Admin? Прочитайте [Переход с Flask-Admin](flask-admin.md).
* Начинаете с нуля? Руководство [Quickstart](../getting-started/quickstart.md) поможет получить работающий административный интерфейс за считанные минуты.
