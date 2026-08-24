---
title: MongoEngine Contrib API संदर्भ
description: starlette-admin में MongoEngine बैकएंड इंटीग्रेशन के लिए API संदर्भ दस्तावेज़।
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib: MongoEngine {#contrib-mongoengine}

MongoEngine बैकएंड
(`starlette_admin.contrib.mongoengine`) के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो docstrings से जेनरेट किया गया है। कार्य-उन्मुख
मार्गदर्शन के लिए [MongoEngine](../../integrations/mongoengine.md) देखें।

::: starlette_admin.contrib.mongoengine.admin.Admin

::: starlette_admin.contrib.mongoengine.view.ModelView

::: starlette_admin.contrib.mongoengine.view.InlineModelView

## फ़ील्ड्स {#fields}

::: starlette_admin.contrib.mongoengine.fields.ObjectIdField

::: starlette_admin.contrib.mongoengine.fields.FileField

::: starlette_admin.contrib.mongoengine.fields.ImageField

## कन्वर्टर {#converters}

::: starlette_admin.contrib.mongoengine.converters.BaseMongoEngineModelConverter

::: starlette_admin.contrib.mongoengine.converters.ModelConverter

## एक्सेप्शन {#exceptions}

::: starlette_admin.contrib.mongoengine.exceptions.NotSupportedField

!!! note
    ठोस फ़िल्टर क्लासेस (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, आदि)
    यहाँ सूचीबद्ध नहीं हैं। ये [फ़िल्टर्स](../filters.md) में डॉक्यूमेंट किए गए बैकएंड-स्वतंत्र
    फ़िल्टर्स के अनुरूप हैं; MongoEngine-विशिष्ट व्यवहार
    [MongoEngine](../../integrations/mongoengine.md#filter-registry) में शामिल है।
