---
title: Authentification
description: Implémentez l'authentification dans starlette-admin à l'aide de AuthProvider
  ou intégrez OAuth pour sécuriser votre tableau de bord.
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# Authentification

Vous protégez l'interface d'administration en implémentant une seule méthode :

```python
async def authenticate(request) -> AdminUser | None
```

Chaque requête protégée vers le panneau d'administration passe par cette méthode. Lorsqu'elle renvoie un `AdminUser`, la requête est authentifiée. Lorsqu'elle renvoie `None`, la requête n'est pas authentifiée, et le flux de connexion ou OAuth que vous avez configuré prend le relais.

En cas de succès, l'`AdminUser` renvoyé est disponible dans :

```python
request.state.admin_user
```

En cas d'échec, la requête est marquée comme anonyme :

```python
request.state.is_anonymous = True
```

Les routes publiques et partiellement protégées peuvent alors distinguer les requêtes authentifiées des requêtes non authentifiées sans déclencher un flux de connexion.


## Choisir un fournisseur d'authentification

| Fournisseur | Quand l'utiliser | Ce que vous implémentez |
| --- | --- | --- |
| `AuthProvider` | Vous voulez la page de connexion intégrée et vous vérifiez vous-même les identifiants. | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | Vous voulez un flux de redirection OAuth2 ou OIDC, tel qu'Auth0, Okta ou Google. | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

Les deux héritent de `BaseAuthProvider` et partagent le même contrat. `authenticate()` s'exécute à chaque requête. Ce qu'il renvoie devient `request.state.admin_user`, et lorsqu'il renvoie `None`, le framework définit `request.state.is_anonymous = True`.

## `AuthProvider` : page de connexion intégrée

Utilisez ce fournisseur lorsque vous voulez que le framework affiche et gère le formulaire de connexion pendant que vous vérifiez les identifiants. Le framework possède le template, le traitement du POST et la redirection.

Voici un exemple complet :

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

### Méthodes requises

Un `AuthProvider` implémente trois méthodes. `SessionMiddleware` est requis ici, car il conserve l'état de connexion de l'utilisateur entre les requêtes.

#### `login()`

Cette méthode traite la soumission du formulaire. Elle reçoit le `username`, le `password`, un booléen `remember_me` et la `request` actuelle.

* **En cas de succès :** écrivez un identifiant, tel qu'un ID utilisateur ou un nom d'utilisateur, dans `request.session`. Renvoyez ensuite `None` pour laisser le framework rediriger vers `next` ou l'index de l'admin, ou renvoyez une `Response` pour rediriger ailleurs.
* **En cas d'échec :** levez `LoginFailed("message")` pour afficher une erreur au-dessus du formulaire, ou levez `FormValidationError({"username": "..."})` pour marquer un champ spécifique comme invalide.

#### `authenticate()`

Cette méthode s'exécute à *chaque* requête vers une route admin protégée. Elle reçoit l'objet `request`.

* Lisez l'identifiant que vous avez enregistré dans `request.session` pendant `login()`.
* Recherchez l'utilisateur dans votre base de données.
* Renvoyez une instance de `AdminUser` lorsque l'utilisateur existe et est valide.
* Renvoyez `None` lorsque l'utilisateur n'existe pas ou n'est pas connecté.

#### `logout()`

Cette méthode gère la déconnexion. Elle reçoit l'objet `request`, et vous effacez les données de l'utilisateur de `request.session` pour révoquer son accès. Renvoyez `None` pour la redirection par défaut vers l'index de l'admin, ou renvoyez une `Response` pour rediriger ailleurs.

## `OAuthProvider` : flux de redirection OAuth2/OIDC


Utilisez `OAuthProvider` lorsque vous déléguez l'authentification à un fournisseur d'identité externe tel qu'Auth0, Okta, Google ou Microsoft Entra ID.

`AuthProvider` gère un formulaire avec nom d'utilisateur et mot de passe à l'intérieur de l'admin. `OAuthProvider` utilise plutôt un flux basé sur une redirection :

1. Redirigez l'utilisateur vers le fournisseur d'identité.
2. Le fournisseur authentifie l'utilisateur.
3. Le fournisseur redirige vers votre application.
4. Votre application échange le callback contre l'identité de l'utilisateur.
5. `authenticate()` restaure l'utilisateur depuis la session.

### Configuration de l'URL de callback (obligatoire)

Avant d'implémenter `OAuthProvider`, enregistrez l'URL de callback de votre application dans le tableau de bord de votre fournisseur d'identité. Pour des raisons de sécurité, les fournisseurs OAuth ne redirigent que vers des URL préalablement approuvées.

#### Exemple d'URL de callback

```text
https://your-domain.com/admin/oauth/callback
```

#### Développement local

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    Votre URL de callback exacte dépend de votre configuration. Elle est construite à partir du `route_name` que vous utilisez lorsque vous montez `Admin`, plus le `callback_path` du fournisseur.

    La configuration par défaut utilise :

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    ce qui produit cette URL de callback :

    ```text
    /admin/oauth/callback
    ```

    Une fois déployée, elle devient :

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    Si vous changez le préfixe de montage ou le chemin de callback du fournisseur, l'URL change en conséquence, et vous devez la mettre à jour dans la configuration de votre fournisseur OAuth.

### Méthodes requises

Un `OAuthProvider` utilise le même modèle basé sur la session que `AuthProvider`, mais il divise la connexion en une redirection et un callback.

