---
title: Расширяемые административные интерфейсы для FastAPI и Starlette
description: Создавайте полноценный админ-интерфейс на основе ваших моделей SQLAlchemy,
  SQLModel, Beanie, MongoEngine или Tortoise ORM.
keywords:
- fastapi admin
- starlette admin
- python admin panel
- crud dashboard
- admin framework
hide:
- navigation
- toc
source_hash: d144ed398cb294767fbc083f9434f9ff94fb01c5c9c76618db5300ead610e8f6
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/)
<!-- translation-notice:end -->

<div class="home-hero">
  <a class="home-badge" href="changelog/">
    <span class="home-badge-dot"></span>
    Новая документация &nbsp;·&nbsp; Посмотрите, что изменилось
  </a>
  <h1 class="home-title">Расширяемые <span class="home-gradient">административные интерфейсы</span><br>для FastAPI &amp; Starlette</h1>
  <p class="home-sub">Создавайте полноценный административный интерфейс на основе ваших моделей SQLAlchemy, SQLModel, Beanie, MongoEngine или Tortoise ORM. Построенный на базе <a href="https://tabler.io">UI-кита Tabler</a>, starlette-admin предоставляет представления списков, автоматически генерируемые формы, экспорт данных и безопасную аутентификацию. Настройте весь интерфейс на Python, не написав ни строчки frontend-кода.</p>
  <div class="home-actions">
    <a class="md-button md-button--primary home-btn" href="getting-started/quickstart/">Начать работу</a>
    <a class="md-button home-btn" href="https://starlette-admin-demo.jowilf.com/">Живая демонстрация</a>
    <a class="md-button home-btn home-btn--github" href="https://github.com/jowilf/starlette-admin">
      <svg viewBox="0 0 16 16" width="16" height="16" fill="currentColor" aria-hidden="true"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0 0 16 8c0-4.42-3.58-8-8-8z"/></svg>
      Поставить звезду на GitHub
    </a>
  </div>
  <div class="home-pip"><code>pip install starlette-admin</code></div>
  <div class="home-shot">
    <img src="assets/images/list-preview.png" alt="starlette-admin dashboard showing statistical widgets, recent activity tables, and a sidebar for model views" loading="lazy">
  </div>
</div>

<h2 class="home-section-title">Встроенные возможности</h2>
<p class="home-lede">Всё необходимое работает сразу после установки. Каждая ключевая возможность имеет документированные точки расширения, поэтому вы можете адаптировать её под свои требования.</p>

