---
title: Аутентификация
description: Реализуйте аутентификацию в starlette-admin с помощью AuthProvider или
  интегрируйте OAuth, чтобы защитить ваш дашборд.
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# Аутентификация

Вы защищаете интерфейс администрирования, реализуя один метод:

```python
async def authenticate(request) -> AdminUser | None
```

Каждый защищённый запрос к панели администрирования проходит через этот метод. Если он возвращает `AdminUser`, запрос считается аутентифицированным. Если он возвращает `None`, запрос не аутентифицирован, и управление переходит к настроенному вами процессу входа или OAuth.

В случае успеха возвращённый `AdminUser` попадает в:

```python
request.state.admin_user
```

В случае неудачи запрос помечается как анонимный:

```python
request.state.is_anonymous = True
```

Благодаря этому публичные и частично защищённые маршруты могут различать аутентифицированные и неаутентифицированные запросы без запуска процесса входа.


## Выбор провайдера аутентификации

| Провайдер | Когда использовать | Что нужно реализовать |
| --- | --- | --- |
| `AuthProvider` | Вам нужна встроенная страница входа, а учётные данные вы проверяете сами. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | Вам нужен редирект-процесс OAuth2 или OIDC, например с Auth0, Okta или Google. | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Оба класса наследуются от `BaseAuthProvider` и следуют одному контракту. Метод `authenticate()` выполняется при каждом запросе. То, что он возвращает, становится значением `request.state.admin_user`; если он возвращает `None`, фреймворк устанавливает `request.state.is_anonymous = True`.

## `AuthProvider`: встроенная страница входа

Используйте этот провайдер, если хотите, чтобы фреймворк отображал и обрабатывал форму входа, а проверку учётных данных вы выполняли самостоятельно. Фреймворк отвечает за шаблон, обработку POST-запросов и перенаправление.

Вот полный пример:

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin

SECRET = "change-me-in-production"

