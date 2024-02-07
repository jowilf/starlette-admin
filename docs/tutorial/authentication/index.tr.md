# Kimlik Doğrulama ve Yetkilendirme

Yönetici arayüzünüzü istenmeyen kullanıcılardan korumak için [AuthProvider][starlette_admin.auth.AuthProvider] sınıfını genişleterek bir `Kimlik Doğrulama Sağlayıcısı` oluşturabilir ve admin uygulamanızı tanımlarken `auth_provider` özelliğine atayabilirsiniz.

## Kullanıcı Adı ve Şifre ile Kimlik Koğrulama

[AuthProvider][starlette_admin.auth.AuthProvider] varsayılan olarak `username` ve `password` alanları içeren bir giriş formu sağlar. Bu kimlik doğrulama yöntemini tam olarak desteklemek için, özel `Kimlik Doğrulama Sağlayıcı`nızda aşağıdaki yöntemleri uygulamanız gerekir:

* [is_authenticated][starlette_admin.auth.BaseAuthProvider.is_authenticated]: Bu metod, gelen her isteği doğrulamak için çağrılacaktır.
* [get_admin_user][starlette_admin.auth.BaseAuthProvider.get_admin_user]: Bağlı olan kullanıcı `adı` ve/veya `profil` bilgisini döndürür.
* [get_admin_config][starlette_admin.auth.BaseAuthProvider.get_admin_config]: Bağlı olan kullanıcıya göre veya başka koşullara göre `logo_url` veya `app_title` bilgisini döndürür.
* [login][starlette_admin.auth.AuthProvider.login]: kullanıcı kimlik bilgilerini doğrulamak için çağrılacaktır.
* [logout][starlette_admin.auth.AuthProvider.logout]: çıkış yapmak için çağrılacaktır (oturumları, çerezleri temizleme, ...)

```python
from starlette.requests import Request
from starlette.responses import Response
from starlette_admin.auth import AdminUser, AuthProvider
from starlette_admin.exceptions import FormValidationError, LoginFailed

users = {
    "admin": {
        "name": "Admin",
        "avatar": "admin.png",
        "company_logo_url": "admin.png",
        "roles": ["read", "create", "edit", "delete", "action_make_published"],
    },
    "johndoe": {
        "name": "John Doe",
        "avatar": None, # Kullanıcı avatarı isteğe bağlıdır
        "roles": ["read", "create", "edit", "action_make_published"],
    },
    "viewer": {"name": "Viewer", "avatar": "guest.png", "roles": ["read"]},
}


class UsernameAndPasswordProvider(AuthProvider):
    """
    Bu sadece göstermek için bir örnektir, kullanıcı kimlik
    bilgilerini kaydetmek ve doğrulamak için daha iyi bir yol değildir.
    """

    async def login(
        self,
        username: str,
        password: str,
        remember_me: bool,
        request: Request,
        response: Response,
    ) -> Response:
        if len(username) < 3:
            """Form verisi doğrulama"""
            raise FormValidationError(
                {"username": "Ensure username has at least 03 characters"}
            )

        if username in users and password == "password":
            """`username` bilgisini session'a kaydedin"""
            request.session.update({"username": username})
            return response

        raise LoginFailed("Invalid username or password")

    async def is_authenticated(self, request) -> bool:
        if request.session.get("username", None) in users:
            """
            İsteğin durumunda bulunan `user` nesnesini kaydedin.
            Daha sonra bağlı kullanicinin erişimin' kısıtlamak için kullanılabilir.
            """
            request.state.user = users.get(request.session["username"])
            return True

        return False

    def get_admin_config(self, request: Request) -> AdminConfig:
        user = request.state.user  # Geçerli kullanıcı
        # Bağlı kullanıcıya göre uygulama başlığını güncelleyin
        custom_app_title = "Hello, " + user["name"] + "!"
        # Bağlı kullanıcıya göre logo url'ini güncelleyin
        custom_logo_url = None
        if user.get("company_logo_url", None):
            custom_logo_url = request.url_for("static", path=user["company_logo_url"])
        return AdminConfig(
            app_title=custom_app_title,
            logo_url=custom_logo_url,
        )

    def get_admin_user(self, request: Request) -> AdminUser:
        user = request.state.user  # Geçerli kullanıcı
        photo_url = None
        if user["avatar"] is not None:
            photo_url = request.url_for("static", path=user["avatar"])
        return AdminUser(username=user["name"], photo_url=photo_url)

    async def logout(self, request: Request, response: Response) -> Response:
        request.session.clear()
        return response

```

