---
title: Admin API संदर्भ
description: starlette-admin में Admin क्लास के लिए API संदर्भ दस्तावेज़।
source_hash: 1c016173cc04603ea66bc0c67d4b34273b13d06baea3238d0ca3cd0c5f09c994
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/admin/)
<!-- translation-notice:end -->

# Admin {#admin}

`BaseAdmin` का पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो इसके docstrings से जेनरेट किया गया है। इसके
कंस्ट्रक्टर विकल्पों का कार्य-उन्मुख मार्गदर्शन देखने के लिए
[Configuring Admin](../user-guide/admin.md) देखें।

`starlette_admin` अपना कोई ठोस `Admin` क्लास एक्सपोर्ट नहीं करता। `starlette_admin.contrib` का
प्रत्येक बैकएंड (`sqla`, `sqlmodel`, `beanie`, `mongoengine`, `tortoise`) अपनी `Admin`
सबक्लास शामिल करता है, जिनका कंस्ट्रक्टर सिग्नेचर वही है जो नीचे डॉक्यूमेंट किया गया है।

::: starlette_admin.base.BaseAdmin
