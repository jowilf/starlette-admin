---
title: Instances Admin multiples
description: Montez plusieurs tableaux de bord admin isolés sur une seule application
  FastAPI pour différents rôles d'utilisateurs ou domaines.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# Instances Admin multiples

Chaque instance `Admin` que vous construisez est une sous-application Starlette autonome. Montez-en autant que nécessaire, chacune avec son propre `base_url`, son propre `route_name`, son fournisseur d'authentification et ses vues.

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

Dans cet exemple, `/staff` affiche une page de connexion adossée à `StaffAuth` et `/root` en affiche une autre adossée à `SuperAdminAuth`. Se connecter à l'un ne donne pas accès à l'autre : chaque `SessionMiddleware` signe son cookie avec son propre `secret_key`, de sorte que chaque instance `Admin` ne lit que les données de session écrites par son propre fournisseur d'authentification.

## `base_url` et `route_name`

`base_url` et `route_name` sont des paramètres du constructeur des classes `Admin` et `BaseAdmin` dans `starlette-admin/base.py`. Leurs valeurs par défaut sont `/admin` et `"admin"` :

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** définit le préfixe de chemin auquel l'admin est monté. Il passe directement dans l'appel interne `app.mount(self.base_url, app=admin_app, name=self.route_name)`, il doit donc être unique pour chaque instance. Dans le cas contraire, un montage masque l'autre.
* **`route_name`** est le nom sous lequel Starlette enregistre le montage. Chaque URL générée par l'admin — pour les listes, les détails, les éditions, les exports et les ressources statiques — provient de `request.url_for(route_name + ":list", ...)`, et chaque template de page lit `request.app.state.ROUTE_NAME` pour obtenir le bon préfixe lors de la construction des liens.

`mount_to` construit une nouvelle sous-application Starlette pour chaque instance admin, si bien que les middlewares, les routes et les variables globales des templates restent isolés. `Admin` n'est pas un singleton à l'échelle du processus : construisez autant d'instances indépendantes que votre application en a besoin.

!!! warning
    Attribuez à chaque `Admin` un `route_name` distinct. Le routeur de Starlette résout `url_for("admin:list", ...)` en correspondant au **nom** du montage ; ainsi, deux admins partageant le même `route_name` laissent l'application parente avec deux montages sous le même nom, et `url_for` résout vers celui que Starlette trouve en premier. Chaque lien interne du deuxième admin — y compris les liens d'édition, les ressources statiques et les endpoints d'export — pointe alors silencieusement vers le `base_url` du premier.

## Partager des vues ou définir des vues distinctes

`add_view` reçoit une instance de vue et la modifie pendant sa configuration. Pour une `BaseModelView`, cette configuration lie des callbacks internes à l'admin auprès duquel elle est enregistrée, notamment la manière dont les champs `HasOne` et `HasMany` résolvent les liens vers les enregistrements associés.

Enregistrez la même **instance** de vue sur deux admins et le second appel `add_view` écrase ces callbacks : les liens de relation sur les pages du premier admin se résolvent alors par rapport aux vues et aux URLs du second.

Pour éviter cela, donnez à chaque admin une nouvelle instance de la **classe** `ModelView`. La classe ne contient aucun état propre à un admin ; seules les instances en ont :

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(
    ModelView(Order)
)  # separate instance of the same class; this is safe
```

Lorsque les deux admins nécessitent des comportements différents, comme des règles de visibilité ou des permissions `can_delete` distinctes, écrivez une sous-classe pour chacun au lieu de modifier une instance partagée à l'exécution :

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

## Et ensuite ?

* **[Authentication](../user-guide/auth.md) :** le contrat complet de `AuthProvider` et `OAuthProvider`.
* **[Extension Points](extension-points.md) :** toutes les autres surfaces enfichables disponibles sur la classe `Admin`.
* **[Quickstart](../getting-started/quickstart.md) :** la configuration mono-admin fondamentale sur laquelle ce guide s'appuie.
