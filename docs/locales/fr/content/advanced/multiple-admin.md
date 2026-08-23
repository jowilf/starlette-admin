---
title: Instances d'administration multiples
description: Montez plusieurs tableaux de bord d'administration isolés sur une seule
  application FastAPI pour différents rôles ou domaines d'utilisateurs.
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# Instances d'administration multiples

Chaque instance de `Admin` que vous construisez est une sous-application Starlette autonome. Montez-en autant que nécessaire, chacune avec son propre `base_url`, `route_name`, fournisseur d'authentification et vues.

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

Dans cet exemple, `/staff` affiche une page de connexion gérée par `StaffAuth` et `/root` en affiche une autre, gérée par `SuperAdminAuth`. Se connecter à l'un ne donne pas accès à l'autre : chaque `SessionMiddleware` signe son cookie avec son propre `secret_key`, de sorte que chaque instance de `Admin` ne lit que les données de session écrites par son propre fournisseur d'authentification.

## `base_url` et `route_name`

`base_url` et `route_name` sont des paramètres du constructeur des classes `Admin` et `BaseAdmin` dans `starlette_admin/base.py`. Ils ont pour valeurs par défaut `/admin` et `"admin"` :

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** définit le préfixe de chemin auquel le panneau d'administration est monté. Il est passé directement dans l'appel interne `app.mount(self.base_url, app=admin_app, name=self.route_name)`, il doit donc être unique pour chaque instance. Sinon, un montage masque l'autre.
* **`route_name`** est le nom sous lequel Starlette enregistre le montage. Chaque URL générée par le panneau d'administration, pour les listes, les détails, les modifications, les exportations et les ressources statiques, provient de `request.url_for(route_name + ":list", ...)`, et chaque template de page lit `request.app.state.ROUTE_NAME` pour obtenir le bon préfixe lors de la construction des liens.

`mount_to` construit une sous-application Starlette fraîche pour chaque instance du panneau d'administration : les middleware, les routes et les variables globales de template restent donc isolés. `Admin` n'est pas un singleton à l'échelle du processus : construisez autant d'instances indépendantes que votre application en a besoin.

!!! warning
    Donnez à chaque `Admin` un `route_name` distinct. Le routeur de Starlette résout `url_for("admin:list", ...)` en faisant correspondre le **nom** du montage ; deux panneaux d'administration partageant un même `route_name` laissent donc l'application parente avec deux montages sous le même nom, et `url_for` résout vers celui que Starlette trouve en premier. Tous les liens internes du second panneau d'administration, y compris les liens de modification, les ressources statiques et les endpoints d'exportation, pointent alors silencieusement vers le `base_url` du premier.

## Partager des vues ou définir des vues distinctes

`add_view` prend une instance de vue et la modifie pendant la configuration. Pour une `BaseModelView`, cette configuration lie des callbacks internes au panneau d'administration auprès duquel elle est enregistrée, notamment la manière dont les champs `HasOne` et `HasMany` résolvent les liens vers les enregistrements liés.

Si vous enregistrez la même **instance** de vue sur deux panneaux d'administration, le second appel à `add_view` écrase ces callbacks : les liens de relation sur les pages du premier panneau sont alors résolus par rapport aux vues et aux URLs du second.

Pour éviter cela, donnez à chaque panneau d'administration une nouvelle instance de la **classe** `ModelView`. La classe ne contient aucun état propre à un panneau d'administration ; seules les instances en contiennent :

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(ModelView(Order))  # separate instance of the same class; this is safe

```

Lorsque les deux panneaux d'administration nécessitent des comportements différents, comme des règles de visibilité différentes ou des permissions `can_delete`, écrivez une sous-classe pour chacun plutôt que de modifier une instance partagée à l'exécution :

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
* **[Quickstart](../getting-started/quickstart.md) :** la configuration de base avec un seul panneau d'administration sur laquelle ce guide s'appuie.
