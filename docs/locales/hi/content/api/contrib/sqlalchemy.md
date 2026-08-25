---
title: SQLAlchemy Contrib API संदर्भ
description: starlette-admin में SQLAlchemy बैकएंड इंटीग्रेशन के लिए API संदर्भ दस्तावेज़।
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy {#contrib-sqlalchemy}

SQLAlchemy बैकएंड (`starlette_admin.contrib.sqla`) के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ,
जो docstrings से जेनरेट किया गया है। कार्य-उन्मुख मार्गदर्शन के लिए
[SQLAlchemy](../../integrations/sqlalchemy.md) देखें।

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Pydantic वैलिडेशन {#pydantic-validation}

`ext.pydantic` एक्सटेंशन, रिकॉर्ड लिखने से पहले फ़ॉर्म डेटा को एक Pydantic मॉडल के विरुद्ध वैलिडेट करता है। पूर्ण
मार्गदर्शन के लिए [Pydantic वैलिडेशन](../../integrations/sqlalchemy.md#pydantic-validation) देखें।

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## फ़ील्ड्स {#fields}

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## कन्वर्टर {#converters}

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## एक्सेप्शन {#exceptions}

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    ठोस फ़िल्टर क्लासेस (`EqualFilter`, `ContainsFilter`, `BetweenFilter`, आदि) यहाँ
    सूचीबद्ध नहीं हैं। ये [फ़िल्टर्स](../filters.md) में डॉक्यूमेंट किए गए बैकएंड-स्वतंत्र फ़िल्टर्स का
    एक-एक करके प्रतिबिंब हैं; जानने लायक SQLAlchemy-विशिष्ट व्यवहार
    [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry) में शामिल है।
