---
title: Несколько экземпляров Admin
description: Подключите несколько изолированных admin-панелей к одному приложению
  FastAPI для разных ролей пользователей или доменов.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# Несколько экземпляров Admin

Каждый создаваемый вами экземпляр `Admin` представляет собой самодостаточную sub-application Starlette. Подключайте столько экземпляров, сколько требуется: каждый со своим `base_url`, `route_name`, провайдером аутентификации и набором views.

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette_admin.auth import AdminUser, AuthProvider, LoginFailed
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Order, Post, User

engine = create_engine("sqlite:///app.sqlite")
app = Starlette()

STAFF = {"staff": "staffpass"}
SUPERADMINS = {"root": "rootpass"}


class StaffAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if STAFF.get(username) == password:
            request.session["user"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("user")
        return AdminUser(username=username) if username in STAFF else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


class SuperAdminAuth(AuthProvider):
    async def login(
        self, username: str, password: str, remember_me: bool, request: Request
    ) -> None:
        if SUPERADMINS.get(username) == password:
            request.session["user"] = username
            return
        raise LoginFailed("Invalid username or password")

    async def authenticate(self, request: Request) -> AdminUser | None:
        username = request.session.get("user")
        return AdminUser(username=username) if username in SUPERADMINS else None

    async def logout(self, request: Request) -> None:
        request.session.clear()


staff_admin = Admin(
    engine,
    title="Staff Admin",
    base_url="/staff",
    route_name="staff_admin",
    auth_provider=StaffAuth(),
    secret_key="staff-secret-change-me",
    middlewares=[Middleware(SessionMiddleware, secret_key="staff-secret-change-me")],
)
staff_admin.add_view(ModelView(Order))
staff_admin.add_view(ModelView(Post))
staff_admin.mount_to(app)

root_admin = Admin(
    engine,
    title="Super Admin",
    base_url="/root",
    route_name="root_admin",
    auth_provider=SuperAdminAuth(),
    secret_key="root-secret-change-me",
    middlewares=[Middleware(SessionMiddleware, secret_key="root-secret-change-me")],
)
root_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(User))
root_admin.mount_to(app)

```

В этом примере `/staff` отображает страницу входа, работающую на основе `StaffAuth`, а `/root` — отдельную страницу, основанную на `SuperAdminAuth`. Вход в одну панель не даёт доступа к другой: каждый `SessionMiddleware` подписывает свой cookie собственным `secret_key`, поэтому каждый экземпляр `Admin` читает только те данные сессии, которые записал его собственный провайдер аутентификации.

## `base_url` и `route_name`

Параметры `base_url` и `route_name` являются параметрами конструктора классов `Admin` и `BaseAdmin` в файле `starlette-admin/base.py`. По умолчанию они принимают значения `/admin` и `"admin"`:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** задаёт префикс пути, по которому монтируется admin-панель. Он передаётся напрямую во внутренний вызов `app.mount(self.base_url, app=admin_app, name=self.route_name)`, поэтому должен быть уникальным для каждого экземпляра. В противном случае одно подключение перекроет другое.
* **`route_name`** — это имя, под которым Starlette регистрирует подключение. Все URL, генерируемые admin-панелью — для списков, страниц деталей, редактирования, экспорта и статических ресурсов, — формируются через `request.url_for(route_name + ":list", ...)`, а каждый шаблон страницы читает `request.app.state.ROUTE_NAME`, чтобы получить правильный префикс для построения ссылок.

Метод `mount_to` создаёт новое Starlette sub-application для каждого экземпляра admin-панели, благодаря чему middleware, маршруты и глобальные переменные шаблонов остаются изолированными. Класс `Admin` не является синглтоном в рамках процесса: создавайте столько независимых экземпляров, сколько требуется вашему приложению.

!!! warning
    Присваивайте каждому `Admin` уникальный `route_name`. Роутер Starlette разрешает вызов `url_for("admin:list", ...)` путём сопоставления **имени** подключения, поэтому два экземпляра с одинаковым `route_name` оставят родительское приложение с двумя подключениями под одним именем, и `url_for` разрешится в то из них, которое Starlette сопоставит первым. В результате все внутренние ссылки второго экземпляра, включая ссылки редактирования, статические ресурсы и endpoint'ы экспорта, будут молча указывать на `base_url` первого экземпляра.

## Совместное использование views против отдельных views

Метод `add_view` принимает экземпляр view и изменяет его в процессе настройки. Для `BaseModelView` эта настройка привязывает внутренние callback'и к той admin-панели, с которой view зарегистрирован, включая способ разрешения ссылок на связанные записи полями `HasOne` и `HasMany`.

Если зарегистрировать один и тот же **экземпляр** view на двух admin-панелях, второй вызов `add_view` перезапишет эти callback'и, вследствие чего ссылки на связанные записи на страницах первой панели будут разрешаться относительно views и URL второй панели.

Чтобы избежать этого, предоставляйте каждой admin-панели новый экземпляр **класса** `ModelView`. Класс не содержит состояния, специфичного для конкретной admin-панели, — таким состоянием обладают только экземпляры:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

Когда двум admin-панелям требуется различное поведение — например, разные правила видимости или права `can_delete`, — напишите отдельный subclass для каждой вместо изменения общего экземпляра во время выполнения:

```python
class StaffOrderView(ModelView):
    fields_default_sort = ["-created_at"]

    def can_delete(self, request: Request) -> bool:
        return False


class RootOrderView(ModelView):
    fields_default_sort = ["-created_at"]


staff_admin.add_view(StaffOrderView(Order))
root_admin.add_view(RootOrderView(Order))

```

---

## Что дальше

* **[Аутентификация](../user-guide/auth.md):** Полное описание контракта `AuthProvider` и `OAuthProvider`.
* **[Точки расширения](extension-points.md):** Все остальные подключаемые поверхности, доступные в классе `Admin`.
* **[Быстрый старт](../getting-started/quickstart.md):** Базовая настройка с одной admin-панелью, на которой строится это руководство.
