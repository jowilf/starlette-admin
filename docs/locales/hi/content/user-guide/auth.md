---
title: प्रमाणीकरण
description: starlette-admin में AuthProvider का उपयोग करके प्रमाणीकरण लागू करें या
  अपना डैशबोर्ड सुरक्षित करने के लिए OAuth के साथ एकीकृत (integrate) करें।
source_hash: 0d55840abab5be403a7df83cdd20bf17ea575bd61f49aaeafcddfb76b3e76054
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "पर्यवेक्षित मशीन अनुवाद"

    यह सामग्री मानव-निर्मित शब्दावलियों और शैली गाइडों के मार्गदर्शन में
    मशीन जनरेशन द्वारा अनुवादित की गई है। चूँकि इस पाठ की समीक्षा
    लाइन-दर-लाइन मैन्युअल रूप से नहीं की गई है, इसलिए कभी-कभी त्रुटियाँ या
    अनाड़ी वाक्य-रचना हो सकती है।

    किसी भी विसंगति की स्थिति में, मूल अंग्रेज़ी संस्करण ही प्रामाणिक स्रोत
    है।

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/auth/)
<!-- translation-notice:end -->

# प्रमाणीकरण {#authentication}

आप एक ही मेथड लागू करके एडमिन इंटरफ़ेस को सुरक्षित करते हैं:

```python
async def authenticate(request) -> AdminUser | None
```

एडमिन का हर संरक्षित (protected) रिक्वेस्ट इस मेथड से गुज़रता है। जब यह `AdminUser` लौटाता है, तो रिक्वेस्ट प्रमाणित (authenticated) हो जाती है। जब यह `None` लौटाता है, तो रिक्वेस्ट अप्रमाणित रहती है और आपके द्वारा कॉन्फ़िगर किया गया साइन-इन या OAuth फ़्लो आगे बढ़ जाता है।

सफलता पर, लौटाया गया `AdminUser` यहाँ उपलब्ध हो जाता है:

```python
request.state.admin_user
```

विफलता पर, रिक्वेस्ट अनामित (anonymous) चिह्नित हो जाती है:

```python
request.state.is_anonymous = True
```

सार्वजनिक और आंशिक रूप से संरक्षित रूट फिर प्रमाणित और अप्रमाणित रिक्वेस्ट को साइन-इन फ़्लो शुरू किए बिना अलग-अलग पहचान सकते हैं।


## प्रमाणीकरण प्रदाता चुनें {#choose-an-authentication-provider}

| प्रदाता | कब उपयोग करें | आप क्या लागू करते हैं |
| --- | --- | --- |
| `AuthProvider` | आप बिल्ट-इन साइन-इन पेज चाहते हैं और क्रेडेंशियल स्वयं जाँचते हैं। | `login()`, `logout()`, `authenticate()` |
| `OAuthProvider` | आप Auth0, Okta, या Google जैसा OAuth2 या OIDC रीडायरेक्ट फ़्लो चाहते हैं। | `redirect_to_provider()`, `handle_callback()`, `authenticate()` |

दोनों `BaseAuthProvider` के सबक्लास हैं और एक ही अनुबंध (contract) साझा करते हैं। `authenticate()` हर रिक्वेस्ट पर चलता है। जो यह लौटाता है वही `request.state.admin_user` बन जाता है, और जब यह `None` लौटाता है, तो फ़्रेमवर्क `request.state.is_anonymous = True` सेट कर देता है।

## `AuthProvider`: बिल्ट-इन साइन-इन पेज {#authprovider-built-in-sign-in-page}

जब आप चाहते हैं कि फ़्रेमवर्क साइन-इन फ़ॉर्म रेंडर और हैंडल करे और आप क्रेडेंशियल सत्यापित करें, तब इस प्रदाता का उपयोग करें। टेम्पलेट, POST हैंडलिंग, और रीडायरेक्ट का स्वामित्व फ़्रेमवर्क के पास रहता है।

यहाँ एक संपूर्ण उदाहरण है:

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

### आवश्यक मेथड {#required-methods}

एक `AuthProvider` तीन मेथड लागू करता है। यहाँ `SessionMiddleware` आवश्यक है, क्योंकि वह उपयोगकर्ता की साइन-इन स्थिति (state) को रिक्वेस्ट के बीच बनाए रखता है।

#### `login()`

