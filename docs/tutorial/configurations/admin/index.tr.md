# Admin Konfigürasyonu

Yönetici arayüzünüzü özelleştirmek için birçok seçenek mevcuttur.

```python
admin = Admin(
    title="SQLModel Admin",
    base_url="/admin",
    route_name="admin",
    statics_dir="statics/admin",
    templates_dir="templates/admin",
    logo_url="`https`://preview.tabler.io/static/logo-white.svg",
    login_logo_url="`https`://preview.tabler.io/static/logo.svg",
    index_view=CustomView(label="Home", icon="fa fa-home", path="/home", template_path="home.html"),
    auth_provider=MyAuthProvider(login_path="/sign-in", logout_path="/sign-out"),
    middlewares=[],
    debug=False,
    i18n_config = I18nConfig(default_locale="en")
)
```

## Parametreler

* `title`: Yönetici arayüzü başlığı.
* `base_url`: Yönetici arayüzünün başlangıç URL'i.
* `route_name`: Bağlanmış yönetici arayüzü ismi.
* `logo_url`: Başlık yerine kullanılacak logonun URL'i.
* `login_logo_url`: Bu değeri atarsanız, giriş sayfasında `logo_url` yerine kullanılacaktır.
* `statics_dir`: Dosya özelinde <abbr title="static">statik</abbr> dosyalar için kullanılacak dizin.
* `templates_dir`: Özelleştirme için kullanılacak <abbr title="templates">şablonlar</abbr> dizini.
* `index_view`: Anasayfa için kullanılacak <abbr title="CustomView">özel görünüm</abbr>.
* `auth_provider`: Kimlik doğrulama sağlayıcısı
* `middlewares`: Starlette <abbr title="middleware">ara yazılımları</abbr>
* `i18n_config`: Admin arayüzü için i18n konfigürasyonu