<div class="home-cards">
  <a class="home-card" href="user-guide/views/">
    <span class="home-card-icon hc-sky"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 10h18"/><path d="M10 3v18"/></svg></span>
    <h3>Таблицы</h3>
    <p>Просматривайте, ищите и сортируйте данные с постраничной навигацией, сортировкой по нескольким столбцам и URL, сохраняющими состояние. Редактируйте поля прямо в представлении списка.</p>
  </a>
  <a class="home-card" href="user-guide/filters/">
    <span class="home-card-icon hc-violet"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16v2.172a2 2 0 0 1-.586 1.414L15 12v7l-6 2v-8.5L4.52 7.572A2 2 0 0 1 4 6.227z"/></svg></span>
    <h3>Фильтры</h3>
    <p>Собирайте вложенные запросы AND/OR прямо в интерфейсе, пользуясь операторами, которые учитывают тип данных: текст, числа, даты и логические значения.</p>
  </a>
  <a class="home-card" href="user-guide/fields/">
    <span class="home-card-icon hc-amber"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7H6a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h9a2 2 0 0 0 2-2v-1"/><path d="M20.385 6.585a2.1 2.1 0 0 0-2.97-2.97L9 12v3h3z"/><path d="M16 5l3 3"/></svg></span>
    <h3>Формы и загрузка файлов</h3>
    <p>Автоматически создавайте формы более чем для 25 типов полей и для связанных данных. Отправляйте загруженные файлы в локальное хранилище или S3.</p>
  </a>
  <a class="home-card" href="user-guide/actions/">
    <span class="home-card-icon hc-rose"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 3v7h6l-8 11v-7H5z"/></svg></span>
    <h3>Действия</h3>
    <p>Создавайте массовые и построчные операции с помощью стандартных декораторов Python. Каждый запуск можно защитить модальным окном подтверждения и собственной формой с данными запроса.</p>
  </a>
  <a class="home-card" href="user-guide/export-import/">
    <span class="home-card-icon hc-emerald"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 17v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"/><path d="M7 11l5 5 5-5"/><path d="M12 4v12"/></svg></span>
    <h3>Экспорт и импорт</h3>
    <p>Экспортируйте записи в CSV, Excel, JSON, PDF или любой формат, который поддерживает tablib. Импортируйте данные пакетно с помощью мастера, который сначала показывает предпросмотр и проверяет каждую строку до записи в базу данных.</p>
  </a>
  <a class="home-card" href="user-guide/auth/">
    <span class="home-card-icon hc-indigo"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a12 12 0 0 0 8.5 3A12 12 0 0 1 12 21 12 12 0 0 1 3.5 6 12 12 0 0 0 12 3"/><circle cx="12" cy="11" r="1"/><path d="M12 12v2.5"/></svg></span>
    <h3>Аутентификация и безопасность</h3>
    <p>Подключите провайдер аутентификации, которым вы уже пользуетесь. Разверните проект с настройками по умолчанию, готовыми к production, включая защиту от CSRF и встроенные ограничения на экспорт и импорт.</p>
  </a>
  <a class="home-card" href="user-guide/inline-forms/">
    <span class="home-card-icon hc-cyan"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 5h8"/><path d="M13 9h5"/><path d="M13 15h8"/><path d="M13 19h5"/><rect x="3" y="4" width="6" height="6" rx="1"/><rect x="3" y="14" width="6" height="6" rx="1"/></svg></span>
    <h3>Встроенные формы</h3>
    <p>Управляйте связанными данными на месте. Редактируйте дочерние записи прямо в форме родительской модели, не покидая страницу.</p>
  </a>
  <a class="home-card" href="user-guide/custom-views/">
    <span class="home-card-icon hc-orange"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="12" width="6" height="8" rx="1"/><rect x="9" y="8" width="6" height="12" rx="1"/><rect x="15" y="4" width="6" height="16" rx="1"/></svg></span>
    <h3>Дашборды</h3>
    <p>Соберите главную страницу из встроенных виджетов статистики, графиков и таблиц или замените её полностью настраиваемым представлением.</p>
  </a>
  <a class="home-card" href="user-guide/i18n/">
    <span class="home-card-icon hc-teal"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h7"/><path d="M9 3v2c0 4.418-2.239 8-5 8"/><path d="M5 9c0 2.144 2.952 3.908 6.7 4"/><path d="M12 20l4-9 4 9"/><path d="M19.1 18h-6.2"/></svg></span>
    <h3>i18n и часовые пояса</h3>
    <p>Предоставляйте админ-панель на нескольких языках с форматированием с учётом локали и точной обработкой часовых поясов из коробки.</p>
  </a>
</div>

<div class="home-code-head">
  <svg class="home-code-mark" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8l-4 4 4 4"/><path d="M17 8l4 4-4 4"/><path d="M14 4l-4 16"/></svg>
  <h2 class="home-section-title">Всё — это Python</h2>
  <p class="home-lede">Создавайте полноценный административный интерфейс с помощью чистого Python API, спроектированного для <strong>быстрой разработки</strong>, <strong>читаемого синтаксиса</strong> и <strong>долгосрочной сопровождаемости</strong>.</p>
</div>

=== "Подключение панели"

    <span class="home-tour-title" role="heading" aria-level="3">Подключите админ-панель</span>

    Зарегистрируйте модель и подключите админ-панель к любому приложению FastAPI или Starlette. Затем запустите `fastapi dev` и откройте `/admin`.

    <a class="home-tour-btn" href="getting-started/quickstart/">Открыть документацию</a>

    ```python title="main.py"
    from fastapi import FastAPI
    from sqlalchemy import create_engine
    from starlette_admin.contrib.sqla import Admin, ModelView

    from models import Base, Post

    engine = create_engine("sqlite:///blog.db")
    Base.metadata.create_all(engine)

    app = FastAPI()

    admin = Admin(engine, title="Blog Admin", secret_key="change-me")
    admin.add_view(ModelView(Post, icon="fa fa-newspaper"))
    admin.mount_to(app)
    ```

