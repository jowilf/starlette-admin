---
title: कस्टम फ़िल्टर
description: starlette-admin में कस्टम डेटाबेस फ़िल्टर और ऑपरेटर बनाकर इनबिल्ट क्वेरी
  बिल्डर को बढ़ाएं।
source_hash: ac118a53b1d95372b17388cb1ce13241e53cd4b2983158208affa0fedb2e2446
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/advanced/custom-filters/)
<!-- translation-notice:end -->

# कस्टम फ़िल्टर {#custom-filters}

जब आपको कोई ऐसा ऑपरेटर चाहिए जो इनबिल्ट सेट में न हो — कोई domain-specific जाँच जैसे "_is divisible by_", कोई computed शर्त जैसे "_created this month_", या किसी ऐसे फ़ील्ड टाइप का समर्थन जिसे डिफ़ॉल्ट रजिस्ट्री छोड़ देती है — तब `BaseFilter` को सबक्लास करें। यह पेज समझाता है कि कोई फ़िल्टर भीतर से कैसे काम करता है, और उसे रजिस्टर करने के दो तरीक़े दिखाता है: या तो अपने बैकएंड की `FilterRegistry` को सबक्लास करके, जिससे वह हर मेल खाते फ़ील्ड टाइप पर लागू हो, या फ़िल्टर को किसी एक फ़ील्ड की `filters=` लिस्ट में पास करके। रोज़मर्रा के विवरणों के लिए — जिनमें प्रति फ़ील्ड टाइप डिफ़ॉल्ट फ़िल्टर, मैन्युअल ओवरराइड, और URL फ़ॉर्मैट शामिल हैं — [फ़िल्टर गाइड](../user-guide/filters.md) देखें।

## `BaseFilter` इंटरफ़ेस {#the-basefilter-interface}

हर फ़िल्टर, चाहे इनबिल्ट हो या कस्टम, दो मेथड इम्प्लीमेंट करता है:

```python
from typing import Any
from starlette_admin.filters.base import BaseFilter, FilterApplyContext, FilterDataType


class MyFilter(BaseFilter):
    name = "my_filter"
    label = "My filter"
    data_type = FilterDataType.STRING

    def parse_value(self, raw: str) -> Any:
        """Convert the raw string from the URL into the value apply() expects.

        Raise FilterValidationError if the value isn't acceptable.
        """
        return raw

    def apply(self, ctx: FilterApplyContext) -> Any:
        """Return a query fragment for this filter's condition."""
        raise NotImplementedError()
```

* **`parse_value(raw)`** रॉ URL स्ट्रिंग को उस टाइप में बदलता है जिसकी `apply()` अपेक्षा करता है — जैसे `Decimal`, `date`, या कोई list। डिफ़ॉल्ट स्ट्रिंग को बिना बदले पास कर देता है, जो `STRING` और `ENUM` फ़िल्टर के लिहाज़ से ठीक है लेकिन संख्यात्मक या तारीख़/समय वाले डेटा के लिए नहीं। यही आपका सत्यापन हुक भी है: ऐसी वैल्यू के लिए `FilterValidationError` रेज़ करें जो पार्स तो हो जाएँ लेकिन फिर भी स्वीकार्य न हों — जैसे रेंज से बाहर या ग़लत फ़ॉर्मैट वाला इनपुट।
* **`apply(ctx)`** एकमात्र ऐब्स्ट्रैक्ट मेथड है। इसे एक `FilterApplyContext` मिलता है जिसमें `query`, `field_name`, `value`, `value2`, `request`, और `view` होते हैं, और यह आपके बैकएंड के लिए एक क्वेरी फ़्रैगमेंट लौटाता है।

## रॉ URL वैल्यू कैसे पार्स होती हैं {#how-raw-url-values-get-parsed}

हर URL पैरामीटर एक स्ट्रिंग होता है, इसलिए `price__gt=50` और `created_at__eq=2026-01-01` दोनों रॉ टेक्स्ट की शक्ल में आते हैं। `apply()` चलने से पहले `parse_value()` उस स्ट्रिंग को फ़िल्टर के `data_type` से मेल खाती Python ऑब्जेक्ट में बदल देता है:

```python
def _parse_number(raw: Any) -> int | float:
    text = str(raw).strip()
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        raise FilterValidationError(f"{raw!r} is not a valid number") from None


class GreaterThanFilter(BaseFilter):
    name = "gt"
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: Any) -> int | float:
        return _parse_number(raw)
```