यह मेथड फ़ॉर्म सबमिशन को हैंडल करता है। इसे `username`, `password`, एक `remember_me` बूलियन, और मौजूदा `request` प्राप्त होता है।

* **सफलता पर:** कोई पहचानकर्ता (identifier), जैसे उपयोगकर्ता ID या यूज़रनेम, `request.session` में लिखें। फिर फ़्रेमवर्क को `next` या एडमिन इंडेक्स पर रीडायरेक्ट करने देने के लिए `None` लौटाएँ, या कहीं और रीडायरेक्ट करने के लिए एक `Response` लौटाएँ।
* **विफलता पर:** फ़ॉर्म के ऊपर त्रुटि दिखाने के लिए `LoginFailed("message")` उठाएँ, या किसी विशिष्ट फ़ील्ड को अमान्य चिह्नित करने के लिए `FormValidationError({"username": "..."})` उठाएँ।

#### `authenticate()`

यह मेथड किसी *भी* संरक्षित एडमिन रूट पर आने वाली हर रिक्वेस्ट पर चलता है। इसे `request` ऑब्जेक्ट प्राप्त होता है।

* `login()` के दौरान `request.session` में सहेजा गया पहचानकर्ता पढ़ें।
* अपने डेटाबेस में उपयोगकर्ता खोजें।
* जब उपयोगकर्ता मौजूद और वैध हो, तो एक `AdminUser` इंस्टेंस लौटाएँ।
* जब उपयोगकर्ता मौजूद न हो या साइन-इन न हो, तो `None` लौटाएँ।

#### `logout()`

यह मेथड साइन-आउट को हैंडल करता है। इसे `request` ऑब्जेक्ट प्राप्त होता है, और एक्सेस रद्द करने के लिए आप उपयोगकर्ता का डेटा `request.session` से हटा देते हैं। एडमिन इंडेक्स पर डिफ़ॉल्ट रीडायरेक्ट के लिए `None` लौटाएँ, या कहीं और रीडायरेक्ट करने के लिए एक `Response` लौटाएँ।

## `OAuthProvider`: OAuth2/OIDC रीडायरेक्ट फ़्लो {#oauthprovider-oauth2oidc-redirect-flow}


जब आप प्रमाणीकरण Auth0, Okta, Google, या Microsoft Entra ID जैसे बाहरी आइडेंटिटी प्रदाता (identity provider) को सौंपते हैं, तब `OAuthProvider` का उपयोग करें।

`AuthProvider` एडमिन के भीतर यूज़रनेम-पासवर्ड फ़ॉर्म हैंडल करता है। `OAuthProvider` इसके बजाय रीडायरेक्ट-आधारित फ़्लो का उपयोग करता है:

1. उपयोगकर्ता को आइडेंटिटी प्रदाता पर रीडायरेक्ट करें।
2. प्रदाता उपयोगकर्ता को प्रमाणित करता है।
3. प्रदाता आपके एप्लिकेशन पर वापस रीडायरेक्ट करता है।
4. आपका एप्लिकेशन कॉलबैक (callback) का उपयोगकर्ता की पहचान के लिए विनिमय (exchange) करता है।
5. `authenticate()` सेशन से उपयोगकर्ता को पुनर्स्थापित (restore) करता है।

### कॉलबैक URL सेटअप (आवश्यक) {#callback-url-setup-required}

`OAuthProvider` लागू करने से पहले, अपने आइडेंटिटी प्रदाता के डैशबोर्ड में अपने एप्लिकेशन का कॉलबैक URL पंजीकृत करें। सुरक्षा के लिए, OAuth प्रदाता केवल पूर्व-अनुमोदित URL पर रीडायरेक्ट करते हैं।

#### उदाहरण कॉलबैक URL {#example-callback-url}

```text
https://your-domain.com/admin/oauth/callback
```

#### लोकल डेवलपमेंट {#local-development}

```text
http://localhost:8000/admin/oauth/callback
```