=== "Views"

    <span class="home-tour-title" role="heading" aria-level="3">Представления</span>

    Настраивайте поиск, сортировку, порядок по умолчанию и форматы экспорта обычными атрибутами класса. Компонуйте формы создания и редактирования с помощью `form_layout`.

    <a class="home-tour-btn" href="user-guide/views/">Открыть документацию</a>

    ```python title="views.py"
    from starlette_admin.contrib.sqla import ModelView


    class PostView(ModelView):
        fields = ["id", "title", "author", "content", "published", "created_at"]
        searchable_fields = ["title", "content"]
        fields_default_sort = [("created_at", True)]
        exporters = ["csv", "xlsx", "json"]
        form_layout = [
            ("title", "author"),
            "content",
            ("published", "created_at"),
        ]


    admin.add_view(PostView(Post, icon="fa fa-newspaper"))
    ```

=== "Fields"

    <span class="home-tour-title" role="heading" aria-level="3">Поля</span>

    Переопределяйте любые автоматически определённые поля, чтобы управлять валидацией, видимостью на отдельных страницах и тем, как starlette-admin считывает и отображает значения.

    <a class="home-tour-btn" href="user-guide/fields/">Открыть документацию</a>

    ```python title="views.py"
    from starlette_admin import DateTimeField, RequestAction, StringField, TextAreaField
    from starlette_admin.contrib.sqla import ModelView


    class PostView(ModelView):
        fields = [
            "id",
            StringField("title", required=True, help_text="Shown on the blog"),
            TextAreaField("content", exclude_from_list=True),
            StringField(
                "author_email",
                getter=lambda request, obj: obj.author.email,
                formatter={RequestAction.LIST: lambda request, value: value or "unset"},
            ),
            DateTimeField("created_at", read_only=True, exclude_from_create=True),
        ]
    ```

=== "Filters"

    <span class="home-tour-title" role="heading" aria-level="3">Фильтры</span>

    Расширяйте встроенный конструктор запросов собственными фильтрами, отвечающими вашим бизнес-правилам. Необходимые операции можно применять непосредственно к модели базы данных.

    <a class="home-tour-btn" href="user-guide/filters/">Открыть документацию</a>

    ```python title="filters.py"
    from datetime import datetime
    from typing import Any

    from starlette_admin.contrib.sqla import ModelView
    from starlette_admin.filters.base import BaseFilter, FilterApplyContext, FilterDataType


    class ActiveThisMonthFilter(BaseFilter):
        name = "this_month"
        label = "Created this month"
        data_type = FilterDataType.NONE  # No value input. The range comes from now().

        def apply(self, ctx: FilterApplyContext) -> Any:
            now = datetime.utcnow()
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            col = getattr(ctx.view.model, ctx.field_name)
            return col.between(start, now)


    class ProductView(ModelView):
        fields = [
            DateTimeField(
                "created_at",
                filters=[ActiveThisMonthFilter, ...],
            ),
        ]
    ```

=== "Actions"

    <span class="home-tour-title" role="heading" aria-level="3">Действия</span>

    Добавляйте бизнес-операции одним декоратором. Окна подтверждения, собственные формы и flash-сообщения уже встроены во framework.

    <a class="home-tour-btn" href="user-guide/actions/">Открыть документацию</a>

    ```python title="views.py"
    from starlette.requests import Request
    from starlette_admin import ActionSelection, action, flash
    from starlette_admin.contrib.sqla import ModelView


    class ArticleView(ModelView):
        actions = ["publish", "delete"]

        @action(
            name="publish",
            text="Mark as published",
            confirmation="Publish the selected articles?",
            submit_btn_text="Yes, publish",
        )
        async def publish(self, request: Request, selection: ActionSelection) -> None:
            articles = await selection.rows()
            for article in articles:
                article.published = True
            flash(request, f"{len(articles)} articles published.", "success")
    ```

