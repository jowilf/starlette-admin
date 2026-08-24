---
title: Mehrere Admin-Instanzen
description: Binden Sie mehrere isolierte Admin-Dashboards für verschiedene Benutzerrollen
  oder Domänen an eine einzige FastAPI-Anwendung an.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# Mehrere Admin-Instanzen

Jede `Admin`-Instanz, die Sie konstruieren, ist eine eigenständige Starlette-Subanwendung. Binden Sie so viele an, wie Sie benötigen, jeweils mit ihrem eigenen `base_url`, `route_name`, Authentifizierungsprovider und ihren Views.

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

In diesem Beispiel zeigt `/staff` eine Anmeldeseite mit `StaffAuth` im Hintergrund und `/root` eine separate Seite, die auf `SuperAdminAuth` basiert. Die Anmeldung bei einer Instanz gewährt keinen Zugriff auf die andere: Jede `SessionMiddleware` signiert ihr Cookie mit ihrem eigenen `secret_key`, sodass jede `Admin`-Instanz nur die Sessiondaten liest, die ihr eigener Authentifizierungsprovider geschrieben hat.

## `base_url` und `route_name`

`base_url` und `route_name` sind Konstruktorparameter der Klassen `Admin` und `BaseAdmin` in `starlette_admin/base.py`. Ihr Defaultwert ist `/admin` bzw. `"admin"`:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** legt das Pfadpräfix fest, unter dem das Admin-Panel eingebunden wird. Es geht direkt in den internen Aufruf `app.mount(self.base_url, app=admin_app, name=self.route_name)` ein und muss daher pro Instanz eindeutig sein. Andernfalls verdeckt ein Mount den anderen.
* **`route_name`** ist der Name, unter dem Starlette den Mount registriert. Jede URL, die das Admin-Panel generiert, für Listen, Details, Bearbeitungen, Exporte und statische Assets, stammt aus `request.url_for(route_name + ":list", ...)`, und jedes Seiten-Template liest `request.app.state.ROUTE_NAME`, um das richtige Präfix für den Linkaufbau zu erhalten.

`mount_to` erstellt für jede Admin-Instanz eine neue Starlette-Subanwendung, sodass Middleware, Routen und Template-Globals isoliert bleiben. `Admin` ist kein prozessweiter Singleton: Konstruieren Sie so viele unabhängige Instanzen, wie Ihre Anwendung benötigt.

!!! warning
    Vergeben Sie jedem `Admin` einen eigenen `route_name`. Der Router von Starlette löst `url_for("admin:list", ...)` durch Abgleich des Mount-**Namens** auf, daher bleiben zwei Admins, die sich einen `route_name` teilen, in der Elternanwendung mit zwei Mounts unter demselben Namen zurück, und `url_for` löst zu dem Mount auf, den Starlette zuerst findet. Jeder interne Link im zweiten Admin, einschließlich Bearbeitungslinks, statischer Assets und Export-Endpoints, zeigt dann stillschweigend auf das `base_url` des ersten Admins.

## Views teilen oder separate Views definieren

`add_view` nimmt eine View-Instanz entgegen und verändert sie während des Setups. Bei einem `BaseModelView` bindet dieses Setup interne Callbacks an das Admin-Panel, bei dem die View registriert wird, einschließlich der Art, wie `HasOne`- und `HasMany`-Felder Links zu verwandten Datensätzen auflösen.

Registrieren Sie dieselbe View-**Instanz** auf zwei Admins, überschreibt der zweite `add_view`-Aufruf diese Callbacks, sodass Beziehungslinks auf den Seiten des ersten Admins gegen die Views und URLs des zweiten Admins aufgelöst werden.

Um dies zu vermeiden, geben Sie jedem Admin eine frische Instanz der `ModelView`-**Klasse**. Die Klasse enthält keinen adminspezifischen Zustand, nur die Instanzen tun dies:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

Wenn beide Admins unterschiedliches Verhalten benötigen, etwa unterschiedliche Sichtbarkeitsregeln oder `can_delete`-Berechtigungen, schreiben Sie stattdessen für jeden eine Subklasse, statt eine gemeinsame Instanz zur Laufzeit zu patchen:

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

## Wie es weitergeht

* **[Authentifizierung](../user-guide/auth.md):** Der vollständige Vertrag von `AuthProvider` und `OAuthProvider`.
* **[Erweiterungspunkte](extension-points.md):** Alle weiteren austauschbaren Schnittstellen, die die Klasse `Admin` bietet.
* **[Quickstart](../getting-started/quickstart.md):** Das grundlegende Setup mit einem einzelnen Admin, auf dem dieser Leitfaden aufbaut.
