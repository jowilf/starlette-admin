---
title: Export und Import
description: Aktivieren Sie CSV-, JSON- und PDF-Export sowie Bulk-Datenimporte mit
  Validierung in starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/export-import/)
<!-- translation-notice:end -->

# Export und Import

Auf jeder Listenseite können Benutzer Daten in eine Datei exportieren und Daten aus einer Datei importieren – Sie müssen also keine eigenen Routen schreiben.

## Überblick

* **Export:** Benutzer wählen die Toolbar-Schaltfläche aus und legen dann Umfang, Felder, Format und Dateinamen fest.
* **Import:** Benutzer wählen die Toolbar-Schaltfläche aus, um einen dreistufigen Assistenten zu öffnen: Hochladen, Vorschau und Ergebnis.
* **Formate:** CSV, JSON, XLSX, ODS, YAML, PDF sowie benutzerdefinierte Formate werden standardmäßig unterstützt.
* **Upsert:** Importe können optional vorhandene Datensätze aktualisieren, die über den Primärschlüssel zugeordnet werden.
* **Integration:** Beide Funktionen funktionieren mit Filterung, Sortierung, Zeilenauswahl und speicherbasierten Feldern.
* **Keine zusätzlichen Endpoints:** Alles ist bereits in der View enthalten.

## Minimales Beispiel

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

`ProductView` zeigt nun eine Schaltfläche **Export** und eine Schaltfläche **Import** in der Listentoolbar an. Jeder Dialog bietet genau die Formate an, die Sie in `exporters` bzw. `importers` angeben.

---

## Export aktivieren

Das Attribut `exporters` listet die bereitzustellenden Formate als einfache Dateiendungs-Zeichenfolgen auf:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

Der Standardwert ist `["csv", "json"]`. Die folgende Tabelle listet alle integrierten Formate und das jeweils benötigte Paket auf. Die Formate `csv`, `tsv` und `json` benötigen keine zusätzlichen Abhängigkeiten. Jedes andere tabellarische Format verwendet `tablib`, und `pdf` verwendet `reportlab`. Eine unbekannte Formatzeichenfolge oder ein Format, dessen Paket nicht installiert ist, löst beim Start einen Fehler aus.

| Format | Installationsanforderung |
| --- | --- |
| `csv`, `tsv`, `json` | Im Kernpaket enthalten |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Formatoptionen überschreiben

