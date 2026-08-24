---
title: Authentifizierung
description: Implementieren Sie die Authentifizierung in starlette-admin mit AuthProvider
  oder integrieren Sie OAuth, um Ihr Dashboard abzusichern.
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# Authentifizierung

Sie schützen das Admin-Interface, indem Sie eine einzige Methode implementieren:

```python
async def authenticate(request) -> AdminUser | None
```

Jeder geschützte Admin-Request durchläuft diese Methode. Wenn sie einen `AdminUser` zurückgibt, ist der Request authentifiziert. Wenn sie `None` zurückgibt, ist der Request nicht authentifiziert, und der von Ihnen konfigurierte Anmelde- oder OAuth-Ablauf übernimmt.

Bei Erfolg landet der zurückgegebene `AdminUser` auf:

```python
request.state.admin_user
```

Bei einem Fehlschlag wird der Request als anonym markiert:

```python
request.state.is_anonymous = True
```

Öffentliche und teilweise geschützte Routen können dann authentifizierte und nicht authentifizierte Requests unterscheiden, ohne einen Anmeldevorgang zu starten.


## Einen Authentifizierungsanbieter auswählen

| Anbieter | Wann Sie ihn verwenden | Was Sie implementieren |
| --- | --- | --- |
| `AuthProvider` | Sie möchten die integrierte Login-Seite und prüfen die Zugangsdaten selbst. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | Sie möchten einen OAuth2- oder OIDC-Redirect-Flow, z. B. mit Auth0, Okta oder Google. | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Beide erben von `BaseAuthProvider` und teilen sich denselben Vertrag. `authenticate()` läuft bei jedem Request. Was sie zurückgibt, wird zu `request.state.admin_user`, und wenn sie `None` zurückgibt, setzt das Framework `request.state.is_anonymous = True`.

## `AuthProvider`: integrierte Login-Seite

Verwenden Sie diesen Anbieter, wenn das Framework das Anmeldeformular rendern und verarbeiten soll, während Sie die Zugangsdaten überprüfen. Das Framework besitzt das Template, die POST-Verarbeitung und den Redirect.

Hier ein vollständiges Beispiel:

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

### Erforderliche Methoden

Ein `AuthProvider` implementiert drei Methoden. `SessionMiddleware` ist hier erforderlich, weil sie den angemeldeten Zustand des Benutzers zwischen Requests speichert.

#### `login()`

Diese Methode verarbeitet das Absenden des Formulars. Sie erhält den `username`, das `password`, einen `remember_me`-Boolean und den aktuellen `request`.

* **Bei Erfolg:** Schreiben Sie einen Identifikator, z. B. eine Benutzer-ID oder einen Benutzernamen, in `request.session`. Geben Sie dann `None` zurück, damit das Framework zu `next` oder zum Admin-Index weiterleitet, oder geben Sie eine `Response` zurück, um woandershin umzuleiten.
* **Bei einem Fehlschlag:** Lösen Sie `LoginFailed("message")` aus, um einen Fehler über dem Formular anzuzeigen, oder lösen Sie `FormValidationError({"username": "..."})` aus, um ein bestimmtes Feld als ungültig zu markieren.

#### `authenticate()`

Diese Methode läuft bei *jedem* Request an einer geschützten Admin-Route. Sie erhält das `request`-Objekt.

* Lesen Sie den Identifikator, den Sie während `login()` in `request.session` gespeichert haben.
* Schlagen Sie den Benutzer in Ihrer Datenbank nach.
* Geben Sie eine `AdminUser`-Instanz zurück, wenn der Benutzer existiert und gültig ist.
* Geben Sie `None` zurück, wenn der Benutzer nicht existiert oder nicht angemeldet ist.

#### `logout()`

Diese Methode verarbeitet den Logout. Sie erhält das `request`-Objekt, und Sie löschen die Daten des Benutzers aus `request.session`, um den Zugriff zu widerrufen. Geben Sie `None` für die Standardweiterleitung zum Admin-Index zurück, oder geben Sie eine `Response` zurück, um woandershin umzuleiten.

