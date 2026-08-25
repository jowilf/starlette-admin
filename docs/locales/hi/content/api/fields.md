---
title: फ़ील्ड्स API संदर्भ
description: starlette-admin में उपलब्ध सभी फ़ील्ड प्रकारों के लिए API संदर्भ दस्तावेज़।
source_hash: 79eba140a93083b5b94b39d6496d16d9703d48140b5290383927e0ee28325836
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/fields/)
<!-- translation-notice:end -->

# फ़ील्ड्स {#fields}

`BaseField` और हर बिल्ट-इन फ़ील्ड प्रकार के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो
docstrings से जेनरेट किया गया है। कार्य-उन्मुख मार्गदर्शन के लिए [फ़ील्ड्स](../user-guide/fields.md) देखें।

## बेस क्लास {#base-class}

::: starlette_admin.fields.BaseField

## टेक्स्ट {#text}

::: starlette_admin.fields.StringField

::: starlette_admin.fields.TextAreaField

::: starlette_admin.fields.TinyMCEEditorField

::: starlette_admin.fields.EmailField

::: starlette_admin.fields.URLField

::: starlette_admin.fields.PhoneField

::: starlette_admin.fields.ColorField

::: starlette_admin.fields.PasswordField

::: starlette_admin.fields.UUIDField

::: starlette_admin.fields.IPAddressField

::: starlette_admin.fields.SlugField

## संख्याएँ {#numbers}

::: starlette_admin.fields.NumberField

::: starlette_admin.fields.IntegerField

::: starlette_admin.fields.DecimalField

::: starlette_admin.fields.FloatField

## बूलियन {#boolean}

::: starlette_admin.fields.BooleanField

## दिनांक और समय {#dates-and-times}

::: starlette_admin.fields.DateTimeField

::: starlette_admin.fields.DateField

::: starlette_admin.fields.TimeField

::: starlette_admin.fields.ArrowField

## विकल्प {#choices}

::: starlette_admin.fields.EnumField

::: starlette_admin.fields.TimeZoneField

::: starlette_admin.fields.CountryField

::: starlette_admin.fields.CurrencyField

::: starlette_admin.fields.TagsField

## संरचित डेटा {#structured-data}

::: starlette_admin.fields.JSONField

::: starlette_admin.fields.CollectionField

::: starlette_admin.fields.ListField

::: starlette_admin.fields.ComputedField

## फ़ाइलें {#files}

::: starlette_admin.fields.FileField

::: starlette_admin.fields.ImageField

## रिलेशन {#relations}

::: starlette_admin.fields.RelationField

::: starlette_admin.fields.HasOne

::: starlette_admin.fields.HasMany