#### `redirect_to_provider()`

Cette méthode démarre le flux OAuth. Elle reçoit la `request` et une `callback_url` générée, et elle doit renvoyer une `Response` qui redirige le navigateur de l'utilisateur vers votre fournisseur d'identité.

#### `handle_callback()`

Cette méthode s'exécute lorsque le navigateur revient du fournisseur avec un code d'autorisation. Elle reçoit la `request`. Échangez le code contre un token d'accès, récupérez le profil de l'utilisateur et stockez son identité dans `request.session`.

#### `authenticate()`

Comme avec `AuthProvider`, cette méthode relit tout ce que `handle_callback()` a stocké dans la session. Renvoyez un `AdminUser` lorsque la session contient des données utilisateur valides, ou `None` dans le cas contraire.

#### `logout()`

Effacez les données de la session. Pour déconnecter également l'utilisateur du fournisseur d'identité (déconnexion RP-initiée en OIDC), redéfinissez cette méthode et renvoyez une `Response` de redirection pointant vers l'endpoint de fin de session du fournisseur au lieu de renvoyer `None`.

Voici un exemple complet :

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

## Enregistrer le fournisseur

Après avoir implémenté un fournisseur d'authentification, attachez-le à l'instance de `Admin`.

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

Cette seule ligne constitue toute l'intégration. `Admin` monte l'`AuthMiddleware` du fournisseur devant chaque route admin et ajoute ses routes (connexion, déconnexion et le callback pour `OAuthProvider`) à l'intérieur du préfixe admin.

## Vérifications des permissions

L'authentification répond à la question « Qui est cet utilisateur ? ». Les permissions répondent à la question « Que peut-il faire ? ». Les permissions appartiennent à la vue. Un contrôle d'accès basé sur les rôles se fait en trois étapes :

1. Créez une sous-classe de `AdminUser`, une simple dataclass, pour ajouter une liste `roles`.
2. Renvoyez cette sous-classe depuis la méthode `authenticate()` de votre fournisseur, remplie à partir de votre stockage d'utilisateurs.
3. Lisez `request.state.admin_user.roles` dans les hooks de permission de la vue.

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

Enregistrez `MyAuthProvider` comme n'importe quel autre fournisseur, avec `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`. Chaque hook ci-dessus a alors accès à `request.state.admin_user.roles`.

`is_accessible()`, disponible sur chaque `BaseView`, masque la vue entière, y compris son entrée dans la barre latérale. `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import` et `can_view_detail` gèrent l'accès aux opérations individuelles sur une `ModelView`. `can_access_field` masque des champs spécifiques, et `is_action_allowed` et `is_row_action_allowed` restreignent les actions groupées et les actions de ligne. Lorsqu'une action de ligne dépend de l'enregistrement plutôt que de l'utilisateur, par exemple pour masquer `publish` sur un article déjà publié, redéfinissez plutôt `is_row_action_allowed_for_obj(request, name, obj)`. Elle reçoit l'objet sous-jacent de la ligne et retombe sur `is_row_action_allowed`.

Pour la référence complète de l'API, consultez [Vues](views.md) et [Actions](actions.md). Une version fonctionnelle complète avec `can_export`, `can_import` et une action de ligne est disponible dans [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth).

## `@login_not_required`

Certaines routes restent publiques même dans un panneau d'administration verrouillé, par exemple un formulaire d'inscription en libre-service ou un health check. Décorez l'endpoint, et `AuthMiddleware` laisse passer la requête sans vérifier un résultat valide de `authenticate()` :

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

`@route` et `@login_not_required` marquent tous deux la fonction avec un attribut et la renvoient inchangée ; l'ordre dans lequel vous les empilez n'a donc pas d'importance.

## `allow_routes`

`allow_routes` offre le même contournement au niveau du nom de route plutôt qu'au niveau de la fonction. Utilisez-le lorsque vous ne contrôlez pas la définition de l'endpoint, ou lorsque vous voulez centraliser la liste des routes autorisées à un seul endroit :

```python
provider = MyAuthProvider(allow_routes=["register"])
```

La chaîne correspond au nom de la route : soit le nom de la méthode, soit la valeur passée au paramètre `name=` dans `@route`, comme `name="register"` ci-dessus. `AuthMiddleware` autorise toujours `"login"` et `"static"`, en plus des routes personnalisées que vous listez.

## `AdminUser`

Tout ce que renvoie `authenticate()` remplit `request.state.admin_user`. La barre supérieure lit deux champs de cet objet :

| Attribut | Type | Valeur par défaut | Description |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (traduisible) | Le nom affiché dans le menu utilisateur de la barre supérieure. |
| `photo_url` | `str | None` | `None` | L'URL de l'image d'avatar. Retombe sur une icône de substitution lorsqu'elle n'est pas définie. |

`AdminUser` est une simple `@dataclass`, donc créer une sous-classe pour transporter des rôles, un ID de tenant ou tout autre élément dont vos hooks de permission ont besoin est le modèle prévu. L'exemple `MyAdminUser` ci-dessus le montre en pratique.

---

**Pour aller plus loin**

* [Sécurité](security.md) : CSRF, clés secrètes et protections automatiques du framework.
* [Vues](views.md) : `can_create`, `can_edit`, `can_delete` et la liste complète des hooks de permission.
* [Actions](actions.md) : `is_action_allowed` et `is_row_action_allowed` pour les actions groupées et les actions de ligne.