## `OAuthProvider`: OAuth2/OIDC-Redirect-Flow


Verwenden Sie `OAuthProvider`, wenn Sie die Authentifizierung an einen externen Identity Provider wie Auth0, Okta, Google oder Microsoft Entra ID delegieren.

`AuthProvider` verarbeitet ein Formular mit Benutzername und Passwort innerhalb des Admin-Bereichs. `OAuthProvider` verwendet stattdessen einen redirect-basierten Ablauf:

1. Leiten Sie den Benutzer zum Identity Provider weiter.
2. Der Provider authentifiziert den Benutzer.
3. Der Provider leitet zurück zu Ihrer Anwendung.
4. Ihre Anwendung tauscht den Callback gegen die Identität des Benutzers ein.
5. `authenticate()` stellt den Benutzer aus der Session wieder her.

### Die Callback-URL einrichten (erforderlich)

Bevor Sie `OAuthProvider` implementieren, registrieren Sie die Callback-URL Ihrer Anwendung im Dashboard Ihres Identity Providers. Aus Sicherheitsgründen leiten OAuth-Provider nur zu vorab genehmigten URLs weiter.

#### Beispiel für eine Callback-URL

```text
https://your-domain.com/admin/oauth/callback
```

#### Lokale Entwicklung

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    Ihre exakte Callback-URL hängt von Ihrer Konfiguration ab. Sie setzt sich zusammen aus dem `route_name`, den Sie beim Mounten von `Admin` verwenden, und dem `callback_path` des Providers.

    Das Standard-Setup verwendet:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    was diese Callback-URL ergibt:

    ```text
    /admin/oauth/callback
    ```

    Nach dem Deployment wird daraus:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    Wenn Sie das Mount-Präfix oder den Callback-Pfad des Providers ändern, ändert sich auch die URL, und Sie müssen sie in Ihrer OAuth-Provider-Konfiguration aktualisieren.

### Erforderliche Methoden

Ein `OAuthProvider` verwendet dasselbe session-basierte Muster wie `AuthProvider`, teilt die Anmeldung aber in einen Redirect und einen Callback auf.

#### `redirect_to_provider()`

Diese Methode startet den OAuth-Ablauf. Sie erhält den `request` und eine generierte `callback_url` und muss eine `Response` zurückgeben, die den Browser des Benutzers zu Ihrem Identity Provider weiterleitet.

#### `handle_callback()`

Diese Methode läuft, wenn der Browser mit einem Authorization Code vom Provider zurückkommt. Sie erhält den `request`. Tauschen Sie den Code gegen ein Access Token ein, rufen Sie das Profil des Benutzers ab und speichern Sie seine Identität in `request.session`.

#### `authenticate()`

Wie bei `AuthProvider` liest diese Methode alles zurück, was `handle_callback()` in der Session gespeichert hat. Geben Sie einen `AdminUser` zurück, wenn die Session gültige Benutzerdaten enthält, andernfalls `None`.

#### `logout()`

Löschen Sie die Session-Daten. Um den Benutzer auch beim Identity Provider abzumelden (OIDC RP-initiiertes Logout), überschreiben Sie diese Methode und geben Sie stattdessen eine Redirect-`Response` zurück, die auf den End-Session-Endpoint des Providers zeigt, statt `None` zurückzugeben.

Hier ein vollständiges Beispiel:

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

## Den Anbieter registrieren

Nachdem Sie einen Authentifizierungsanbieter implementiert haben, hängen Sie ihn an die `Admin`-Instanz an.

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

Diese eine Zeile ist die gesamte Integration. `Admin` mounted die `AuthMiddleware` des Providers vor jede Admin-Route und fügt die Routen des Providers (Anmeldung, Abmeldung und den Callback für `OAuthProvider`) innerhalb des Admin-Präfixes hinzu.

## Berechtigungsprüfungen

Die Authentifizierung beantwortet die Frage „Wer ist das?“. Die Berechtigungen beantworten die Frage „Was darf diese Person?“. Berechtigungen gehören zur View. Der rollenbasierte Zugriff besteht aus drei Schritten:

