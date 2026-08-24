---
title: विजेट्स API संदर्भ
description: starlette-admin में डैशबोर्ड और फ़ॉर्म-लेआउट विजेट्स के लिए संपूर्ण API
  संदर्भ।
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/api/widgets/)
<!-- translation-notice:end -->

# विजेट्स {#widgets}

विजेट सिस्टम के लिए पूर्ण एट्रिब्यूट और मेथड संदर्भ, जो docstrings से जेनरेट किया गया है। कार्य-उन्मुख
मार्गदर्शन के लिए [कस्टम व्यू और विजेट](../user-guide/custom-views.md) और
[फ़ॉर्म लेआउट](../advanced/form-layout.md) देखें।

विजेट, कंपोज़ किए जा सकने वाले और रेंडर हो सकने वाले बिल्डिंग ब्लॉक हैं जिनका उपयोग UI एलिमेंट को डायनैमिक रूप से बनाने के लिए किया जाता है। नीचे सूचीबद्ध हर विजेट क्लास को सीधे `starlette_admin` से इंपोर्ट किया जा सकता है।

विजेट सिस्टम संदर्भ के अनुसार दो प्रमुख भूमिकाएँ निभाता है:

* **डैशबोर्ड और कस्टम पेज:** स्टैंडअलोन इंटरफ़ेस और मेट्रिक बोर्ड बनाने के लिए [`CustomView`](views.md#starlette_admin.views.CustomView) के `widget` एट्रिब्यूट के रूप में उपयोग किए जाते हैं।
* **फ़ॉर्म लेआउट:** create/edit फ़ॉर्म पर इनपुट को व्यवस्थित और समूहित करने के लिए [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) के `form_layout` एट्रिब्यूट के रूप में उपयोग किए जाते हैं।

---

## बेस क्लास {#base-class}

सभी विजेट एक साझा बेस क्लास से इनहेरिट होते हैं, जो स्टैंडर्ड रेंडरिंग और एसेट-कलेक्शन इंटरफ़ेस परिभाषित करता है।

::: starlette_admin.widgets.BaseWidget

---

## कंटेंट विजेट {#content-widgets}

कंटेंट विजेट आपके UI ट्री की लीफ़ नोड्स की तरह काम करते हैं। अन्य विजेट रखने के बजाय ये लाइव डेटा दिखाते हैं। प्रत्येक कंटेंट विजेट एक एसिंक्रोनस कॉलबैक स्वीकार करता है, जो प्रति रिक्वेस्ट एक बार कॉल होता है, जिससे रेंडर किए गए मान हमेशा अद्यतित रहते हैं।

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## लेआउट विजेट {#layout-widgets}

लेआउट विजेट कंटेनर होते हैं जिनका उपयोग उनके `children` (जो कंटेंट विजेट, फ़ॉर्म फ़ील्ड, या अन्य लेआउट विजेट हो सकते हैं) को व्यवस्थित करने के लिए किया जाता है।

**स्वचालित एसेट मैनेजमेंट:** लेआउट विजेट अपने ट्री को रिकर्सिव रूप से ट्रैवर्स करके अपने children से `additional_css_links` और `additional_js_links` कलेक्ट करते हैं। इससे गहराई तक नेस्ट किए गए कंपोनेंट्स भी बिना किसी मैन्युअल वायरिंग के अपनी आवश्यक CSS/JS एसेट स्वतः लोड कर लेते हैं।

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## रिस्पॉन्सिव साइज़िंग {#responsive-sizing}

विभिन्न स्क्रीन साइज़ पर रिस्पॉन्सिव ग्रिड व्यवहार, कॉलम चौड़ाई और ब्रेकपॉइंट मैनेज करने के लिए समर्पित यूटिलिटी क्लासेस।

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## फ़ॉर्म लेआउट रेफ़रेंस {#form-layout-references}

मॉडल फ़ॉर्म के संदर्भ में विशिष्ट डेटाबेस फ़ील्ड को रेफ़र करने के लिए विशेष रूप से उपयोग किए जाने वाले विजेट।

::: starlette_admin.widgets.FieldRef

---

## शॉर्टहैंड और नॉर्मलाइज़ेशन {#shorthand-normalization}

आपके लेआउट कोड को साफ़ और अत्यधिक पठनीय रखने के लिए, कंटेनर विजेट स्पष्ट विजेट क्लास इंस्टैंटिएशन के स्थान पर साधारण Python प्रकार स्वीकार करते हैं। इनिशियलाइज़ेशन (`__post_init__`) के दौरान कंटेनर इन शॉर्टहैंड मानों को स्वतः उनके संबंधित विजेट में बदल देते हैं।

**समर्थित शॉर्टहैंड:**

* `str`: फ़ील्ड रेफ़रेंस (`FieldRef`) में बदलता है।
* `tuple`: साइड-बाय-साइड रो (`RowWidget`) में बदलता है।
* `list`: वर्टिकल स्टैक (`ColumnWidget`) में बदलता है।

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## हेल्पर {#helpers}

Jinja2 टेम्पलेट या कस्टम कॉन्टेक्स्ट के भीतर विजेट रेंडर करने के लिए यूटिलिटी फ़ंक्शन।

::: starlette_admin.widgets.render_widget