=== "Authentication"

    <span class="home-tour-title" role="heading" aria-level="3">Аутентификация</span>

    Реализуйте три стандартных метода поверх собственной проверки учётных данных. starlette-admin возьмёт на себя страницу входа, сессии и перенаправления.

    <a class="home-tour-btn" href="user-guide/auth/">Открыть документацию</a>

    ```python title="auth.py"
    from starlette.requests import Request
    from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed


    class MyAuthProvider(AuthProvider):
        async def login(self, username, password, remember_me, request: Request) -> None:
            if not await check_credentials(username, password):
                raise LoginFailed("Invalid username or password")
            request.session["username"] = username

        async def authenticate(self, request: Request) -> AdminUser | None:
            if username := request.session.get("username"):
                return AdminUser(username=username)
            return None

        async def logout(self, request: Request) -> None:
            request.session.clear()


    admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)
    ```

=== "Dashboard"

    <span class="home-tour-title" role="heading" aria-level="3">Дашборд</span>

    Собирайте главную страницу панели из виджетов статистики, графиков и таблиц, которые запрашивают актуальные данные при каждом обращении.

    <a class="home-tour-btn" href="user-guide/custom-views/">Открыть документацию</a>

    ```python title="dashboard.py"
    from starlette_admin import CardRowWidget, ChartWidget, CustomView, StatWidget

    dashboard = CardRowWidget(
        children=[
            StatWidget(title="Orders", value_callback=count_orders, countup=True),
            StatWidget(title="Revenue", value_callback=sum_revenue, color="success"),
            ChartWidget(title="Sales", chart_type="area", series_callback=sales_series),
        ]
    )

    admin = Admin(
        engine,
        title="Shop Admin",
        secret_key="change-me",
        index_view=CustomView(menu_label="Dashboard", icon="fa fa-home", widget=dashboard),
    )
    ```

<h2 class="home-section-title">Плагины и расширения</h2>
<p class="home-lede">Каждый слой можно заменить. Упаковывайте функциональность в самодостаточные плагины или подключайтесь к выделенным точкам расширения, чтобы адаптировать framework под свою предметную область.</p>

<div class="home-plugins">
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-violet">Готовые плагины</span>
    <h3>Плагины без шаблонного кода</h3>
<p>Установите пакет плагина и передайте его экземпляру <code>Admin</code>. Поля, конвертеры, шаблоны и ассеты подключатся между собой автоматически.</p>
    <div class="home-snippet">

    ```python
    from starlette_admin_geospatial import GeospatialPlugin
    from starlette_admin.contrib.sqla import Admin

    admin = Admin(
        engine,
        plugins=[GeospatialPlugin(default_zoom=13)],
    )
    ```

    </div>
    <a class="home-more" href="advanced/plugins/">Читать руководство по плагинам</a>
  </div>
  <div class="home-plugin-panel">
    <span class="home-eyebrow hc-emerald">Точки расширения</span>
    <h3>Подключайтесь к любому компоненту</h3>
    <p>Предопределённые интерфейсы позволяют независимо заменять или расширять каждый аспект работы системы. Наследуйте нужный базовый класс и зарегистрируйте его. Можно настроить всё: от процесса аутентификации до форматов экспорта.</p>
    <ul class="home-hooks">
      <li><a href="advanced/custom-fields/"><span>Пользовательские поля</span><code>BaseField</code></a></li>
      <li><a href="advanced/custom-filters/"><span>Пользовательские фильтры</span><code>BaseFilter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Экспортеры</span><code>BaseExporter</code></a></li>
      <li><a href="user-guide/export-import/"><span>Импортеры</span><code>BaseImporter</code></a></li>
      <li><a href="advanced/custom-themes/"><span>Темы</span><code>BaseTheme</code></a></li>
      <li><a href="user-guide/auth/"><span>Провайдеры аутентификации</span><code>BaseAuthProvider</code></a></li>
      <li><a href="user-guide/file-storage/"><span>Бэкенды хранения</span><code>BaseStorage</code></a></li>
      <li><a href="user-guide/custom-views/"><span>Виджеты дашборда</span><code>BaseWidget</code></a></li>
      <li><a href="advanced/templates/"><span>Шаблоны</span><code>templates_dir</code></a></li>
    </ul>
    <a class="home-more" href="advanced/extension-points/">Изучить все точки расширения</a>
  </div>
</div>
