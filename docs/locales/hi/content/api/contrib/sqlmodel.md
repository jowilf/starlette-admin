---
title: SQLModel Contrib API संदर्भ
description: starlette-admin में SQLModel बैकएंड इंटीग्रेशन के लिए API संदर्भ दस्तावेज़।
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib: SQLModel {#contrib-sqlmodel}

SQLModel बैकएंड (`starlette_admin.contrib.sqlmodel`) के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ,
जो docstrings से जेनरेट किया गया है। SQLModel अंदरूनी रूप से SQLAlchemy है, इसलिए `Admin` और `ModelView`,
[SQLAlchemy बैकएंड](sqlalchemy.md) की हल्की सबक्लासेस हैं जो फ़ॉर्म डेटा को मॉडल की
Pydantic लेयर के ज़रिए वैलिडेट करती हैं। कार्य-उन्मुख मार्गदर्शन के लिए
[SQLModel इंटीग्रेशन](../../integrations/sqlmodel.md) देखें।

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