# Demo user store: replace with a real lookup against your database
USERS = {"admin": {"name": "Administrator", "password": "password"}}


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return AdminUser(username=user["name"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


engine = create_engine("sqlite:///admin.sqlite")
app = Starlette(middleware=[Middleware(SessionMiddleware, secret_key=SECRET)])
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key=SECRET
)
admin.mount_to(app)
```

### Обязательные методы

Класс `AuthProvider` реализует три метода. Здесь требуется `SessionMiddleware`, поскольку именно он сохраняет состояние входа пользователя между запросами.

#### `login()`

Этот метод обрабатывает отправку формы. Он получает `username`, `password`, логическое значение `remember_me` и текущий `request`.

* **При успехе:** запишите идентификатор, например ID пользователя или имя пользователя, в `request.session`. Затем верните `None`, чтобы фреймворк перенаправил на `next` или на главную страницу панели администрирования, либо верните `Response`, чтобы перенаправить в другое место.
* **При неудаче:** вызовите исключение `LoginFailed("message")`, чтобы показать ошибку над формой, или `FormValidationError({"username": "..."})`, чтобы пометить конкретное поле как недопустимое.

#### `authenticate()`

Этот метод выполняется при *каждом* запросе к защищённому маршруту панели администрирования. Он получает объект `request`.

* Прочитайте идентификатор, который вы сохранили в `request.session` во время `login()`.
* Найдите пользователя в вашей базе данных.
* Верните экземпляр `AdminUser`, если пользователь существует и действителен.
* Верните `None`, если пользователь не существует или не выполнил вход.

#### `logout()`

Этот метод обрабатывает выход из системы. Он получает объект `request`, и вы очищаете данные пользователя из `request.session`, чтобы отозвать доступ. Верните `None` для стандартного перенаправления на главную страницу панели администрирования или верните `Response`, чтобы перенаправить в другое место.

## `OAuthProvider`: редирект-процесс OAuth2/OIDC {#oauthprovider-oauth2oidc-redirect-flow}


Используйте `OAuthProvider`, когда вы делегируете аутентификацию внешнему поставщику идентификации, такому как Auth0, Okta, Google или Microsoft Entra ID.

`AuthProvider` обрабатывает форму с именем пользователя и паролем внутри панели администрирования. `OAuthProvider` вместо этого использует редирект-процесс:

1. Перенаправьте пользователя к поставщику идентификации.
2. Поставщик аутентифицирует пользователя.
3. Поставщик перенаправляет обратно в ваше приложение.
4. Ваше приложение обменивает колбэк на идентификатор пользователя.
5. `authenticate()` восстанавливает пользователя из сессии.

### Настройка URL колбэка (обязательно)

Прежде чем реализовать `OAuthProvider`, зарегистрируйте URL колбэка вашего приложения в дашборде поставщика идентификации. В целях безопасности поставщики OAuth перенаправляют только на заранее одобренные URL.

#### Пример URL колбэка

```text
https://your-domain.com/admin/oauth/callback
```

#### Локальная разработка

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    Точный URL колбэка зависит от вашей конфигурации. Он формируется из `route_name`, который вы указываете при монтировании `Admin`, плюс `callback_path` провайдера.

    Конфигурация по умолчанию использует:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    что даёт следующий URL колбэка:

    ```text
    /admin/oauth/callback
    ```

    В развёрнутом виде это выглядит так:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    Если вы измените префикс монтирования или путь колбэка провайдера, URL изменится соответствующим образом, и вам придётся обновить его в конфигурации вашего OAuth-провайдера.

### Обязательные методы

Класс `OAuthProvider` использует тот же механизм на основе сессии, что и `AuthProvider`, но разделяет вход на два шага: перенаправление и колбэк.

#### `redirect_to_provider()`

Этот метод запускает OAuth-процесс. Он получает `request` и сгенерированный `callback_url` и должен вернуть `Response`, который перенаправляет браузер пользователя к вашему поставщику идентификации.

#### `handle_callback()`

Этот метод выполняется, когда браузер возвращается от поставщика с кодом авторизации. Он получает `request`. Обменяйте код на токен доступа, получите профиль пользователя и сохраните его идентификатор в `request.session`.

#### `authenticate()`

Как и в случае с `AuthProvider`, этот метод читает то, что `handle_callback()` сохранил в сессии. Верните `AdminUser`, если в сессии есть корректные данные пользователя, иначе верните `None`.

#### `logout()`

Очистите данные сессии. Чтобы также выйти пользователя из системы поставщика идентификации (OIDC RP-initiated logout), переопределите этот метод и верните `Response` с перенаправлением на эндпоинт завершения сессии поставщика вместо возврата `None`.

Вот полный пример:

```python
import os

from authlib.integrations.starlette_client import OAuth
from starlette.datastructures import URL
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.status import HTTP_303_SEE_OTHER
from starlette_admin.auth import AdminUser, OAuthProvider

AUTH0_CLIENT_ID = os.getenv("AUTH0_CLIENT_ID", "your-auth0-client-id")
AUTH0_CLIENT_SECRET = os.getenv("AUTH0_CLIENT_SECRET", "your-auth0-client-secret")
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN", "your-auth0-domain")

oauth = OAuth()
oauth.register(
    "auth0",
    client_id=AUTH0_CLIENT_ID,
    client_secret=AUTH0_CLIENT_SECRET,
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f"https://{AUTH0_DOMAIN}/.well-known/openid-configuration",
)


class Auth0Provider(OAuthProvider):
    async def redirect_to_provider(
        self, request: Request, callback_url: str
    ) -> Response:
        client = oauth.create_client("auth0")
        return await client.authorize_redirect(request, callback_url)

    async def handle_callback(self, request: Request) -> None:
        client = oauth.create_client("auth0")
        token = await client.authorize_access_token(request)
        request.session["user"] = dict(token["userinfo"])

    async def authenticate(self, request: Request) -> AdminUser | None:
        user = request.session.get("user")
        if user:
            return AdminUser(username=user["name"], photo_url=user.get("picture"))
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()
        client = oauth.create_client("auth0")
        metadata = await client.load_server_metadata()
        end_session_endpoint = metadata.get("end_session_endpoint")
        if end_session_endpoint:
            logout_url = str(
                URL(end_session_endpoint).include_query_params(
                    post_logout_redirect_uri="https://www.google.com/",
                    client_id=AUTH0_CLIENT_ID,
                )
            )
            return RedirectResponse(logout_url, status_code=HTTP_303_SEE_OTHER)
        return None


SECRET_KEY = "change-me"
engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
# required because Auth0Provider's handle_callback/authenticate methods use request.session
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

admin = Admin(
    engine, title="My Admin", auth_provider=Auth0Provider(), secret_key=SECRET_KEY
)
admin.mount_to(app)
```

## Регистрация провайдера

После реализации провайдера аутентификации подключите его к экземпляру `Admin`.

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

Эта одна строка — вся интеграция. `Admin` монтирует `AuthMiddleware` провайдера перед каждым маршрутом панели администрирования и добавляет маршруты провайдера (вход, выход и колбэк для `OAuthProvider`) внутрь префикса панели администрирования.

## Проверки прав доступа

Аутентификация отвечает на вопрос «Кто это?». Права доступа отвечают на вопрос «Что им можно делать?». Права принадлежат представлению. Доступ на основе ролей состоит из трёх шагов:

1. Создайте подкласс `AdminUser` — обычного дата-класса — и добавьте список `roles`.
2. Возвращайте этот подкласс из метода `authenticate()` вашего провайдера, заполняя его данными из вашего хранилища пользователей.
3. Читайте `request.state.admin_user.roles` в хуках проверки прав представления.

```python
from dataclasses import dataclass, field
from typing import Any

from starlette.requests import Request
from starlette_admin import action, row_action
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.exceptions import ActionFailed
from starlette_admin.fields import BaseField
from starlette_admin.types import RequestAction

# Demo user store: replace with a real lookup against your database
USERS = {
    "admin": {
        "name": "Administrator",
        "password": "password",
        "roles": ["read", "create", "edit", "delete", "read_body", "publish"],
    },
    "editor": {
        "name": "Editor",
        "password": "password",
        "roles": ["read", "create", "edit", "read_body", "publish"],
    },
    "viewer": {"name": "Viewer", "password": "password", "roles": ["read"]},
}


# Step 1: AdminUser is a plain dataclass, so subclassing it to add `roles` is
# the intended pattern rather than a workaround.
@dataclass
class MyAdminUser(AdminUser):
    roles: list[str] = field(default_factory=list)


class MyAuthProvider(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        user = USERS.get(username)
        if user and password == user["password"]:
            request.session["username"] = username
            return
        raise LoginFailed("Invalid username or password")

    # Step 2: authenticate() looks up the roles for the signed-in user and
    # returns them on a MyAdminUser instead of a plain AdminUser.
    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("username")
        user = USERS.get(username)
        if user:
            return MyAdminUser(username=user["name"], roles=user["roles"])
        return None

    async def logout(self, request: Request) -> None:
        request.session.clear()


# Step 3: Every hook below reads request.state.admin_user.roles, which is
# populated only because authenticate() returned a MyAdminUser.
class ArticleView(ModelView):
    def is_accessible(self, request: Request) -> bool:
        return "read" in request.state.admin_user.roles  # Hides the view entirely

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.admin_user.roles

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.admin_user.roles

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.admin_user.roles

    def can_access_field(
        self, request: Request, field: BaseField, action: RequestAction | None = None
    ) -> bool:
        if field.name == "body":
            return "read_body" in request.state.admin_user.roles
        return super().can_access_field(request, field, action)

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "publish":
            return "publish" in request.state.admin_user.roles
        return await super().is_action_allowed(request, name)
```

Зарегистрируйте `MyAuthProvider` как любой другой провайдер: `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. После этого каждый из перечисленных выше хуков получит доступ к `request.state.admin_user.roles`.

Метод `is_accessible()`, доступный в каждом `BaseView`, скрывает представление целиком, включая его пункт в боковом меню. Методы `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import` и `can_view_detail` ограничивают отдельные операции в `ModelView`. Метод `can_access_field` скрывает конкретные поля, а `is_action_allowed` и `is_row_action_allowed` ограничивают групповые действия и действия над строкой. Когда действие над строкой зависит от самой записи, а не от пользователя — например, скрытие `publish` для уже опубликованной статьи, — переопределите вместо этого метод `is_row_action_allowed_for_obj(request, name, obj)`. Он получает базовый объект строки и в качестве резервного варианта обращается к `is_row_action_allowed`.

Полную справку по API см. в документации [Представления](views.md) и [Действия](actions.md). Полный рабочий пример с `can_export`, `can_import` и действием над строкой находится в [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Некоторые маршруты остаются публичными даже в закрытой панели администрирования, например форма самостоятельной регистрации или проверка работоспособности. Добавьте декоратор к эндпоинту, и `AuthMiddleware` пропустит запрос без проверки результата `authenticate()`:

```python
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette_admin import CustomView, route
from starlette_admin.auth import login_not_required


class AccountsView(CustomView):
    menu_label = "Accounts"
    path = "/accounts"

    @route("/register", methods=["GET", "POST"], name="register")
    @login_not_required
    async def register(self, request: Request) -> Response:
        if request.method == "GET":
            return self.templates.TemplateResponse(
                request=request, name="register.html", context={}
            )
        form = await request.form()
        # Create the user account before granting access to the panel
        await create_user(email=form["email"], password=form["password"])
        return RedirectResponse(request.url_for("admin:login"), status_code=302)
```

И `@route`, и `@login_not_required` помечают функцию атрибутом и возвращают её без изменений, поэтому порядок их применения не имеет значения.

## `allow_routes`

`allow_routes` даёт тот же обходной механизм, но на уровне имени маршрута, а не функции. Используйте его, когда вы не управляете определением эндпоинта или когда хотите держать список исключений в одном месте:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

Строка — это имя маршрута: либо имя метода, либо значение, переданное в параметр `name=` декоратора `@route`, например `name="register"` выше. `AuthMiddleware` всегда разрешает `"login"` и `"static"` в дополнение к указанным вами пользовательским маршрутам.

## `AdminUser`

То, что возвращает `authenticate()`, заполняет `request.state.admin_user`. Верхняя панель читает из него два поля:

| Атрибут | Тип | По умолчанию | Описание |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (переводится) | Имя, отображаемое в меню пользователя верхней панели. |
| `photo_url` | `str | None` | `None` | URL изображения аватара. Если не задано, используется иконка-заглушка. |

`AdminUser` — обычный `@dataclass`, поэтому создание подкласса для хранения ролей, ID арендатора или любых других данных, необходимых вашим хукам проверки прав, — это предусмотренный шаблон использования. Пример `MyAdminUser` выше показывает это на практике.

---

**Что дальше**

* [Безопасность](security.md): CSRF, секретные ключи и то, что фреймворк защищает автоматически.
* [Представления](views.md): `can_create`, `can_edit`, `can_delete` и полный список хуков проверки прав.
* [Действия](actions.md): `is_action_allowed` и `is_row_action_allowed` для групповых действий и действий над строкой.
