---
title: इवेंट्स API संदर्भ
description: starlette-admin में इवेंट सिस्टम और हुक के लिए API संदर्भ दस्तावेज़।
source_hash: 38b33892f675bf13798c334f941f806a503dc542816e56e5593ee7eb99103312
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/events/)
<!-- translation-notice:end -->

# इवेंट्स {#events}

इवेंट सिस्टम के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो docstrings से जेनरेट किया गया है। कार्य-उन्मुख
मार्गदर्शन के लिए [इवेंट्स](../advanced/events.md) देखें।

## इवेंट बस {#event-bus}

::: starlette_admin.events.AdminEventBus

::: starlette_admin.events.EventBus

::: starlette_admin.events.AdminEventSubscriber

::: starlette_admin.events.on

::: starlette_admin.events.AdminEvent

## इवेंट कॉन्टेक्स्ट {#event-contexts}

::: starlette_admin.events.EventContext

::: starlette_admin.events.BeforeCreateContext

::: starlette_admin.events.AfterCreateContext

::: starlette_admin.events.BeforeEditContext

::: starlette_admin.events.AfterEditContext

::: starlette_admin.events.BeforeDeleteContext

::: starlette_admin.events.AfterDeleteContext

::: starlette_admin.events.BeforeBulkDeleteContext

::: starlette_admin.events.AfterBulkDeleteContext

::: starlette_admin.events.BeforeActionContext

::: starlette_admin.events.AfterActionContext

::: starlette_admin.events.BeforeExportContext

::: starlette_admin.events.AfterExportContext

::: starlette_admin.events.BeforeImportContext

::: starlette_admin.events.AfterImportContext

::: starlette_admin.events.AfterLoginContext
