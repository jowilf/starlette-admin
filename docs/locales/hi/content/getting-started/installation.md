---
title: इंस्टॉलेशन
description: जानें कि अपने FastAPI या Starlette एप्लिकेशन के लिए एडमिन इंटरफ़ेस बनाने
  हेतु starlette-admin और उसकी वैकल्पिक डिपेंडेंसी कैसे इंस्टॉल करें।
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# इंस्टॉलेशन {#installation}

**starlette-admin** को अपनी पसंदीदा पैकेज मैनेजर से इंस्टॉल करें।

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin को **Python 3.11 या उसके बाद का वर्शन** चाहिए।

कोर पैकेज बैकएंड-अज्ञेयवादी (backend-agnostic) है। अपने एप्लिकेशन के लिए एडमिन इंटरफ़ेस बनाने के लिए, बेस पैकेज के साथ अपनी डेटा लेयर (जैसे SQLAlchemy, Beanie, MongoEngine, या Tortoise ORM) के उपयुक्त इंटीग्रेशन को इंस्टॉल करें।

## शामिल डिपेंडेंसी {#included-dependencies}

बेस इंस्टॉलेशन में एडमिन इंटरफ़ेस चलाने के लिए आवश्यक सब कुछ शामिल है। डिफ़ॉल्ट रूप से कोई वैकल्पिक डिपेंडेंसी इंस्टॉल नहीं होती।

| डिपेंडेंसी | उद्देश्य |
| --- | --- |
| [Starlette](https://www.starlette.io/) | एडमिन एप्लिकेशन को होस्ट करती है। |
| [Jinja2](https://jinja.palletsprojects.com/) | लिस्ट, डिटेल और फ़ॉर्म पेजों के लिए टेम्पलेट इंजन उपलब्ध कराती है। |
| [python-multipart](https://github.com/Kludex/python-multipart) | फ़ॉर्म सबमिशन और फ़ाइल अपलोड को पार्स करती है। |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | CSRF टोकन और फ़्लैश संदेशों के लिए कुकीज़ पर हस्ताक्षर करती है। |

FastAPI से बने एप्लिकेशन को किसी अतिरिक्त इंटीग्रेशन की आवश्यकता नहीं होती, क्योंकि FastAPI Starlette पर बना है। एडमिन इंटरफ़ेस को अपने मौजूदा FastAPI एप्लिकेशन पर माउंट करें।

## वैकल्पिक डिपेंडेंसी {#optional-dependencies}

starlette-admin निम्नलिखित वैकल्पिक डिपेंडेंसी प्रदान करता है:

- `pdf`: PDF एक्सपोर्ट सपोर्ट जोड़ता है ([reportlab](https://www.reportlab.com/))।
- `i18n`: अंतर्राष्ट्रीयकरण सपोर्ट जोड़ता है ([Babel](https://babel.pocoo.org/))।
- `tinymce`: रिच टेक्स्ट एडिटर सपोर्ट जोड़ता है। [nh3](https://nh3.readthedocs.io/) इंस्टॉल करता है, जो `TinyMCEEditorField` द्वारा सबमिट किए गए HTML को सैनिटाइज़ करता है।
- `s3`: S3-संगत ऑब्जेक्ट स्टोरेज सपोर्ट जोड़ता है। AWS S3 और MinIO जैसी संगत ऑब्जेक्ट स्टोरेज सेवाओं पर असिंक्रोनस अपलोड के लिए [aiobotocore](https://aiobotocore.readthedocs.io/) इंस्टॉल करता है।

एक या अधिक वैकल्पिक डिपेंडेंसी को starlette-admin के साथ इंस्टॉल करें:

=== "pip"

    ```bash
    # Install the `pdf` extra.
    pip install "starlette-admin[pdf]"

    # Install multiple extras.
    pip install "starlette-admin[i18n,pdf,s3]"
    ```

=== "uv"

    ```bash
    # Install the `pdf` extra.
    uv add "starlette-admin[pdf]"

    # Install multiple extras.
    uv add "starlette-admin[i18n,pdf,s3]"
    ```

## सोर्स से इंस्टॉल करें {#install-from-source}

नवीनतम अप्रकाशित बदलावों का उपयोग करने के लिए, पैकेज को सीधे GitHub रिपॉज़िटरी से इंस्टॉल करें।

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## अगले चरण {#next-steps}

- **[क्विकस्टार्ट](quickstart.md)**: वास्तविक डेटा के साथ अपना पहला एडमिन इंटरफ़ेस बनाएँ।
- **[अवधारणाएँ](concepts.md)**: starlette-admin के पीछे के कोर आर्किटेक्चर और डिज़ाइन सिद्धांतों को जानें।