!!! important
    आपका सटीक कॉलबैक URL आपके कॉन्फ़िगरेशन पर निर्भर करता है। यह `Admin` को माउंट करते समय उपयोग किए गए `route_name`, और प्रदाता के `callback_path` से मिलकर बनता है।

    डिफ़ॉल्ट सेटअप उपयोग करता है:

    * `route_name="admin"`
    * `callback_path="oauth/callback"`

    जो यह कॉलबैक URL बनाता है:

    ```text
    /admin/oauth/callback
    ```

    डिप्लॉय करने पर यह बन जाता है:

    ```text
    https://your-domain.com/admin/oauth/callback
    ```

    अगर आप माउंट प्रीफ़िक्स या प्रदाता कॉलबैक पथ बदलते हैं, तो यह URL भी बदल जाता है, और आपको इसे अपने OAuth प्रदाता कॉन्फ़िगरेशन में अपडेट करना होगा।

### आवश्यक मेथड {#required-methods_1}

एक `OAuthProvider` वही सेशन-आधारित पैटर्न उपयोग करता है जो `AuthProvider` करता है, लेकिन साइन-इन को रीडायरेक्ट और कॉलबैक में बाँटता है।

#### `redirect_to_provider()`

यह मेथड OAuth फ़्लो शुरू करता है। इसे `request` और एक जनरेट किया गया `callback_url` प्राप्त होता है, और उसे ऐसा `Response` लौटाना चाहिए जो उपयोगकर्ता के ब्राउज़र को आपके आइडेंटिटी प्रदाता पर रीडायरेक्ट करे।

#### `handle_callback()`

यह मेथड तब चलता है जब ब्राउज़र प्रदाता से ऑथराइज़ेशन कोड (authorization code) लेकर लौटता है। इसे `request` प्राप्त होता है। कोड को एक्सेस टोकन के लिए विनिमय करें, उपयोगकर्ता की प्रोफ़ाइल फ़ेच करें, और उसकी पहचान `request.session` में सहेजें।

#### `authenticate()`

`AuthProvider` की तरह, यह मेथड `handle_callback()` द्वारा सेशन में सहेजी गई चीज़ों को वापस पढ़ता है। जब सेशन में वैध उपयोगकर्ता डेटा हो तो `AdminUser` लौटाएँ, अन्यथा `None` लौटाएँ।

#### `logout()`

सेशन डेटा साफ़ करें। उपयोगकर्ता को आइडेंटिटी प्रदाता से भी साइन-आउट करवाने के लिए (OIDC RP-initiated logout), इस मेथड को ओवरराइड करें और `None` लौटाने के बजाय प्रदाता के end-session एंडपॉइंट की ओर इशारा करने वाला रीडायरेक्ट `Response` लौटाएँ।

यहाँ एक संपूर्ण उदाहरण है:

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

## प्रदाता पंजीकृत करें {#register-the-provider}

प्रमाणीकरण प्रदाता लागू करने के बाद, उसे `Admin` इंस्टेंस से जोड़ें।

```python
admin = Admin(
    engine, title="My Admin", auth_provider=MyAuthProvider(), secret_key="..."
)
admin.mount_to(app)
```

यही एक पंक्ति पूरा एकीकरण (integration) है। `Admin` प्रदाता के `AuthMiddleware` को हर एडमिन रूट से आगे माउंट करता है और प्रदाता के रूट (साइन-इन, साइन-आउट, और `OAuthProvider` के लिए कॉलबैक) को एडमिन प्रीफ़िक्स के भीतर जोड़ता है।

## अनुमति जाँचें {#permission-checks}

प्रमाणीकरण यह बताता है कि "यह कौन है?" अनुमतियाँ यह बताती हैं कि "वे क्या कर सकते हैं?" अनुमतियाँ व्यू से जुड़ी होती हैं। भूमिका-आधारित एक्सेस तीन चरणों में लगता है:

1. `AdminUser`, जो एक साधारण dataclass है, का सबक्लास बनाकर उसमें `roles` सूची जोड़ें।
2. अपने यूज़र स्टोर से भरकर, अपने प्रदाता के `authenticate()` मेथड से वही सबक्लास लौटाएँ।
3. व्यू के अनुमति हुक में `request.state.admin_user.roles` पढ़ें।

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

`MyAuthProvider` को किसी अन्य प्रदाता की तरह पंजीकृत करें, जैसे `admin = Admin(engine, auth_provider=MyAuthProvider(), secret_key=SECRET)`। इसके बाद ऊपर का हर हुक `request.state.admin_user.roles` तक पहुँच रखता है।

