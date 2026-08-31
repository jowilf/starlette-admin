---
title: Mehrere Admin-Instanzen
description: Binden Sie mehrere isolierte Admin-Dashboards in eine einzige FastAPI-Anwendung
  ein – für verschiedene Benutzerrollen oder Domänen.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
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

Jede `Admin`-Instanz, die Sie konstruieren, ist eine eigenständige Starlette-Subanwendung. Binden Sie so viele ein, wie Sie benötigen – jede mit ihrer eigenen `base_url`, ihrem eigenen `route_name`, ihrem eigenen Authentifizierungsprovider und ihren eigenen Views.

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

In diesem Beispiel zeigt `/staff` eine Anmeldeseite, die von `StaffAuth` bereitgestellt wird, während `/root` eine separate Seite mit `SuperAdminAuth` anbietet. Die Anmeldung bei dem einen gewährt keinen Zugriff auf den anderen: Jede `SessionMiddleware` signiert ihr Cookie mit ihrem eigenen `secret_key`, sodass jede `Admin`-Instanz ausschließlich die Session-Daten liest, die ihr eigener Authentifizierungsprovider geschrieben hat.

## `base_url` und `route_name`

`base_url` und `route_name` sind Konstruktorparameter der Klassen `Admin` und `BaseAdmin` in `starlette_admin/base.py`. Ihre Standardwerte sind `/admin` und `"admin"`:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** legt das Pfadpräfix fest, unter dem die Admin-Oberfläche eingebunden wird. Es geht direkt in den internen Aufruf `app.mount(self.base_url, app=admin_app, name=self.route_name)` ein und muss daher pro Instanz eindeutig sein. Andernfalls verdeckt eine Einbindung die andere.
* **`route_name`** ist der Name, unter dem Starlette die Einbindung registriert. Jede vom Admin generierte URL – für Listen, Details, Bearbeitungen, Exporte und statische Assets – entsteht über `request.url_for(route_name + ":list", ...)`, und jedes Seiten-Template liest `request.app.state.ROUTE_NAME`, um das richtige Präfix für die Link-Erzeugung zu erhalten.

`mount_to` erzeugt für jede Admin-Instanz eine neue Starlette-Subanwendung, sodass Middleware, Routen und Template-Globals isoliert bleiben. `Admin` ist kein prozessweiter Singleton: Konstruieren Sie so viele unabhängige Instanzen, wie Ihre Anwendung benötigt.

!!! warning
    Vergeben Sie jeder `Admin`-Instanz einen eigenen `route_name`. Der Router von Starlette löst `url_for("admin:list", ...)` durch Abgleich des Mount-**Namens** auf. Teilen sich zwei Admins denselben `route_name`, enthält die Parent-Anwendung zwei Mounts unter demselben Namen, und `url_for` liefert denjenigen zurück, den Starlette zuerst findet. Dadurch zeigen sämtliche internen Links des zweiten Admins – darunter Edit-Links, statische Assets und Export-Endpoints – stillschweigend auf die `base_url` des ersten Admins.

## Geteilte Views vs. separate Views

`add_view` nimmt eine View-Instanz entgegen und verändert sie während des Setups. Bei einem `BaseModelView` bindet dieses Setup interne Callbacks an den Admin, bei dem die View registriert ist – einschließlich der Art und Weise, wie `HasOne`- und `HasMany`-Felder Links zu verwandten Datensätzen auflösen.

Registrieren Sie dieselbe View-**Instanz** auf zwei Admins, überschreibt der zweite `add_view`-Aufruf diese Callbacks. Die Relationslinks auf den Seiten des ersten Admins werden dann gegen die Views und URLs des zweiten Admins aufgelöst.

Um dies zu vermeiden, geben Sie jedem Admin eine frische Instanz der `ModelView`-**Klasse**. Die Klasse selbst enthält keinen admin-spezifischen Zustand – nur die Instanzen tun dies:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(
    ModelView(Order)
)  # separate instance of the same class; this is safe
```

Wenn die beiden Admins unterschiedliches Verhalten benötigen – etwa unterschiedliche Sichtbarkeitsregeln oder `can_delete`-Berechtigungen – schreiben Sie für jeden eine eigene Subklasse, statt eine geteilte Instanz zur Laufzeit zu patchen:

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
* **[Erweiterungspunkte](extension-points.md):** Alle weiteren pluggable Oberflächen der `Admin`-Klasse.
* **[Quickstart](../getting-started/quickstart.md):** Das grundlegende Setup mit einem einzelnen Admin, auf dem dieser Leitfaden aufbaut.
