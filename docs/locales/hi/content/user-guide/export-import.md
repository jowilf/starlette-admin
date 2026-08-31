---
title: एक्सपोर्ट और इंपोर्ट
description: starlette-admin में CSV, JSON, और PDF export functionality सक्षम करें
  तथा validation के साथ bulk data imports चलाएँ।
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
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

    [मूल अंग्रेज़ी संस्करण पढ़ें](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# एक्सपोर्ट और इंपोर्ट {#export-and-import}

हर लिस्ट पेज users को data को file में एक्सपोर्ट और file से इंपोर्ट करने देता है, इसलिए आपको custom routes लिखने नहीं पड़ते।

## Overview

* **Export:** Users toolbar button select करते हैं, फिर scope, fields, format, और filename सेट करते हैं।
* **Import:** Users toolbar button से एक three-step wizard खोलते हैं: upload, preview, और results.
* **Formats:** CSV, JSON, XLSX, ODS, YAML, PDF, और custom formats box से बाहर supported हैं।
* **Upsert:** Imports optionally primary key से matched existing records update कर सकते हैं।
* **Integration:** दोनों features filtering, sorting, row selection, और storage-backed fields के साथ काम करते हैं।
* **No extra endpoints:** सब कुछ view के साथ ही ship होता है।

## Minimal example

```python hl_lines="23 24"
from sqlalchemy import Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin.contrib.sqla import Admin, ModelView

engine = create_engine("sqlite:///store.sqlite")


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column()


class ProductView(ModelView):
    fields = ["id", "name", "description", "price"]
    exporters = ["csv", "xlsx", "json"]
    importers = ["csv", "xlsx"]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Store Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

`ProductView` अब list toolbar में **Export** और **Import** button दिखाता है। प्रत्येक dialog ठीक वही formats offer करता है जो आपने `exporters` और `importers` में listed किए हैं।

---

## Export सक्षम करना {#enabling-export}

`exporters` attribute expose किए जाने वाले formats की list है — plain extension strings के रूप में:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]
```

डिफ़ॉल्ट `["csv", "json"]` है। नीचे की table हर built-in format और उसे चाहिए package list करती है। `csv`, `tsv`, और `json` formats को extra dependencies नहीं चाहिए। बाकी हर tabular format `tablib` उपयोग करता है, और `pdf` `reportlab`. अज्ञात format string, या जिसका package इंस्टॉल नहीं है, startup पर error raise करता है।

| Format | Install requirement |
| --- | --- |
| `csv`, `tsv`, `json` | Included in core |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Format options override करना {#overriding-format-options}

हर format string sensible defaults वाले preconfigured exporter instance में resolve होता है। जब किसी format को अलग settings चाहिए, string के बजाय exporter instance pass करें। उसी list में strings और instances mix कर सकते हैं:

```python hl_lines="5"
from starlette_admin.export import CsvExporter


class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]
```

`CsvExporter` keyword arguments `csv.writer` को forward करता है और `escape_formulas` parameter स्वीकार करता है। `TablibExporter(format, **kwargs)` हर tablib format cover करता है और keyword arguments `tablib.Dataset.export()` को forward करता है।

!!! warning
    Formula escaping डिफ़ॉल्ट रूप से बंद रहती है। यदि exported fields user-supplied strings contain कर सकती हैं, तो formula injection रोकने के लिए `CsvExporter`, `TsvExporter`, या `TablibExporter` पर `escape_formulas=True` सेट करें — अन्यथा कोई spreadsheet application में file खोलते ही injection हो सकता है। [Formula injection](security.md#formula-injection) देखें।

Export डिफ़ॉल्ट रूप से चालू रहता है। `exporters` list गैर-खाली होते ही toolbar में **Export** button दिखता है। यह restrict करने के लिए कौन export कर सकता है, `can_export(request)` method override करें:

```python hl_lines="5 6"
from starlette.requests import Request


class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"
```

### Export dialog {#the-export-dialog}

Export एक built-in global action है। **Export** select करने पर एक dialog खुलता है जहाँ user download से पहले export set up करता है।

* **Scope:** क्या export करना है। Options हैं: "Selected rows" — rows checked होने पर default, "All matching rows" — select-all banner से उपलब्ध, और "Current page" — कुछ selected न होने पर default.
* **Fields:** प्रत्येक exportable field के लिए एक checkbox। Checkbox clear करने पर वह column drop हो जाता है। `exclude_from_export=True` वाले fields यहाँ कभी नहीं दिखते।
* **Format:** `exporters` के हर format के लिए एक entry.
* **Filename:** Default view key होता है। Server file extension append करता है।

हर scope list page के current search, filters, और sort order का सम्मान करता है — यानी user जो देखता है, वही export होता है।

### Row cap {#the-row-cap}

```python
from starlette_admin.export import ExportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    export_config=ExportConfig(max_rows=50_000),
)
```

`ExportConfig.max_rows` का default 100,000 है। Cap उन rows की संख्या पर लागू होता है जो चुना गया scope वास्तव में produce करेगा, और admin कोई row fetch करने से पहले count check करता है। Count limit पार करने पर admin error flash करके file generate करने के बजाय list page पर redirect कर देता है। इससे large table पर broad, unfiltered export request hang नहीं करता। Limit हटाने के लिए `max_rows=None` सेट करें।

---

## Import सक्षम करना {#enabling-import}

`importers` attribute ठीक `exporters` की तरह काम करता है और format strings स्वीकार करता है:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]
```

Built-in import formats हैं: `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf`, और `html` — export counterparts की जैसी ही dependencies। किसी format के defaults override करने के लिए importer instance pass करें, जैसे `starlette_admin.importers` से `CsvImporter(delimiter=";")`.

Import डिफ़ॉल्ट रूप से चालू रहता है, `["csv", "json"]` के साथ। `importers` list गैर-खाली होते ही toolbar में **Import** button दिखता है। यह restrict करने के लिए कौन import कर सकता है, `can_import(request)` method override करें:

```python hl_lines="5 6"
from starlette.requests import Request


class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"
```

### Import wizard {#the-import-wizard}

**Import** select करने पर एक three-step wizard खुलता है। Final confirmation से पहले database में कुछ भी नहीं लिखा जाता, और steps के बीच server पर कोई file store नहीं होती: browser file को hold करता है और हर step पर उसे फिर post करता है।

1. **Upload:** Format चुनें, file चुनें, और optionally **Update existing records by primary key** select करें। यह select करने पर जिस row की primary key किसी existing record से match करती है, वह नया record बनाने के बजाय उस record को update करती है। अन्यथा हर row create होती है।
2. **Preview:** Upload submit करने पर कुछ भी लिखे बिना पूरा validation pass चलता है। Wizard summary, column mappings, sample rows, और detailed error table दिखाता है।
3. **Result:** Wizard import commit करता है और created, updated, और skipped records के final counts report करता है। Preview में validation fail हुई rows skip हो जाती हैं।

!!! tip
    Backend से primary keys generate करवाने के लिए preview mapping में primary key column clear कर दें। Imported rows फिर कोई key value carry नहीं करतीं, इसलिए आपके exported file का reimport stale IDs पर fail होने के बजाय fresh records बनाता है।

### Upload और row caps {#upload-and-row-caps}

```python
from starlette_admin.importers import ImportConfig
from starlette_admin.contrib.sqla import Admin

admin = Admin(
    engine,
    title="Store Admin",
    secret_key="change-me",
    import_config=ImportConfig(max_rows=50_000),
)
```

Import endpoint export row cap का mirror है। `ImportConfig.max_rows` का default 100,000 है और कोई record बनने से पहले enforce होता है। Admin uploaded file को pre-pass में count करता है और cap से अधिक rows वाली file को HTTP 400 error के साथ reject कर देता है। Limit हटाने के लिए `max_rows=None` सेट करें। `ImportConfig.max_upload_size` भी uploads को default रूप से 10 MB पर cap करता है।

### Header matching

Wizard हर file header को पहले आपके field के `label` से match करता है, फिर उसके `name` से। Column `Name` वाली file और column `name` वाली file दोनों `name` field से map होती हैं। Unmatched columns ignore होते हैं, और matching column विहीन fields को `None` मिलता है।

## File fields

Storage-backed `FileField` या `ImageField` वाला view ZIP archive के रूप में export होता है, ताकि file contents row data के साथ चलें:

```python
from sqlalchemy import Integer, JSON, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///catalog.sqlite")
covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")


class Base(DeclarativeBase):
    pass


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    photo: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class ProductView(ModelView):
    fields = [
        "id",
        "name",
        ImageField("photo", storage=covers_storage, upload_folder="products"),
    ]


Base.metadata.create_all(engine)
admin = Admin(engine, title="Catalog Admin", secret_key="change-me")
admin.add_view(ProductView(Product, icon="fa fa-box"))
```

`ProductView` को CSV में export करने पर इस structure वाला `export.zip` बनता है:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

`export.csv` का `photo` column file का ZIP-relative path रखता है — `assets/<storage-name>/<key>` — जिससे CSV spreadsheet application में readable रहता है। Admin referenced हर file अपने storage backend से fetch करके उसे `assets/` के अंदर package करता है।

Import ZIP archives accept नहीं करता। `FileField` और `ImageField` import से हमेशा excluded रहते हैं — डिफ़ॉल्ट रूप से `exclude_from_import=True` — इसलिए wizard upload पर `photo` column ignore कर देता है। Plain data file reimport करें, फिर files create/edit फ़ॉर्म से attach करें।


## Custom exporter लिखना {#writing-a-custom-exporter}

Custom exporter लिखने के लिए `BaseExporter` subclass करें और `generate` method implement करें। Base class ZIP wrapping, file downloads, और response headers handle करता है:

```python
from typing import Any
from starlette_admin.export import BaseExporter
from starlette_admin.fields import BaseField


class MarkdownExporter(BaseExporter):
    content_type = "text/markdown"
    extension = "md"

    async def generate(
        self, fields: list[BaseField], rows: list[dict[str, Any]]
    ) -> bytes:
        lines = [
            " | ".join(f.label or f.name for f in fields),
            " | ".join("---" for _ in fields),
        ]
        for row in rows:
            lines.append(" | ".join(str(row.get(f.name, "")) for f in fields))
        return "\n".join(lines).encode("utf-8")
```

`rows` data pre-cleaned आता है: admin पहले हर `FileField` और `ImageField` value को उसके ZIP-relative path string से replace कर देता है, इसलिए आपका `generate` method file dictionaries handle नहीं करता। Format dropdown में दिखाने के लिए `MarkdownExporter()` को अपनी `exporters` list में register करें।

## Custom importer लिखना {#writing-a-custom-importer}

Custom importer लिखने के लिए `BaseImporter` subclass करें और `parse` को async generator के रूप में implement करें जो प्रति row एक dictionary yield करे:

```python
import json
from collections.abc import AsyncGenerator
from typing import Any
from starlette_admin.importers import BaseImporter, ImportContext


class NdjsonImporter(BaseImporter):
    extension = "ndjson"

    async def parse(self, ctx: ImportContext) -> AsyncGenerator[dict[str, Any], None]:
        for line in ctx.content.decode("utf-8").splitlines():
            if line.strip():
                yield json.loads(line)
```

---

## आगे क्या {#whats-next}

* **[File Storage](file-storage.md):** Export ZIP bundle में referenced storage backends configure करें।
* **[Security](security.md):** Export row caps और import upload size limits.
* **[एक्शन](actions.md):** Export/import के साथ bulk और row actions जोड़ें।
