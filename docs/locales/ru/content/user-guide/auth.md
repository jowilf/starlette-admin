---
title: Аутентификация
description: Реализуйте аутентификацию в starlette-admin с помощью AuthProvider или
  интегрируйте OAuth для защиты вашей панели.
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# Аутентификация

Вы защищаете интерфейс администрирования, реализуя один метод:

```python
async def authenticate(request) -> AdminUser | None
```

Каждый защищённый запрос к панели проходит через этот метод. Если он возвращает `AdminUser`, запрос считается аутентифицированным. Если он возвращает `None`, запрос считается неаутентифицированным, и в работу вступает настроенный вами процесс входа или OAuth.

В случае успеха возвращённый объект `AdminUser` сохраняется в:

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
| `AuthProvider` | Вам нужна встроенная страница входа, а учётные данные вы проверяете самостоятельно. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | Вам нужен redirect-процесс OAuth2 или OIDC, например Auth0, Okta или Google. | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Оба класса наследуются от `BaseAuthProvider` и подчиняются одному контракту. Метод `authenticate()` выполняется при каждом запросе. Его результат становится значением `request.state.admin_user`, а если он вернул `None`, фреймворк устанавливает `request.state.is_anonymous = True`.

## `AuthProvider`: встроенная страница входа

Используйте этого провайдера, когда вы хотите, чтобы фреймворк отображал и обрабатывал форму входа, а проверку учётных данных выполняли вы. Фреймворк отвечает за шаблон, обработку POST-запроса и перенаправление.

Полный пример:

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

`AuthProvider` реализует три метода. Здесь требуется `SessionMiddleware`, поскольку именно он сохраняет состояние входа пользователя между запросами.

#### `login()`

Этот метод обрабатывает отправку формы. Он получает `username`, `password`, логическое значение `remember_me` и текущий `request`.

* **При успехе:** запишите идентификатор, например ID или имя пользователя, в `request.session`. Затем верните `None`, чтобы фреймворк выполнил перенаправление на параметр `next` или на главную страницу панели, либо верните `Response`, чтобы перенаправить пользователя куда-либо ещё.
* **При ошибке:** вызовите исключение `LoginFailed("message")`, чтобы отобразить сообщение об ошибке над формой, либо `FormValidationError({"username": "..."})`, чтобы пометить конкретное поле как некорректное.

#### `authenticate()`

Этот метод выполняется при *каждом* обращении к защищённому маршруту панели. Он получает объект `request`.

* Прочитайте идентификатор, который вы сохранили в `request.session` во время `login()`.
* Найдите пользователя в вашей базе данных.
* Верните экземпляр `AdminUser`, если пользователь существует и действителен.
* Верните `None`, если пользователь не существует или не вошёл в систему.

#### `logout()`

Этот метод обрабатывает выход из системы. Он получает объект `request`; чтобы отозвать доступ, очистите данные пользователя из `request.session`. Верните `None` для стандартного перенаправления на главную страницу панели, либо верните `Response`, чтобы перенаправить пользователя куда-либо ещё.

## `OAuthProvider`: redirect-процесс OAuth2/OIDC {#oauthprovider-oauth2oidc-redirect-flow}


Используйте `OAuthProvider`, когда вы делегируете аутентификацию внешнему поставщику идентификации, такому как Auth0, Okta, Google или Microsoft Entra ID.

`AuthProvider` работает с формой имени пользователя и пароля внутри панели. `OAuthProvider` вместо этого использует процесс на основе перенаправлений:

1. Перенаправьте пользователя к поставщику идентификации.
2. Поставщик аутентифицирует пользователя.
3. Поставщик перенаправляет пользователя обратно в ваше приложение.
4. Ваше приложение обменивает callback-данные на идентификатор пользователя.
5. Метод `authenticate()` восстанавливает пользователя из сессии.

### Настройка callback URL (обязательно)

Перед реализацией `OAuthProvider` зарегистрируйте callback URL вашего приложения в консоли управления поставщика идентификации. В целях безопасности поставщики OAuth перенаправляют только на заранее одобренные URL.

#### Пример callback URL

```text
https://your-domain.com/admin/oauth/callback
```

#### Локальная разработка

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    Точный адрес callback URL зависит от вашей конфигурации. Он формируется из `route_name`, который вы используете при подключении `Admin`, плюс `callback_path` провайдера.

    В конфигурации по умолчанию используются:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    что даёт следующий callback URL:

    ```text
    /admin/oauth/callback
    ```

    В развёрнутом приложении он принимает вид:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    Если вы измените префикс подключения или путь callback провайдера, URL изменится соответствующим образом, и вам придётся обновить его в конфигурации поставщика OAuth.

### Обязательные методы

