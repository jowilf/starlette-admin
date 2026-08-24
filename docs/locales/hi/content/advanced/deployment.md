---
title: डिप्लॉयमेंट
description: अपने FastAPI और starlette-admin एप्लिकेशन को सुरक्षित और कुशल तरीके से
  प्रोडक्शन में डिप्लॉय करने की बेहतरीन प्रथाएँ।
source_hash: def246bd4a7147614b7e4c4d87700c12e6e3d520c2d13ef9f06250aec691f355
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/deployment/)
<!-- translation-notice:end -->

# डिप्लॉयमेंट {#deployment}

एडमिन को रिवर्स प्रॉक्सी के पीछे चलाने पर दो बातें बदलती हैं जिन्हें लोकल डेवलपमेंट में आप नज़रअंदाज़ कर सकते हैं: secret key को worker प्रोसेस के दौरान स्थिर (stable) रहना चाहिए, और जनरेट किए गए URL को HTTPS दर्शाने चाहिए, भले ही आपका ऐप प्रॉक्सी से केवल सादा HTTP ही देखता हो।

!!! note "Framework-specific deployment guides"
    यह पेज केवल `Admin` के लिए विशिष्ट बातें कवर करता है। अंतर्निहित एप्लिकेशन और ASGI सर्वर के लिए देखें:

    * **FastAPI:** [FastAPI Deployment Documentation](https://fastapi.tiangolo.com/deployment/)
    * **Uvicorn:** [Uvicorn Deployment Documentation](https://www.uvicorn.org/deployment/)

```python
import os

from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin, ModelView

from myapp.models import Post

engine = create_engine(os.environ["DATABASE_URL"])
app = Starlette()

admin = Admin(
    engine,
    title="My Admin",
    base_url="/admin",
    secret_key=os.environ["ADMIN_SECRET_KEY"],
)
admin.add_view(ModelView(Post))
admin.mount_to(app)
```

```shell title="Running behind a reverse proxy"
uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
```

## Secret key

जब आप `secret_key` पास नहीं करते, तो `Admin` स्टार्टअप पर एक यादृच्छिक `secret_key` जनरेट करता है। किसी एक लोकल प्रोसेस के लिए यह ठीक है, लेकिन प्रत्येक worker प्रोसेस अपनी कुंजी स्वतंत्र रूप से जनरेट करती है, इसलिए एक worker द्वारा साइन किया गया CSRF टोकन दूसरे पर वैध नहीं होगा। एक से अधिक प्रोसेस चलाने से पहले `secret_key` को किसी एनवायरनमेंट वेरिएबल से सेट करें। मल्टी-worker फ़ेलियर मोड और कुंजी के उपयोग की पूरी जानकारी के लिए [Security](../user-guide/security.md) देखें।

## रिवर्स प्रॉक्सी और HTTPS {#reverse-proxy-and-https}

`Admin` हर इंटरनल लिंक (लिस्ट पेज, एडिट फ़ॉर्म, एक्सपोर्ट, `/static` माउंट, `/_files/...` के माध्यम से सर्व की गई अपलोड की गई फ़ाइलें) `request.url_for(...)` कॉल करके बनाता है, जो अपनी स्कीम इनकमिंग रिक्वेस्ट से लेता है। जब Nginx, Caddy, या Traefik जैसा कोई प्रॉक्सी TLS टर्मिनेट करके आपके ऐप को सादा HTTP फ़ॉरवर्ड करता है, तब Starlette को यह नहीं पता चल सकता कि मूल रिक्वेस्ट HTTPS थी — जब तक कि प्रॉक्सी `X-Forwarded-Proto` हेडर न भेजे और आपका ASGI सर्वर उस पर भरोसा न करे। इसे बिना कॉन्फ़िगर किए छोड़ने पर जनरेट किए गए लिंक `http://` पर डाउनग्रेड हो जाते हैं, जिन्हें ब्राउज़र ब्लॉक कर देते हैं या फिर री-राइट कर देते हैं जब पेज स्वयं HTTPS पर लोड हुआ हो।

इसे दो जगह ठीक करें:

1. **प्रॉक्सी** हेडर फ़ॉरवर्ड करता है:

    ```nginx title="nginx"
    location /admin/ {
        proxy_pass http://127.0.0.1:8000/admin/;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    ```

2. **Uvicorn** उस पर भरोसा करता है — `--proxy-headers` और `--forwarded-allow-ips` के साथ, जिसमें प्रॉक्सी का IP नामित होता है (`'*'` यदि प्रॉक्सी केवल आपके नेटवर्क के अंदर से ही पहुँचा जा सकता है):

    ```shell
    uvicorn myapp.main:app --forwarded-allow-ips='*' --proxy-headers
    ```

Gunicorn का `uvicorn.workers.UvicornWorker` वही दो सेटिंग्स `--forwarded-allow-ips` से पढ़ता है। प्रोसेस-मैनेजर विकल्पों का पूरा सेट देखने के लिए [Uvicorn's deployment docs](https://www.uvicorn.org/deployment/) देखें।

!!! warning
    `--forwarded-allow-ips='*'` **किसी भी** स्रोत से आए फ़ॉरवर्डेड हेडर पर भरोसा करता है। इसे तभी उपयोग करें जब ऐप आपके प्रॉक्सी के अलावा किसी और रास्ते से पहुँचा न जा सके — उदाहरण के लिए जब वह प्राइवेट नेटवर्क या Unix socket से बंधा (bind) हो। यदि ऐप सीधे पहुँचा जा सकता है, तो इस सेटिंग को प्रॉक्सी के वास्तविक IP तक सीमित रखें। अन्यथा कोई क्लाइंट `X-Forwarded-Proto` और `X-Forwarded-For` को सीधे स्पूफ़ कर सकता है।

## स्टैटिक एसेट {#static-assets}

एडमिन की CSS और JS फ़ाइलें `starlette_admin` पैकेज के अंदर शिप होती हैं, और `Admin` उन्हें स्वयं ही `base_url` के अंतर्गत एक `/static` माउंट के माध्यम से सर्व करता है — किसी अलग स्टैटिक होस्ट से नहीं। `static_dir` केवल अलग-अलग फ़ाइलों को ओवरराइड करने देता है ([Templates](templates.md) देखें); यह एसेट सर्विंग को आपकी ऐप प्रोसेस से हटाता नहीं है। इन्हें CDN से सर्व करने का कोई बिल्ट-इन विकल्प नहीं है। यदि आपको ऐसा करना है, तो प्रॉक्सी लेयर पर `{base_url}/static/*` के लिए cache-friendly `Cache-Control` रूल जोड़ें।

अपलोड की गई फ़ाइलों का मामला अलग है: `LocalStorage` इन्हें भी ऐप के माध्यम से सर्व करता है (`/_files/{storage}/{path}`, ताकि auth middleware फिर भी लागू रहे), लेकिन `S3Storage` और अन्य रिमोट बैकएंड इन्हें सीधे प्रोवाइडर से सर्व कर सकते हैं। [File Storage](../user-guide/file-storage.md) देखें।

---

## आगे क्या {#whats-next}

* **[Security](../user-guide/security.md):** `secret_key` का मल्टी-worker फ़्ूटगन पूरी तरह, साथ ही बिल्ट-इन सुरक्षा क्या-क्या कवर करती है और क्या नहीं।
* **[Authentication](../user-guide/auth.md):** प्रोडक्शन में एडमिन के पहुँच योग्य बनने से पहले ही उस तक पहुँच को नियंत्रित करें।
* **[File Storage](../user-guide/file-storage.md):** `S3Storage` और अन्य रिमोट बैकएंड को कॉन्फ़िगर करना।