1. Erstellen Sie eine Unterklasse von `AdminUser`, einer einfachen Dataclass, um eine `roles`-Liste hinzuzufügen.
2. Geben Sie diese Unterklasse aus der `authenticate()`-Methode Ihres Providers zurück, gefüllt aus Ihrem Benutzerspeicher.
3. Lesen Sie `request.state.admin_user.roles` in den Permission-Hooks der View.

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

Registrieren Sie `MyAuthProvider` wie jeden anderen Anbieter, mit `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. Jeder Hook oben hat dann Zugriff auf `request.state.admin_user.roles`.

`is_accessible()`, verfügbar auf jeder `BaseView`, blendet die gesamte View aus, einschließlich ihres Sidebar-Eintrags. `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import` und `can_view_detail` schalten einzelne Operationen auf einer `ModelView` frei. `can_access_field` blendet bestimmte Felder aus, und `is_action_allowed` sowie `is_row_action_allowed` beschränken Massen- und Zeilenaktionen. Wenn eine Zeilenaktion vom Datensatz statt vom Benutzer abhängt, z. B. das Ausblenden von `publish` bei einem bereits veröffentlichten Artikel, überschreiben Sie stattdessen `is_row_action_allowed_for_obj(request, name, obj)`. Sie erhält das zugrunde liegende Objekt der Zeile und fällt auf `is_row_action_allowed` zurück.

Für die vollständige API-Referenz siehe [Views](views.md) und [Actions](actions.md). Eine vollständig funktionierende Version mit `can_export`, `can_import` und einer Zeilenaktion finden Sie unter [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Manche Routen bleiben öffentlich, selbst in einem sonst abgesicherten Admin-Panel, z. B. ein Selfservice-Registrierungsformular oder ein Health Check. Dekorieren Sie den Endpoint, und `AuthMiddleware` lässt den Request durch, ohne ein gültiges Ergebnis von `authenticate()` zu prüfen:

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

`@route` und `@login_not_required` versehen die Funktion beide mit einem Attribut und geben sie unverändert zurück, daher spielt die Reihenfolge, in der Sie sie stapeln, keine Rolle.

## `allow_routes`

`allow_routes` bietet Ihnen dieselbe Umgehung auf Ebene des Routennamens statt auf Ebene der Funktion. Verwenden Sie es, wenn Sie die Endpoint-Definition nicht selbst besitzen oder wenn Sie die Liste der Umgehungen an einem Ort sammeln möchten:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

Der String ist der Name der Route: entweder der Name der Methode oder der Wert, den Sie an den Parameter `name=` in `@route` übergeben haben, wie oben `name="register"`. `AuthMiddleware` erlaubt immer `"login"` und `"static"`, zusätzlich zu den benutzerdefinierten Routen, die Sie auflisten.

## `AdminUser`

Was auch immer `authenticate()` zurückgibt, füllt `request.state.admin_user`. Die obere Leiste liest daraus zwei Felder:

| Attribut | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (übersetzbar) | Der Name, der im Benutzer-Menü der oberen Leiste angezeigt wird. |
| `photo_url` | `str | None` | `None` | Die URL des Avatarbildes. Fällt auf ein Platzhalter-Symbol zurück, wenn nicht gesetzt. |

`AdminUser` ist eine einfache `@dataclass`, daher ist das Erstellen einer Unterklasse, um Rollen, eine Tenant-ID oder alles andere, was Ihre Permission-Hooks benötigen, mitzuführen, das vorgesehene Muster. Das `MyAdminUser`-Beispiel oben zeigt dies in der Praxis.

---

**Wie es weitergeht**

* [Security](security.md): CSRF, Secret Keys und was das Framework automatisch schützt.
* [Views](views.md): `can_create`, `can_edit`, `can_delete` und die vollständige Liste der Permission-Hooks.
* [Actions](actions.md): `is_action_allowed` und `is_row_action_allowed` für Massen- und Zeilenaktionen.