इस तरह `?filter=price__gt=50` और `?filter=price__gt=50.5`, `GreaterThanFilter.apply()` तक `"50"` और `"50.5"` स्ट्रिंगों की बजाय Python संख्याओं (`int` के तौर पर `50`, `float` के तौर पर `50.5`) की तरह पहुँचते हैं। `apply()` वह पार्स की हुई वैल्यू सीधे क्वेरी ऑब्जेक्ट को पास कर देता है, और आख़िरी coercion कॉलम के असली टाइप (जैसे `Decimal` या `Numeric`) के हिसाब से डेटाबेस ड्राइवर संभाल लेता है।

| `data_type` | रॉ URL वैल्यू का उदाहरण | पार्स हुई Python वैल्यू | पार्स किसने किया |
| --- | --- | --- | --- |
| `number` | `50`, `-3`, `50.5` | `int(50)`, `int(-3)`, `float(50.5)` | `filters.numeric._parse_number` (`int()` आज़माता है, न मिले तो `float()`) |
| `date` | `2026-01-01` | `date(2026, 1, 1)` | `filters.date._parse_temporal`, `date.fromisoformat()` के साथ |
| `datetime` | `2026-01-01T14:30:00` | `datetime(2026, 1, 1, 14, 30)` | `filters.date._parse_temporal`, `datetime.fromisoformat()` के साथ |
| `time` | `14:30:00` | `time(14, 30)` | `filters.date._parse_temporal`, `time.fromisoformat()` के साथ |
| `array` | `ACTIVE,OUT_OF_STOCK` | `["ACTIVE", "OUT_OF_STOCK"]` | `filters.array._parse_array` (बिना कोट वाले कॉमा पर विभाजित करता है) |
| `string`, `enum` | `admin` | `"admin"` | `BaseFilter.parse_value` डिफ़ॉल्ट (बिना बदले पास होती है) |
| `none` | *(URL में कोई वैल्यू ही नहीं)* | *(कभी कॉल नहीं होता)* | N/A |

जब कोई वैल्यू पार्स होने में नाकाम रहती है — जैसे `price__gt=abc` या `created_at__eq=not-a-date` — तो `parse_value()` एक `FilterValidationError` रेज़ करता है। रिक्वेस्ट हैंडर उसे पकड़ लेता है और कोई भी डेटाबेस क्वेरी चलाने से पहले `HTTP 400` लौटा देता है:

```text
GET /admin/product/list?filter=price__gt=abc
Returns: 400 Bad Request: Invalid 'filter' parameter: 'abc' is not a valid number

```

बिना वैल्यू वाले फ़िल्टर, यानी जिनका `data_type=none` है — जैसे `is_null`, `is_true`, या `in_past` — इस चरण को छोड़ देते हैं। इनके लिए `parse_value` कभी चलता ही नहीं; इसीलिए `field__is_null` के लिए URL में `=value` की ज़रूरत नहीं होती: बदलने को कोई इनपुट स्ट्रिंग होती ही नहीं।

## कस्टम फ़िल्टर उपलब्ध कराना {#making-a-custom-filter-available}

आप किसी व्यू के साथ कस्टम फ़िल्टर दो तरीक़ों से रजिस्टर कर सकते हैं। अपनी चाही हुई दायरे (scope) से मेल खाता तरीक़ा चुनें।

### प्रति फ़ील्ड इंस्टेंस (सीमित scope) {#per-field-instance-narrow-scope}

