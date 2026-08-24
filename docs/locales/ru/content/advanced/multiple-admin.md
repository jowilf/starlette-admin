---
title: Несколько экземпляров панели администрирования
description: Подключите несколько изолированных дашбордов администрирования к одному
  приложению FastAPI для разных ролей пользователей или доменов.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
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

    [Читать оригинал на английском](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# Несколько экземпляров панели администрирования

Каждый создаваемый вами экземпляр `Admin` — это самодостаточное подприложение Starlette. Подключайте столько экземпляров, сколько нужно, каждый со своими `base_url`, `route_name`, провайдером аутентификации и представлениями.

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

В этом примере `/staff` показывает страницу входа на основе `StaffAuth`, а `/root` — отдельную страницу на основе `SuperAdminAuth`. Вход в одну панель не даёт доступа к другой: каждый `SessionMiddleware` подписывает свой cookie собственным `secret_key`, поэтому каждый экземпляр `Admin` читает только те данные сессии, которые записал его собственный провайдер аутентификации.

## `base_url` и `route_name`

`base_url` и `route_name` — это параметры конструктора классов `Admin` и `BaseAdmin` в файле `starlette_admin/base.py`. По умолчанию они равны `/admin` и `"admin"`:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** задаёт префикс пути, по которому подключается панель администрирования. Он передаётся напрямую во внутренний вызов `app.mount(self.base_url, app=admin_app, name=self.route_name)`, поэтому должен быть уникальным для каждого экземпляра. Иначе одно подключение перекроет другое.
* **`route_name`** — это имя, под которым Starlette регистрирует подключение. Каждый URL, который генерирует панель — для списков, деталей, редактирования, экспорта и статических ресурсов, — строится через `request.url_for(route_name + ":list", ...)`, а каждый шаблон страницы читает `request.app.state.ROUTE_NAME`, чтобы получить правильный префикс для построения ссылок.

Метод `mount_to` создаёт новое подприложение Starlette для каждого экземпляра панели, поэтому middleware, маршруты и глобальные переменные шаблонов остаются изолированными. `Admin` — не синглтон на уровне процесса: создавайте столько независимых экземпляров, сколько нужно вашему приложению.

!!! warning
    Задавайте каждому экземпляру `Admin` уникальное значение `route_name`. Маршрутизатор Starlette разрешает `url_for("admin:list", ...)` по совпадению **имени** подключения, поэтому если две панели используют один `route_name`, родительское приложение получит два подключения с одинаковым именем, и `url_for` разрешится в то из них, которое Starlette найдёт первым. В результате все внутренние ссылки второй панели, включая ссылки на редактирование, статические ресурсы и эндпоинты экспорта, будут молча указывать на `base_url` первой панели.

## Общие представления или отдельные представления

Метод `add_view` принимает экземпляр представления и изменяет его в процессе настройки. Для `BaseModelView` эта настройка привязывает внутренние колбэки к той панели, с которой представление зарегистрировано, включая способ разрешения ссылок на связанные записи полями `HasOne` и `HasMany`.

Если зарегистрировать один и тот же **экземпляр** представления на двух панелях, второй вызов `add_view` перезапишет эти колбэки, и ссылки на связи на страницах первой панели будут разрешаться относительно представлений и URL второй панели.

Чтобы этого избежать, передавайте каждой панели новый экземпляр **класса** `ModelView`. Класс не хранит состояния, специфичного для панели, — его хранят только экземпляры:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

Когда двум панелям нужно разное поведение — например, разные правила видимости или права `can_delete`, — напишите подкласс для каждой вместо изменения общего экземпляра во время выполнения:

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

* **[Аутентификация](../user-guide/auth.md):** полный контракт `AuthProvider` и `OAuthProvider`.
* **[Точки расширения](extension-points.md):** все остальные подключаемые поверхности класса `Admin`.
* **[Быстрый старт](../getting-started/quickstart.md):** базовая настройка с одной панелью, на которой построено это руководство.