`is_accessible()`, जो हर `BaseView` पर उपलब्ध है, साइडबार एंट्री सहित पूरे व्यू को छिपा देता है। `can_create`, `can_edit`, `can_delete`, `can_export`, `can_import`, और `can_view_detail` किसी `ModelView` पर अलग-अलग ऑपरेशन को नियंत्रित (gate) करते हैं। `can_access_field` विशिष्ट फ़ील्ड छिपाता है, और `is_action_allowed` तथा `is_row_action_allowed` बैच व पंक्ति एक्शन को प्रतिबंधित करते हैं। जब कोई पंक्ति एक्शन उपयोगकर्ता के बजाय रिकॉर्ड पर निर्भर हो, जैसे पहले से प्रकाशित आर्टिकल पर `publish` छिपाना, तब `is_row_action_allowed_for_obj(request, name, obj)` को ओवरराइड करें। उसे पंक्ति का अंतर्निहित (underlying) ऑब्जेक्ट प्राप्त होता है और वह `is_row_action_allowed` पर फ़ॉलबैक करता है।

संपूर्ण API संदर्भ के लिए, [व्यू](views.md) और [एक्शन](actions.md) देखें। `can_export`, `can_import`, और एक पंक्ति एक्शन के साथ पूरा कार्यशील संस्करण [`examples/03-auth`](https://github.com/jowilf/starlette-admin/tree/main/examples/03-auth) में है।

## `@login_not_required`

अन्यथा पूरी तरह सुरक्षित एडमिन पैनल में भी कुछ रूट सार्वजनिक रहते हैं, जैसे स्वयं-सेवा पंजीकरण फ़ॉर्म या हेल्थ चेक। उस एंडपॉइंट को डेकोरेट करें, और `AuthMiddleware` वैध `authenticate()` परिणाम की जाँच किए बिना रिक्वेस्ट को आगे जाने देता है:

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

`@route` और `@login_not_required` दोनों फ़ंक्शन को एक एट्रिब्यूट से चिह्नित करके उसे अपरिवर्तित (unchanged) लौटाते हैं, इसलिए इन्हें जिस क्रम में स्टैक किया जाए, कोई फ़र्क़ नहीं पड़ता।

## `allow_routes`

`allow_routes` आपको फ़ंक्शन-स्तर के बजाय रूट-नाम स्तर पर वही बाईपास (bypass) देता है। इसका उपयोग तब करें जब एंडपॉइंट परिभाषा आपके नियंत्रण में न हो, या जब आप बाईपास सूची एक ही जगह रखना चाहते हों:

```python
provider = MyAuthProvider(allow_routes=["register"])
```

वह स्ट्रिंग रूट का नाम होती है: या तो मेथड का नाम, या `@route` में `name=` पैरामीटर को दिया गया मान, जैसे ऊपर `name="register"`। `AuthMiddleware` आपके द्वारा सूचीबद्ध कस्टम रूट के अलावा `"login"` और `"static"` को हमेशा अनुमति देता है।

## `AdminUser`

जो कुछ भी `authenticate()` लौटाता है, वही `request.state.admin_user` को भर देता है। टॉप बार उससे दो फ़ील्ड पढ़ता है:

| एट्रिब्यूट | टाइप | डिफ़ॉल्ट | विवरण |
| --- | --- | --- | --- |
| `username` | `str` | `"Administrator"` (अनुवाद योग्य) | टॉप-बार उपयोगकर्ता मेन्यू में दिखाया जाने वाला नाम। |
| `photo_url` | `str | None` | `None` | अवतार (avatar) छवि का URL. सेट न होने पर प्लेसहोल्डर आइकन पर फ़ॉलबैक करता है। |

`AdminUser` एक साधारण `@dataclass` है, इसलिए भूमिकाएँ, कोई टेनेंट ID, या आपके अनुमति हुक की ज़रूरत की कोई भी अन्य चीज़ ले जाने के लिए उसका सबक्लास बनाना ही अभीष्ट पैटर्न है। ऊपर दिया `MyAdminUser` उदाहरण इसे व्यवहार में दिखाता है।

---

**आगे क्या**

* [सुरक्षा](security.md): CSRF, सीक्रेट की, और फ़्रेमवर्क स्वतः क्या सुरक्षित रखता है।
* [व्यू](views.md): `can_create`, `can_edit`, `can_delete`, और अनुमति हुक की पूरी सूची।
* [एक्शन](actions.md): बैच और पंक्ति एक्शन के लिए `is_action_allowed` और `is_row_action_allowed`।