Çalışan bir örnek için [`https://github.com/jowilf/starlette-admin/tree/main/examples/auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/auth) sayfasına bakabilirsiniz.

## Özel Kimlik Doğrulama Akışı (OAuth2/OIDC, ...)

OAuth2 veya OIDC gibi özelleştirilmiş bir kimlik doğrulama akışı kullanmayı tercih ediyorsanız, özel `Kimlik Doğrulama Sağlayıcı`nızda aşağıdaki yöntemleri uygulayabilirsiniz:

* [is_authenticated][starlette_admin.auth.BaseAuthProvider.is_authenticated]: Bu metod, gelen her isteği doğrulamak için çağrılacaktır.
* [get_admin_user][starlette_admin.auth.BaseAuthProvider.get_admin_user]: Bağlı olan kullanıcı `adı` ve/veya `profil` bilgisini döndürür.
* [render_login][starlette_admin.auth.AuthProvider.render_login]: Özelleştirilmiş giriş sayfasını oluşturmak için varsayılan davranışı geçersiz kılın.
* [render_logout][starlette_admin.auth.AuthProvider.render_logout]: Özelleştirilmiş çıkış yapma mantığını uygulayın.

Bunlarla birlikte ihtiyaçlarınıza bağlı olarak aşağıdaki yöntemleri geçersiz kılabilirsiniz:

* [get_middleware][starlette_admin.auth.BaseAuthProvider.get_middleware]: Yönetici arayüzü için özel bir kimlik doğrulama ara yazılımı sağlamak için kullanılır.
* [setup_admin][starlette_admin.auth.BaseAuthProvider.setup_admin]: Yönetici arayüzünün kurulum aşamasında çağrılır ve özel konfigürasyonlar ve kurulum için kullanılır.

```python
from typing import Optional

from starlette.datastructures import URL
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import RedirectResponse, Response
from starlette.routing import Route
from starlette_admin import BaseAdmin
from starlette_admin.auth import AdminUser, AuthMiddleware, AuthProvider

from authlib.integrations.starlette_client import OAuth

from .config import AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_DOMAIN

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


class MyAuthProvider(AuthProvider):
    async def is_authenticated(self, request: Request) -> bool:
        if request.session.get("user", None) is not None:
            request.state.user = request.session.get("user")
            return True
        return False

    def get_admin_user(self, request: Request) -> Optional[AdminUser]:
        user = request.state.user
        return AdminUser(
            username=user["name"],
            photo_url=user["picture"],
        )

    async def render_login(self, request: Request, admin: BaseAdmin):
        """Özelleştirilmiş giriş mantığını geliştirmek için varsayılan davranışı geçersiz kılın."""
        auth0 = oauth.create_client("auth0")
        redirect_uri = request.url_for(
            admin.route_name + ":authorize_auth0"
        ).include_query_params(next=request.query_params.get("next"))
        return await auth0.authorize_redirect(request, str(redirect_uri))

    async def render_logout(self, request: Request, admin: BaseAdmin) -> Response:
        """Özelleştirilmiş çıkış mantığını geliştirmek için varsayılan davranışı geçersiz kılın."""
        request.session.clear()
        return RedirectResponse(
            url=URL(f"https://{AUTH0_DOMAIN}/v2/logout").include_query_params(
                returnTo=request.url_for(admin.route_name + ":index"),
                client_id=AUTH0_CLIENT_ID,
            )
        )

    async def handle_auth_callback(self, request: Request):
        auth0 = oauth.create_client("auth0")
        token = await auth0.authorize_access_token(request)
        request.session.update({"user": token["userinfo"]})
        return RedirectResponse(request.query_params.get("next"))

    def setup_admin(self, admin: "BaseAdmin"):
        super().setup_admin(admin)
        """Özel kimlik doğrulama için callback route'u ekleyin"""
        admin.routes.append(
            Route(
                "/auth0/authorize",
                self.handle_auth_callback,
                methods=["GET"],
                name="authorize_auth0",
            )
        )

    def get_middleware(self, admin: "BaseAdmin") -> Middleware:
        return Middleware(
            AuthMiddleware, provider=self, allow_paths=["/auth0/authorize"]
        )

```

Çalışan bir örnek için [`https://github.com/jowilf/starlette-admin/tree/main/examples/authlib`](https://github.com/jowilf/starlette-admin/tree/main/examples/authlib) sayfasına bakabilirsiniz.

`AuthProvider` aşağıdaki gibi yönetici arayüzünüze eklenebilir:

```python
admin = Admin(
    engine,
    title="Example: Authentication",
    auth_provider=MyAuthProvider(),
    middlewares=[Middleware(SessionMiddleware, secret_key=SECRET)],
)
```

## Authorization - Yetkilendirme

### Tüm Görünümler İçin

Her [görünüm][starlette_admin.views.BaseView] geçerli kullanıcının erişimini kısıtlamak için kullanılabilecek [is_accessible][starlette_admin.views.BaseView.is_accessible] metodunu kullanır.

```python

```python
from starlette_admin import CustomView
from starlette.requests import Request

class ReportView(CustomView):

    def is_accessible(self, request: Request) -> bool:
        return "admin" in request.state.user["roles"]
```

!!! important "Önemli"
    Görünüm erişilemez olduğunda, menü yapısında yer almaz.

### [ModelView][starlette_admin.views.BaseModelView] İçin

In [ModelView][starlette_admin.views.BaseModelView], içinde, geçerli kullanıcının erişimini kısıtlamak için aşağıdaki yöntemleri geçersiz kılabilirsiniz:

* `can_view_details`: Bir öğenin tam ayrıntılarını görüntüleme izni.
* `can_create`: Bir öğeyi oluşturma izni.
* `can_edit`: Bir öğeyi düzenleme izni.
* `can_delete`: Bir öğeyi silme izni.
* `is_action_allowed`: ismi verilen <abbr title="action">toplu işlem</abbr>in izin verilip verilmediğini doğrulayın.
* `is_row_action_allowed`: ismi verilen <abbr title="action">satır işlem</abbr>inin izin verilip verilmediğini doğrulayın.

```python
from starlette_admin.contrib.sqla import ModelView
from starlette.requests import Request
from starlette_admin import action, row_action

class ArticleView(ModelView):
    exclude_fields_from_list = [Article.body]

    def can_view_details(self, request: Request) -> bool:
        return "read" in request.state.user["roles"]

    def can_create(self, request: Request) -> bool:
        return "create" in request.state.user["roles"]

    def can_edit(self, request: Request) -> bool:
        return "edit" in request.state.user["roles"]

    def can_delete(self, request: Request) -> bool:
        return "delete" in request.state.user["roles"]

    async def is_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "action_make_published" in request.state.user["roles"]
        return await super().is_action_allowed(request, name)

    async def is_row_action_allowed(self, request: Request, name: str) -> bool:
        if name == "make_published":
            return "row_action_make_published" in request.state.user["roles"]
        return await super().is_row_action_allowed(request, name)

    @action(
        name="make_published",
        text="Mark selected articles as published",
        confirmation="Are you sure you want to mark selected articles as published ?",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
    )
    async def make_published_action(self, request: Request, pks: List[Any]) -> str:
        ...
        return "{} articles were successfully marked as published".format(len(pks))


    @row_action(
        name="make_published",
        text="Mark as published",
        confirmation="Are you sure you want to mark this article as published ?",
        icon_class="fas fa-check-circle",
        submit_btn_text="Yes, proceed",
        submit_btn_class="btn-success",
        action_btn_class="btn-info",
    )
    async def make_published_row_action(self, request: Request, pk: Any) -> str:
        ...
        return "The article was successfully marked as published"
```
