---
title: एकाधिक एडमिन इंस्टेंस
description: अलग-अलग उपयोगकर्ता भूमिकाओं या डोमेन के लिए एक ही FastAPI एप्लिकेशन पर
  कई पृथक एडमिन डैशबोर्ड माउंट करें।
source_hash: 8b8c561c0c44bf9cb942e4e0d074f7a7e10c1e1fadb7339f4c76acce70d3a9a2
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/multiple-admin/)
<!-- translation-notice:end -->

# एकाधिक एडमिन इंस्टेंस {#multiple-admin-instances}

आपके द्वारा बनाया गया प्रत्येक `Admin` इंस्टेंस एक स्वयं-निहित (self-contained) Starlette सब-एप्लिकेशन है। जितनी आवश्यकता हो, उतनी इंस्टेंस माउंट करें — प्रत्येक का अपना `base_url`, `route_name`, authentication provider, और views।

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

इस उदाहरण में `/staff` पर `StaffAuth` द्वारा समर्थित एक sign-in पेज और `/root` पर `SuperAdminAuth` द्वारा समर्थित एक अलग sign-in पेज दिखता है। एक में sign in करना दूसरे तक पहुँच नहीं देता: प्रत्येक `SessionMiddleware` अपनी cookie को अपनी ही `secret_key` से साइन करता है, इसलिए प्रत्येक `Admin` इंस्टेंस केवल उही session डेटा पढ़ता है जो उसका अपना authentication provider लिखा था।

## `base_url` और `route_name` {#base_url-and-route_name}

`base_url` और `route_name` `starlette_admin/base.py` में `Admin` और `BaseAdmin` क्लासों के constructor parameters हैं। उनके डिफ़ॉल्ट `/admin` और `"admin"` हैं:

```python
def __init__(
    self,
    title: str = "Admin",
    base_url: str = "/admin",
    route_name: str = "admin",
    ...
)

```

* **`base_url`** वह पाथ prefix सेट करता है जिस पर एडमिन माउंट होता है। यह सीधे इंटरनल `app.mount(self.base_url, app=admin_app, name=self.route_name)` कॉल में चला जाता है, इसलिए प्रति-इंस्टेंस इसका unique होना ज़रूरी है — अन्यथा एक mount दूसरे पर छाया (shadow) कर देगा।
* **`route_name`** वह नाम है जिसके अंतर्गत Starlette mount को रजिस्टर करता है। एडमिन द्वारा जनरेट किया गया हर URL — lists, details, edits, exports और static assets — `request.url_for(route_name + ":list", ...)` से आता है, और हर पेज टेम्पलेट link building के लिए सही prefix पाने के लिए `request.app.state.ROUTE_NAME` पढ़ता है।

`mount_to` प्रत्येक एडमिन इंस्टेंस के लिए एक नया Starlette सब-एप्लिकेशन बनाता है, इसलिए middleware, routes और template globals पृथक रहते हैं। `Admin` कोई process-wide singleton नहीं है: अपने एप्लिकेशन की ज़रूरत के अनुसार जितने स्वतंत्र इंस्टेंस चाहें बनाएँ।

!!! warning
    हर `Admin` को एक distinct `route_name` दें। Starlette का राउटर `url_for("admin:list", ...)` को mount **name** मिलाकर resolve करता है, इसलिए एक ही `route_name` साझा करने वाले दो एडमिन parent एप्लिकेशन में एक ही नाम के दो mounts छोड़ देते हैं, और `url_for` उसी को resolve करता है जिसे Starlette पहले मिलाता है। तब दूसरे एडमिन का हर इंटरनल लिंक — edit links, static assets और export endpoints सहित — चुपचाप पहले एडमिन के `base_url` की ओर इशारा करने लगता है।

## Views साझा करना vs. अलग views परिभाषित करना {#sharing-views-vs-defining-separate-views}

`add_view` एक view इंस्टेंस लेता है और setup के दौरान उसे mutate करता है। `BaseModelView` के लिए, यह setup इंटरनल callbacks को उस एडमिन से बाँधता (bind) है जिसके साथ वह रजिस्टर है — जिसमें यह भी शामिल है कि `HasOne` और `HasMany` फ़ील्ड related-record links कैसे resolve करते हैं।

वही view **instance** दो एडमिन पर रजिस्टर करें और दूसरा `add_view` कॉल उन callbacks को overwrite कर देगा; परिणामस्वरूप पहले एडमिन के पेजों के relation links दूसरे एडमिन के views और URLs के विरुद्ध resolve होंगे।

इससे बचने के लिए, प्रत्येक एडमिन को `ModelView` **क्लास** का एक नया इंस्टेंस दें। क्लास में कोई admin-specific state नहीं होती — केवल instances में होती है:

```python
staff_admin.add_view(ModelView(Order))
root_admin.add_view(
    ModelView(Order)
)  # separate instance of the same class; this is safe
```

जब दोनों एडमिन को अलग व्यवहार चाहिए — जैसे अलग visibility rules या `can_delete` permissions — तो shared instance को runtime पर patch करने के बजाय प्रत्येक के लिए एक subclass लिखें:

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

## आगे क्या {#whats-next}

* **[Authentication](../user-guide/auth.md):** पूर्ण `AuthProvider` और `OAuthProvider` contract.
* **[Extension Points](extension-points.md):** `Admin` क्लास पर उपलब्ध बाकी हर pluggable surface.
* **[क्विकस्टार्ट](../getting-started/quickstart.md):** बुनियादी single-admin setup जिस पर यह गाइड बनी है।