Jede Formatzeichenfolge wird zu einer vorkonfigurierten Exporter-Instanz mit sinnvollen Standardwerten aufgelöst. Wenn ein Format andere Einstellungen benötigt, übergeben Sie stattdessen eine Exporter-Instanz. Sie können Zeichenfolgen und Instanzen in derselben Liste mischen:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` leitet Schlüsselwortargumente an `csv.writer` weiter und akzeptiert den Parameter `escape_formulas`. `TablibExporter(format, **kwargs)` deckt jedes tablib-Format ab und leitet Schlüsselwortargumente an `tablib.Dataset.export()` weiter.

!!! warning
    Das Escaping von Formeln ist standardmäßig deaktiviert. Wenn exportierte Felder benutzerdefinierte Zeichenfolgen enthalten können, setzen Sie `escape_formulas=True` bei `CsvExporter`, `TsvExporter` oder `TablibExporter`, um eine Formelinjektion zu verhindern, wenn jemand die Datei in einer Tabellenkalkulationsanwendung öffnet. Weitere Informationen finden Sie unter [Formula injection](security.md#formula-injection).

Der Export ist standardmäßig aktiviert. Die Schaltfläche **Export** erscheint in der Toolbar, sobald die Liste `exporters` nicht leer ist. Um festzulegen, wer exportieren darf, überschreiben Sie die Methode `can_export(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Der Exportdialog

Der Export ist eine integrierte globale Action. Beim Auswählen von **Export** öffnet sich ein Dialog, in dem der Benutzer den Export konfiguriert, bevor er heruntergeladen wird.

* **Umfang:** Was exportiert werden soll. Die Optionen sind „Ausgewählte Zeilen“ (Standard, wenn Zeilen markiert sind), „Alle übereinstimmenden Zeilen“ (verfügbar über das Banner „Alle auswählen“) und „Aktuelle Seite“ (Standard, wenn nichts ausgewählt ist).
* **Felder:** Ein Kontrollkästchen pro exportierbarem Feld. Deaktivieren eines Kontrollkästchens entfernt diese Spalte. Felder mit `exclude_from_export=True` erscheinen hier nie.
* **Format:** Ein Eintrag pro Format in `exporters`.
* **Dateiname:** Standardmäßig der View-Schlüssel. Der Server hängt die Dateiendung an.

Jeder Umfang berücksichtigt die aktuelle Suche, die Filter und die Sortierreihenfolge der Listenseite – was der Benutzer sieht, ist genau das, was er exportiert.

### Das Zeilenlimit

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

`ExportConfig.max_rows` hat den Standardwert 100.000. Das Limit bezieht sich auf die Anzahl der Zeilen, die der gewählte Umfang tatsächlich erzeugen würde, und der Admin prüft die Anzahl, bevor er irgendeine Zeile abruft. Wird das Limit überschritten, zeigt der Admin eine Fehlermeldung an und leitet zurück zur Listenseite, statt die Datei zu generieren. So wird verhindert, dass ein breiter, ungefilterter Export auf einer großen Tabelle die Anfrage blockiert. Setzen Sie `max_rows=None`, um das Limit zu entfernen.

---

## Import aktivieren

Das Attribut `importers` funktioniert exakt wie `exporters` und akzeptiert Formatzeichenfolgen:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

Die integrierten Importformate sind `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` und `html` – mit denselben Abhängigkeiten wie ihre Export-Pendants. Um die Standardwerte eines Formats zu überschreiben, übergeben Sie eine Importer-Instanz, z. B. `CsvImporter(delimiter=";")` aus `starlette_admin.importers`.

Der Import ist standardmäßig aktiviert, mit `["csv", "json"]`. Die Schaltfläche **Import** erscheint in der Toolbar, sobald die Liste `importers` nicht leer ist. Um festzulegen, wer importieren darf, überschreiben Sie die Methode `can_import(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Der Importassistent

Beim Auswählen von **Import** öffnet sich ein dreistufiger Assistent. Vor der abschließenden Bestätigung wird nichts in die Datenbank geschrieben, und zwischen den Schritten wird keine Datei auf dem Server gespeichert: Der Browser hält die Datei vor und sendet sie bei jedem Schritt erneut.

1. **Hochladen:** Wählen Sie ein Format, wählen Sie eine Datei aus und aktivieren Sie optional **Vorhandene Datensätze nach Primärschlüssel aktualisieren**. Wenn Sie diese Option aktivieren, aktualisiert eine Zeile, deren Primärschlüssel mit einem vorhandenen Datensatz übereinstimmt, diesen Datensatz, statt einen neuen zu erstellen. Andernfalls wird jede Zeile neu erstellt.
2. **Vorschau:** Das Absenden des Uploads führt einen vollständigen Validierungsdurchlauf durch, ohne etwas zu schreiben. Der Assistent zeigt eine Zusammenfassung, die Spaltenzuordnungen, Beispielzeilen und eine detaillierte Fehlertabelle an.
3. **Ergebnis:** Der Assistent committet den Import und meldet die endgültigen Zahlen für erstellte, aktualisierte und übersprungene Datensätze. Zeilen, die in der Vorschau die Validierung nicht bestanden haben, werden übersprungen.

!!! tip
    Damit das Backend die Primärschlüssel generiert, entfernen Sie die Zuordnung der Primärschlüsselspalte in der Vorschau. Die importierten Zeilen tragen dann keinen Schlüsselwert, sodass der erneute Import einer von Ihnen exportierten Datei neue Datensätze erstellt, statt an veralteten IDs zu scheitern.

### Upload- und Zeilenlimits

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

Der Import-Endpoint spiegelt das Export-Zeilenlimit wider. `ImportConfig.max_rows` hat den Standardwert 100.000 und wird durchgesetzt, bevor irgendein Datensatz erstellt wird. Der Admin zählt die hochgeladene Datei in einem Vorablauf und weist eine Datei mit mehr Zeilen als dem Limit mit einem HTTP-400-Fehler ab. Setzen Sie `max_rows=None`, um das Limit zu entfernen. `ImportConfig.max_upload_size` begrenzt Uploads zusätzlich auf standardmäßig 10 MB.

### Header-Zuordnung

Der Assistent ordnet jeden Datei-Header zunächst dem `label` Ihres Feldes zu, danach dessen `name`. Eine Datei mit der Spalte `Name` und eine Datei mit der Spalte `name` werden beide dem Feld `name` zugeordnet. Nicht zugeordnete Spalten werden ignoriert, und Felder ohne passende Spalte erhalten `None`.

## Dateifelder

Eine View mit einem speicherbasierten `FileField` oder `ImageField` wird als ZIP-Archiv exportiert, sodass die Dateiinhalte zusammen mit den Zeilendaten übertragen werden:

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

Der Export von `ProductView` als CSV erzeugt eine Datei `export.zip` mit folgender Struktur:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

Die Spalte `photo` in `export.csv` enthält den ZIP-relative Pfad der Datei, `assets/<storage-name>/<key>`, wodurch die CSV in einer Tabellenkalkulationsanwendung lesbar bleibt. Der Admin ruft jede referenzierte Datei aus ihrem Storage-Backend ab und packt sie unter `assets/`.

Der Import akzeptiert keine ZIP-Archive. `FileField` und `ImageField` sind vom Import immer ausgeschlossen, da sie standardmäßig `exclude_from_import=True` setzen – der Assistent ignoriert daher die Spalte `photo` beim Upload. Importieren Sie erneut eine reine Datendatei und hängen Sie anschließend Dateien über die Create- oder Edit-Formulare an.


## Einen eigenen Exporter schreiben

Um einen eigenen Exporter zu schreiben, leiten Sie von `BaseExporter` ab und implementieren die Methode `generate`. Die Basisklasse übernimmt das ZIP-Einpacken, den Dateidownload und die Response-Header:

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

Die Daten in `rows` kommen bereits bereinigt an: Der Admin ersetzt zuerst jeden Wert von `FileField` und `ImageField` durch seine ZIP-relative Pfadzeichenfolge, sodass Ihre Methode `generate` nie mit Datei-Dictionarys umgehen muss. Registrieren Sie `MarkdownExporter()` in Ihrer Liste `exporters`, um es im Format-Dropdown anzuzeigen.

## Einen eigenen Importer schreiben

Um einen eigenen Importer zu schreiben, leiten Sie von `BaseImporter` ab und implementieren `parse` als Async Generator, der pro Zeile ein Dictionary liefert:

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

## Wie es weitergeht

* **[File Storage](file-storage.md):** Konfigurieren Sie die Storage-Backends, auf die im Export-ZIP-Bundle verwiesen wird.
* **[Security](security.md):** Export-Zeilenlimits und Import-Uploadgrößenbeschränkungen.
* **[Actions](actions.md):** Ergänzen Sie Bulk- und Row-Actions neben Export und Import.
