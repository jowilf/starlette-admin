---
title: Tortoise ORM Contrib API संदर्भ
description: starlette-admin में Tortoise ORM बैकएंड इंटीग्रेशन के लिए API संदर्भ
  दस्तावेज़।
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib: Tortoise ORM {#contrib-tortoise-orm}

Tortoise ORM बैकएंड
(`starlette_admin.contrib.tortoise`) के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो docstrings से जेनरेट किया गया है। कार्य-उन्मुख
मार्गदर्शन के लिए [Tortoise ORM](../../integrations/tortoise.md) देखें।

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## फ़ील्ड्स {#fields}

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## कन्वर्टर {#converters}

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    ठोस फ़िल्टर क्लासेस (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter`, आदि)
    यहाँ सूचीबद्ध नहीं हैं। ये [फ़िल्टर्स](../filters.md) में डॉक्यूमेंट किए गए बैकएंड-स्वतंत्र
    फ़िल्टर्स के अनुरूप हैं; Tortoise-विशिष्ट व्यवहार (केस-इनसेंसिटिव लुकअप, enum रूपांतरण,
    raw key column null चेक)
    [Tortoise ORM](../../integrations/tortoise.md#filter-registry) में शामिल है।