`OAuthProvider` использует ту же схему с привязкой к сессии, что и `AuthProvider`, но разделяет вход на два этапа: перенаправление и callback.

#### `redirect_to_provider()`

Этот метод запускает процесс OAuth. Он получает `request` и сгенерированный `callback_url` и должен вернуть `Response`, перенаправляющий браузер пользователя к вашему поставщику идентификации.

#### `handle_callback()`

Этот метод выполняется, когда браузер возвращается от поставщика с кодом авторизации. Он получает `request`. Обменяйте код на access token, получите профиль пользователя и сохраните его идентификатор в `request.session`.

#### `authenticate()`

Как и в случае с `AuthProvider`, этот метод читает всё, что метод `handle_callback()` сохранил в сессии. Верните `AdminUser`, если в сессии содержатся корректные данные пользователя, иначе — `None`.

#### `logout()`

Очистите данные сессии. Чтобы также выйти пользователя из системы поставщика идентификации (OIDC RP-initiated logout), переопределите этот метод и верните `Response` с перенаправлением на end-session endpoint поставщика вместо возврата `None`.

Полный пример:

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

Эта единственная строка — вся интеграция. `Admin` монтирует `AuthMiddleware` провайдера перед каждым маршрутом панели и добавляет маршруты провайдера (вход, выход и callback для `OAuthProvider`) внутрь префикса панели.

## Проверка прав доступа

Аутентификация отвечает на вопрос «Кто это?». Права доступа отвечают на вопрос «Что он может делать?». Права принадлежат view. Доступ на основе ролей состоит из трёх шагов:

1. Создайте подкласс `AdminUser` — обычного dataclass-класса — добавив список `roles`.
2. Возвращайте экземпляр этого подкласса из метода `authenticate()` вашего провайдера, заполняя его данными из вашего хранилища пользователей.
3. Читайте `request.state.admin_user.roles` в permission hook'ах view.

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

Зарегистрируйте `MyAuthProvider`, как и любого другого провайдера: `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. После этого каждый из перечисленных hook'ов получит доступ к `request.state.admin_user.roles`.

Метод `is_accessible()`, доступный в каждом `BaseView`, полностью скрывает view, включая его пункт в боковом меню. Методы `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import` и `can_view_detail` управляют отдельными операциями в `ModelView`. Метод `can_access_field` скрывает конкретные поля, а `is_action_allowed` и `is_row_action_allowed` ограничивают bulk- и row action'ы. Когда row action зависит от самой записи, а не от пользователя — например, нужно скрыть действие `publish` для уже опубликованной статьи — переопределите вместо него метод `is_row_action_allowed_for_obj(request, name, obj)`. Он получает базовый объект строки и при отсутствии переопределения откатывается к `is_row_action_allowed`.

Полную справку по API см. в разделах [Views](views.md) и [Actions](actions.md). Полностью рабочий пример с `can_export`, `can_import` и row action находится в [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Некоторые маршруты остаются публичными даже в закрытой панели администрирования — например, форма самостоятельной регистрации или health check. Добавьте декоратор к endpoint'у, и `AuthMiddleware` пропустит запрос без проверки корректного результата `authenticate()`:

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

И `@route`, и `@login_not_required` лишь помечают функцию атрибутом и возвращают её без изменений, поэтому порядок их наложения не имеет значения.

## `allow_routes`

`allow_routes` предоставляет такое же исключение, но на уровне имени маршрута, а не функции. Используйте его, когда определение endpoint'а принадлежит не вам, или когда вы хотите держать список исключений в одном месте:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

Строка здесь — имя маршрута: либо имя метода, либо значение, переданное в параметре `name=` декоратора `@route`, например `name="register"` выше. `AuthMiddleware` всегда разрешает `"login"` и `"static"` поверх перечисленных вами пользовательских маршрутов.

## `AdminUser`

Всё, что возвращает `authenticate()`, попадает в `request.state.admin_user`. Верхняя панель читает из него два поля:

| Атрибут | Тип | Значение по умолчанию | Описание |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (переводится) | Имя, отображаемое в меню пользователя верхней панели. |
| `photo_url` | `str | None` | `None` | URL аватара. Если не задан, используется иконка-заглушка. |

`AdminUser` — обычный класс с декоратором `@dataclass`, поэтому создание подкласса для хранения ролей, идентификатора tenant'а или любых других данных, необходимых вашим permission hook'ам, является штатным подходом. Приведённый выше пример `MyAdminUser` демонстрирует это на практике.

---

**Что дальше**

* [Security](security.md): CSRF, секретные ключи и то, что фреймворк защищает автоматически.
* [Views](views.md): `can_create`, `can_edit`, `can_delete` и полный список permission hook'ов.
* [Actions](actions.md): `is_action_allowed` и `is_row_action_allowed` для bulk- и row action'ов.