फ़िल्टर को टारगेट फ़ील्ड की `filters=` लिस्ट में पास करें — डिफ़ॉल्ट के साथ या उनकी जगह। इनबिल्ट फ़िल्टर के साथ इसी पैटर्न के लिए [किसी ख़ास फ़ील्ड के फ़िल्टर ओवरराइड करना](../user-guide/filters.md#overriding-filters-for-a-specific-field) देखें। जब फ़िल्टर केवल एक ही फ़ील्ड के लिए मायने रखता हो, तब इसका इस्तेमाल करें।

### रजिस्ट्री-व्यापी (हर मेल खाता फ़ील्ड टाइप) {#registry-wide-every-matching-field-type}

हर बैकएंड एक `FilterRegistry` सबक्लास के साथ आता है: SQLAlchemy के लिए `SqlaFilterRegistry`, Beanie के लिए `BeanieFilterRegistry`, MongoEngine के लिए `MongoEngineFilterRegistry`, और Tortoise ORM के लिए `TortoiseFilterRegistry`। हर एक, किसी सपोर्टेड फ़ील्ड टाइप के डिफ़ॉल्ट फ़िल्टर एक ऐसी मेथड में तय करता है जिस पर `@filters(FieldType, ...)` डेकोरेटर लगा हो:

```python
# starlette_admin/contrib/sqla/filters.py
class SqlaFilterRegistry(FilterRegistry):
    @filters(StringField)
    def string_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            ContainsFilter,
            NotContainsFilter,
            EqualFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    @filters(NumberField, FloatField)
    def numeric_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [
            NumericEqualFilter,
            GreaterThanFilter,
            LessThanFilter,
            IsNullFilter,
            IsNotNullFilter,
        ]

    # ... one method per field type
```

किसी पूरे व्यू में किसी फ़ील्ड टाइप के लिए उपलब्ध फ़िल्टर बदलने के लिए, बैकएंड की रजिस्ट्री को सबक्लास करें, कोई `@filters` मेथड ओवरराइड या जोड़ें, और `get_filter_registry()` से अपने सबक्लास का इंस्टेंस लौटाएं:

```python
class ProductFilterRegistry(SqlaFilterRegistry):
    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    def get_filter_registry(self) -> FilterRegistry:
        return ProductFilterRegistry()
```

ये मेथड दो तरीक़ों में से किसी एक से घोषित करें, इस पर निर्भर करते हुए कि आप मौजूदा फ़िल्टर को बदलना चाहते हैं या उनमें जोड़ना चाहते हैं:

* **ओवरराइड:** अपने सबक्लास पर `@filters(StringField)` दोबारा घोषित करें और ठीक वही क्लास लौटाएं जो आप चाहते हैं। इससे पैरेंट की लिस्ट बदल जाती है, इसलिए जो इनबिल्ट फ़िल्टर आप रखना चाहते हैं उन्हें शामिल करें।
* **एक्सटेंड:** `@filters(IntegerField)` तब घोषित करें जब पैरेंट रजिस्ट्री केवल व्यापक `NumberField` ही रजिस्टर करती हो। चूँकि `IntegerField`, `NumberField` का सबक्लास है, मेथड रेज़ोल्यूशन ऑर्डर (MRO) `IntegerField` को आपकी नई मेथड तक पहुँचा देता है, जबकि `DecimalField` — जो भी एक `NumberField` सबक्लास है लेकिन खुद का कोई रजिस्ट्रेशन नहीं रखता — पैरेंट का `numeric_filters` बिना बदलाव इनहेरिट करता रहता है।

यह एक साधारण Python सबक्लास है, इसलिए यह कोई ग्लोबल स्टेट नहीं बदलता। `ProductFilterRegistry()` का हर कॉल एक स्वतंत्र रजिस्ट्री बनाता है, और आपके बदलाव उन्हीं व्यू तक सीमित रहते हैं जो उसे लौटाते हैं। बाक़ी सभी व्यू बैकएंड के डिफ़ॉल्ट ही रखते हैं।

## पूरा SQLAlchemy उदाहरण {#full-sqlalchemy-example}

नीचे दिया `DivisibleByFilter` एक वैल्यू लेता है — वह divisor जिसके विरुद्ध कॉलम की जाँच होगी। `SqlaFilterRegistry` का एक सबक्लास इसे अलग-अलग फ़ील्ड पर लगाने के बजाय `ProductView` के हर `IntegerField` पर लागू करता है:

```python
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from decimal import Decimal
from typing import Any

from fastapi import FastAPI
from sqlalchemy import Integer, Numeric, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette.requests import Request
from starlette_admin import IntegerField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.contrib.sqla.filters import SqlaFilterRegistry
from starlette_admin.fields import BaseField
from starlette_admin.filters import (
    BaseFilter,
    FilterApplyContext,
    FilterDataType,
    FilterRegistry,
    FilterValidationError,
    filters,
)

engine = create_engine(
    "sqlite:///product.db", connect_args={"check_same_thread": False}, echo=True
)


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str]
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    lot_size: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)

    async def __admin_repr__(self, request: Request) -> str:
        return self.name


class DivisibleByFilter(BaseFilter):
    """
    Filters database rows where the column value is an exact multiple of a given divisor.
    """

    name = "divisible_by"
    label = "Is divisible by"
    data_type = FilterDataType.NUMBER

    def parse_value(self, raw: str) -> int:
        """Validates and converts the raw admin UI input into an integer divisor."""
        try:
            divisor = int(raw)
        except ValueError:
            raise FilterValidationError(f"{raw!r} is not a valid integer") from None

        if divisor == 0:
            raise FilterValidationError("divisor must not be 0")

        return divisor

    def apply(self, ctx: FilterApplyContext) -> Any:
        """Applies the modulus condition to the underlying SQLAlchemy query context."""
        column = getattr(ctx.view.model, ctx.field_name)
        return column % ctx.value == 0


class ProductFilterRegistry(SqlaFilterRegistry):
    """
    Custom filter registry that injects `DivisibleByFilter` into integer fields.

    Overriding `integer_filters` gives every IntegerField the divisibility filter
    on top of the standard numeric defaults. Other numeric fields, such as
    DecimalField, are unaffected.
    """

    @filters(IntegerField)
    def integer_filters(self, field: BaseField) -> list[type[BaseFilter]]:
        return [*self.numeric_filters(field), DivisibleByFilter]


class ProductView(ModelView):
    fields = [
        "id",
        "name",
        "price",
        # Note: Passing just the string "lot_size" would also work, as SQLAlchemy's
        # default converter automatically maps integer columns to IntegerField.
        IntegerField("lot_size"),
    ]

    def get_filter_registry(self) -> FilterRegistry:
        """Binds the custom filter registry to this specific view."""
        return ProductFilterRegistry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Blog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-product"))
admin.mount_to(app)
```

एक चलाने योग्य ऐप के लिए [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) देखें, जिसमें कस्टम `BaseFilter` सबक्लास इसी तरह रजिस्टर किया गया है।

अब `lot_size__divisible_by` विकल्प `IntegerField("lot_size")` के लिए एक फ़िल्टर के रूप में दिखता है, बिना फ़ील्ड पर कोई स्पष्ट `filters=` घोषणा किए। उदाहरण के लिए, `lot_size__divisible_by=6` उन प्रोडक्ट से मेल खाता है जिनका lot size 6 का गुणज है:

```text
http://127.0.0.1:8000/admin/product/list?filter=lot_size__divisible_by=6&sort=id__asc
```

!!! tip
    किसी फ़िल्टर को `FilterRegistry` सबक्लास के रूप में तब इस्तेमाल करें जब वह किसी व्यू में किसी दिए गए टाइप के हर फ़ील्ड पर लागू होने लायक़ जेनेरिक हो। प्रति-फ़ील्ड `filters=` लिस्ट तब इस्तेमाल करें जब लॉजिक केवल एक ही फ़ील्ड से जुड़ा हो। [फ़िल्टर गाइड](../user-guide/filters.md#overriding-filters-for-a-specific-field) में प्रति-फ़ील्ड पैटर्न के उदाहरण हैं।

## `get_choices` के साथ डायनामिक choices {#dynamic-choices-with-get_choices}

डिफ़ॉल्ट रूप से, फ़िल्टर का वैल्यू इनपुट उसके `data_type` के मुताबिक़ होता है: `STRING` के लिए एक साधारण टेक्स्ट बॉक्स, `NUMBER` के लिए नंबर बॉक्स, और इसी तरह। जब वैल्यू किसी ऐसे ड्रॉपडाउन से आनी हो जो `(value, label)` जोड़ों की प्रति-रिक्वेस्ट लिस्ट से भरा जाता है, तब `get_choices(request)` को ओवरराइड करें। किसी relation फ़ील्ड पर "is one of" फ़िल्टर इसका सामान्य उदाहरण है: पोस्ट होने वाली वैल्यू एक फ़ॉरेन key होती है, लेकिन पिकर को एक पढ़ने-योग्य नाम दिखाना चाहिए।

`get_choices` को मौजूदा `Request` मिलता है और वह `(value, label)` जोड़ों की एक sequence लौटाता है, या `None` (डिफ़ॉल्ट) — जिस स्थिति में साधारण इनपुट ज्यों-का-त्यों रहता है। ग़ैर-खाली नतीजा साधारण इनपुट और फ़ील्ड के अपने दिए गए choices (जैसा `EnumField` करता है) — दोनों पर भारी पड़ता है।

नीचे का उदाहरण — [examples/advanced/07-hr](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/07-hr) से लिया गया — `Employee` लिस्ट के `department` फ़ील्ड में "is one of" और "is not one of" का जोड़ा जोड़ता है। `department` एक `RelationField` है, इसलिए डिफ़ॉल्ट रजिस्ट्री उसे केवल null जाँचें ही देती है: किसी संबंधित row की तुलना किसी रॉ स्ट्रिंग से करने का कोई जेनेरिक तरीक़ा नहीं होता। `get_choices` ड्रॉपडाउन के लिए हर `Department` को नाम से सूचीबद्ध करता है, और `parse_value` पोस्ट हुई वैल्यू को पूर्णांकों में बदल देता है ताकि `apply` relationship के ज़रिए join करके नामों की तुलना करने की बजाय सीधे `Department.id` फ़ॉरेन key पर मेल खा सके:

```python
# examples/advanced/07-hr/filters.py
from typing import Any

from models import Department, Employee
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette_admin.filters.base import FilterApplyContext, FilterValidationError
from starlette_admin.filters.enum import InFilter, NotInFilter


class _DepartmentChoicesMixin:
    """Shared `get_choices`/`parse_value` for the two filters below: the
    filter builder's dropdown lists every department by name, and posts back
    the department's `id` rather than its name, so `apply` can match on the
    primary key instead of an `ilike` comparison.
    """

    def get_choices(self, request: Request) -> list[tuple[int, str]]:
        session: Session = request.state.session
        return list(
            session.execute(
                select(Department.id, Department.name).order_by(Department.name)
            ).all()
        )

    def parse_value(self, raw: Any) -> list[int]:
        values = super().parse_value(raw)  # type: ignore[misc]
        try:
            return [int(v) for v in values]
        except ValueError as err:
            raise FilterValidationError("Department id must be an integer") from err


class DepartmentInFilter(_DepartmentChoicesMixin, InFilter):
    """Employees in one of the selected departments."""

    name = "department_in"
    label = "is one of"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return Employee.department_id.in_(ctx.value)


class DepartmentNotInFilter(_DepartmentChoicesMixin, NotInFilter):
    """Employees not in any of the selected departments"""

    name = "department_not_in"
    label = "is not one of"

    def apply(self, ctx: FilterApplyContext) -> Any:
        return ~Employee.department_id.in_(ctx.value)
```

इस पैटर्न के बारे में ध्यान देने योग्य कुछ बातें:

* **मिक्सिन MRO में बेस फ़िल्टर क्लास से पहले आता है।** `class DepartmentInFilter(_DepartmentChoicesMixin, InFilter)` में `_DepartmentChoicesMixin` पहले है, इसलिए उसके `get_choices` और `parse_value` उन मेथड को ओवरराइड कर देते हैं जिन्हें हर फ़िल्टर अन्यथा इनहेरिट करता। `super().parse_value(raw)` अब भी `InFilter.parse_value` तक पहुँचता है, जो रॉ वैल्यू को list में तोड़ता है, और फिर मिक्सिन उसे पूर्णांकों में बदलता है।
* **`get_choices` हर रिक्वेस्ट पर चलता है**, इंपोर्ट के समय सिर्फ़ एक बार नहीं, इसलिए ड्रॉपडाउन हमेशा मौजूदा rows को दर्शाता है। नया जोड़ा गया `Department` फ़िल्टर बिल्डर में तुरंत दिख जाता है — न सर्वर रीस्टार्ट की ज़रूरत, न अमान्य करने को कोई कैश।
* **`(value, label)` जोड़े और `parse_value` का आउटपुट टाइप आपस में मेल खाने चाहिए।** ड्रॉपडाउन वही `value` वापस पोस्ट करता है जिसे यूज़र ने चुना, इसलिए `parse_value` उसे उस रूप में बदलता है जिसकी `apply` अपेक्षा करता है। यहाँ `Department.id` पहले से ही `int` है, इसलिए मिक्सिन का `parse_value` इसे दोहराता है और किसी और चीज़ पर सत्यापन त्रुटि रेज़ करता है।
* **`InFilter` और `NotInFilter` पहले से ही `data_type = FilterDataType.ENUM` पर डिफ़ॉल्ट हैं**, यानी multi-select, इसलिए दोनों सबक्लास को `data_type` ओवरराइड की ज़रूरत नहीं। `get_choices` को ओवरराइड करना ही काफ़ी है ताकि वह multi-select ख़ाली छोड़ने के बजाय departments से भर जाए।

---

## आगे क्या {#whats-next}

* **[फ़िल्टर](../user-guide/filters.md):** फ़ील्ड टाइप के हिसाब से डिफ़ॉल्ट फ़िल्टर, URL फ़ॉर्मैट, और `filters=` ओवरराइड के बारे में जानें।
* **[SQLAlchemy](../integrations/sqlalchemy.md):** इस पेज के उदाहरण में इस्तेमाल हुआ SQLAlchemy बैकएंड देखें।
* **[एक्सटेंशन पॉइंट](extension-points.md):** `ModelView` पर ओवरराइड किए जा सकने वाले मेथड की पूरी सूची देखें।
