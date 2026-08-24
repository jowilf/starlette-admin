---
title: फ़िल्टर्स API संदर्भ
description: starlette-admin में डेटाबेस क्वेरी फ़िल्टर्स के लिए API संदर्भ दस्तावेज़।
source_hash: c26f3e6379afdc4268934bf0f05b895ebb00f0517dd9834b6fbc337c4f192231
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/filters/)
<!-- translation-notice:end -->

# फ़िल्टर्स {#filters}

फ़िल्टर सिस्टम के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो docstrings से जेनरेट किया गया है। कार्य-उन्मुख
मार्गदर्शन के लिए [फ़िल्टर्स](../user-guide/filters.md) और
[कस्टम फ़िल्टर](../advanced/custom-filters.md) देखें।

नीचे दी गई क्लासेस बैकएंड-स्वतंत्र हैं: ये किसी फ़िल्टर का `name`, `label`, और
`data_type` घोषित करती हैं, लेकिन उसकी क्वेरी लॉजिक नहीं। प्रत्येक ORM बैकएंड (`contrib.sqla`, `contrib.beanie`,
`contrib.mongoengine`, `contrib.tortoise`) इन्हें सबक्लास करके उस
बैकएंड के लिए वास्तविक `apply()` इंप्लीमेंटेशन जोड़ता है। ठोस, इंपोर्ट करने योग्य फ़िल्टर क्लासेस के लिए संबंधित [इंटीग्रेशन पेज](../integrations/sqlalchemy.md) देखें।

## कोर प्रकार {#core-types}

::: starlette_admin.filters.base.FilterDataType

::: starlette_admin.filters.base.BaseFilter

::: starlette_admin.filters.base.FilterApplyContext

::: starlette_admin.filters.base.FilterValidationError

::: starlette_admin.filters.base.FilterRule

::: starlette_admin.filters.base.FilterGroup

::: starlette_admin.filters.registry.FilterRegistry

::: starlette_admin.filters.registry.filters

## जेनेरिक {#generic}

::: starlette_admin.filters.generic.EqualFilter

::: starlette_admin.filters.generic.NotEqualFilter

::: starlette_admin.filters.generic.IsNullFilter

::: starlette_admin.filters.generic.IsNotNullFilter

## संख्यात्मक {#numeric}

::: starlette_admin.filters.numeric.EqualFilter

::: starlette_admin.filters.numeric.NotEqualFilter

::: starlette_admin.filters.numeric.GreaterThanFilter

::: starlette_admin.filters.numeric.LessThanFilter

::: starlette_admin.filters.numeric.GreaterThanOrEqualFilter

::: starlette_admin.filters.numeric.LessThanOrEqualFilter

::: starlette_admin.filters.numeric.BetweenFilter

## स्ट्रिंग {#string}

::: starlette_admin.filters.string.ContainsFilter

::: starlette_admin.filters.string.NotContainsFilter

::: starlette_admin.filters.string.StartsWithFilter

::: starlette_admin.filters.string.EndsWithFilter

## बूलियन {#boolean}

::: starlette_admin.filters.boolean.IsTrueFilter

::: starlette_admin.filters.boolean.IsFalseFilter

## दिनांक और समय {#date-and-time}

::: starlette_admin.filters.date.DateEqualFilter

::: starlette_admin.filters.date.DateTimeEqualFilter

::: starlette_admin.filters.date.TimeEqualFilter

::: starlette_admin.filters.date.DateBetweenFilter

::: starlette_admin.filters.date.DateTimeBetweenFilter

::: starlette_admin.filters.date.TimeBetweenFilter

::: starlette_admin.filters.date.DateInPastFilter

::: starlette_admin.filters.date.DateInFutureFilter

## Enum {#enum}

::: starlette_admin.filters.enum.InFilter

::: starlette_admin.filters.enum.NotInFilter

## ऐरे {#array}

::: starlette_admin.filters.array.InFilter

::: starlette_admin.filters.array.NotInFilter
