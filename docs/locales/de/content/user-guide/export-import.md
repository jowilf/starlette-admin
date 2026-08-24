---
title: Export und Import
description: Aktivieren Sie CSV-, JSON- und PDF-Export sowie Massenimporte mit Validierung
  in starlette-admin.
source_hash: 90cb474355c091c80bb8d0e65e3b1aefa9a94e31738fb71b4e28e71590b29ce1
prompt_hash: e74e266b22cedf72eaa794c2ae7a360fd32046953223afb4ffa22b1342d51b63
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-23'
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

Auf jeder Listenseite können Benutzer Daten in eine Datei exportieren und Daten aus einer Datei importieren, sodass Sie keine benutzerdefinierten Routen schreiben müssen.

## Überblick

* **Export:** Benutzer wählen die Toolbar-Schaltfläche aus und legen dann Umfang, Felder, Format und Dateinamen fest.
* **Import:** Benutzer wählen die Toolbar-Schaltfläche aus, um einen dreistufigen Assistenten zu öffnen: Upload, Vorschau und Ergebnisse.
* **Formate:** CSV, JSON, XLSX, ODS, YAML, PDF und benutzerdefinierte Formate werden ab Werk unterstützt.
* **Upsert:** Importe können optional vorhandene Datensätze aktualisieren, die über den Primärschlüssel gefunden werden.
* **Integration:** Beide Funktionen funktionieren mit Filterung, Sortierung, Zeilenauswahl und feldern mit Storage-Backend.
* **Keine zusätzlichen Endpoints:** Alles ist in der View enthalten.

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

`ProductView` zeigt jetzt eine Schaltfläche **Export** und eine Schaltfläche **Import** in der Listentoolbar an. Jeder Dialog bietet genau die Formate an, die Sie in `exporters` und `importers` auflisten.

---

## Export aktivieren

Das Attribut `exporters` listet die bereitzustellenden Formate als einfache Extension-Strings auf:

```python hl_lines="2"
class ProductView(ModelView):
    exporters = ["csv", "xlsx", "json"]

```

Der Defaultwert ist `["csv", "json"]`. Die folgende Tabelle listet jedes integrierte Format und das benötigte Paket auf. Die Formate `csv`, `tsv` und `json` benötigen keine zusätzlichen Abhängigkeiten. Jedes andere tabellarische Format verwendet `tablib`, und `pdf` verwendet `reportlab`. Ein unbekannter Formatstring oder ein Format, dessen Paket nicht installiert ist, löst beim Start einen Fehler aus.

| Format | Installationsanforderung |
| --- | --- |
| `csv`, `tsv`, `json` | Im Core enthalten |
| `xlsx` | `pip install tablib[xlsx]` |
| `xls` | `pip install tablib[xls]` |
| `ods` | `pip install tablib[ods]` |
| `yaml` | `pip install tablib[yaml]` |
| `dbf`, `html`, `latex`, `jira`, `rst` | `pip install tablib` |
| `pdf` | `pip install starlette-admin[pdf]` |

### Formatoptionen überschreiben

Jeder Formatstring wird zu einer vorkonfigurierten Exporter-Instanz mit sinnvollen Defaults aufgelöst. Wenn ein Format andere Einstellungen benötigt, übergeben Sie stattdessen eine Exporter-Instanz. Sie können Strings und Instanzen in derselben Liste mischen:

```python hl_lines="5"
from starlette_admin.export import CsvExporter

class ProductView(ModelView):
    exporters = [CsvExporter(delimiter=";"), "xlsx", "json"]

```

`CsvExporter` leitet Keyword-Argumente an `csv.writer` weiter und akzeptiert einen Parameter `escape_formulas`. `TablibExporter(format, **kwargs)` deckt jedes Tablib-Format ab und leitet Keyword-Argumente an `tablib.Dataset.export()` weiter.

!!! warning
    Das Escaping von Formeln ist standardmäßig deaktiviert. Wenn exportierte Felder vom Benutzer bereitgestellte Strings enthalten können, setzen Sie `escape_formulas=True` auf `CsvExporter`, `TsvExporter` oder `TablibExporter`, um eine Formel-Injection zu verhindern, wenn jemand die Datei in einer Tabellenkalkulationsanwendung öffnet. Siehe [Formula injection](security.md#formula-injection).

Export ist standardmäßig aktiviert. Die Schaltfläche **Export** erscheint in der Toolbar, sobald die Liste `exporters` nicht leer ist. Um einzuschränken, wer exportieren darf, überschreiben Sie die Methode `can_export(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_export(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Der Exportdialog

Export ist eine integrierte globale Aktion. Wenn Sie **Export** auswählen, öffnet sich ein Dialog, in dem der Benutzer den Export vor dem Herunterladen konfiguriert.

* **Umfang:** Was exportiert werden soll. Die Optionen sind „Selected rows“, der Defaultwert, wenn Zeilen angehakt sind, „All matching rows“, verfügbar über das Select-all-Banner, und „Current page“, der Defaultwert, wenn nichts ausgewählt ist.
* **Felder:** Eine Checkbox pro exportierbarem Feld. Wenn Sie eine Checkbox deaktivieren, entfällt diese Spalte. Felder mit `exclude_from_import=True` erscheinen hier nie.
* **Format:** Ein Eintrag pro Format in `exporters`.
* **Dateiname:** Defaultwert ist der View-Key. Der Server hängt die Dateierweiterung an.

Jeder Umfang berücksichtigt die aktuelle Suche, Filter und Sortierung der Listenseite, sodass der Benutzer genau das exportiert, was er sieht.

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

`ExportConfig.max_rows` hat den Defaultwert 100.000. Das Limit gilt für die Anzahl der Zeilen, die der gewählte Umfang tatsächlich erzeugen würde, und das Admin-Panel prüft die Anzahl, bevor es irgendeine Zeile abruft. Wenn die Anzahl das Limit überschreitet, zeigt das Admin-Panel eine Fehlermeldung als Flash-Nachricht an und leitet zurück zur Listenseite, statt die Datei zu generieren. So wird verhindert, dass ein breiter, ungefilterter Export auf einer großen Tabelle den Request blockiert. Setzen Sie `max_rows=None`, um das Limit zu entfernen.

---

## Import aktivieren

Das Attribut `importers` funktioniert genau wie `exporters` und akzeptiert Formatstrings:

```python hl_lines="2"
class ProductView(ModelView):
    importers = ["csv", "xlsx"]

```

Die integrierten Importformate sind `csv`, `tsv`, `json`, `yaml`, `xlsx`, `xls`, `ods`, `dbf` und `html`, mit denselben Abhängigkeiten wie ihre Export-Pendants. Um die Defaults eines Formats zu überschreiben, übergeben Sie eine Importer-Instanz, z. B. `CsvImporter(delimiter=";")` aus `starlette_admin.importers`.

Import ist standardmäßig aktiviert, mit `["csv", "json"]`. Die Schaltfläche **Import** erscheint in der Toolbar, sobald die Liste `importers` nicht leer ist. Um einzuschränken, wer importieren darf, überschreiben Sie die Methode `can_import(request)`:

```python hl_lines="5 6"
from starlette.requests import Request

class ProductView(ModelView):
    def can_import(self, request: Request) -> bool:
        return request.state.admin_user.username == "admin"

```

### Der Importassistent

Wenn Sie **Import** auswählen, öffnet sich ein dreistufiger Assistent. Vor der finalen Bestätigung wird nichts in die Datenbank geschrieben, und zwischen den Schritten wird keine Datei auf dem Server gespeichert: Der Browser hält die Datei und sendet sie bei jedem Schritt erneut.

1. **Upload:** Wählen Sie ein Format, wählen Sie eine Datei aus und optional **Update existing records by primary key**. Wenn Sie dies auswählen, aktualisiert eine Zeile, deren Primärschlüssel einem vorhandenen Datensatz entspricht, diesen Datensatz, statt einen neuen zu erstellen. Andernfalls wird jede Zeile neu erstellt.
2. **Vorschau:** Das Absenden des Uploads führt einen vollständigen Validierungsdurchlauf durch, ohne etwas zu schreiben. Der Assistent zeigt eine Zusammenfassung, die Spaltenzuordnungen, Beispielzeilen und eine detaillierte Fehlertabelle.
3. **Ergebnis:** Der Assistent committet den Import und meldet die finalen Zahlen für erstellte, aktualisierte und übersprungene Datensätze. Zeilen, die in der Vorschau die Validierung nicht bestanden haben, werden übersprungen.

!!! tip
    Damit das Backend Primärschlüssel generiert, deaktivieren Sie die Primärschlüsselspalte in der Zuordnung der Vorschau. Die importierten Zeilen tragen dann keinen Schlüsselwert, sodass das erneute Importieren einer von Ihnen exportierten Datei neue Datensätze erstellt, statt an veralteten IDs zu scheitern.

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

Der Import-Endpoint spiegelt das Export-Zeilenlimit wider. `ImportConfig.max_rows` hat den Defaultwert 100.000 und wird durchgesetzt, bevor irgendein Datensatz erstellt wird. Das Admin-Panel zählt die hochgeladene Datei in einem Durchlauf vorab und weist eine Datei mit mehr Zeilen als dem Limit mit einem HTTP-400-Fehler zurück. Setzen Sie `max_rows=None`, um das Limit zu entfernen. `ImportConfig.max_upload_size` begrenzt Uploads ebenfalls standardmäßig auf 10 MB.

### Header-Abgleich

Der Assistent gleicht jeden Datei-Header zunächst mit dem `label` Ihres Feldes ab, dann mit seinem `name`. Eine Datei mit der Spalte `Name` und eine Datei mit der Spalte `name` werden beide einem Feld namens `name` zugeordnet. Nicht übereinstimmende Spalten werden ignoriert, und Felder ohne passende Spalte erhalten `None`.

## File-Felder

Eine View mit einem `FileField` oder `ImageField` mit Storage-Backend wird als ZIP-Archiv exportiert, sodass die Dateiinhalte zusammen mit den Zeilendaten transportiert werden:

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

Der Export von `ProductView` nach CSV erzeugt eine `export.zip` mit dieser Struktur:

```text
export.zip
├── export.csv              ← photo column holds "assets/covers/products/a1b2_photo.jpg"
└── assets/
    └── covers/
        └── products/
            └── a1b2_photo.jpg


```

Die Spalte `photo` in `export.csv` enthält den ZIP-relativen Pfad der Datei, `assets/<storage-name>/<key>`, wodurch die CSV in einer Tabellenkalkulationsanwendung lesbar bleibt. Das Admin-Panel ruft jede referenzierte Datei aus ihrem Storage-Backend ab und packt sie unter `assets/`.

Der Import akzeptiert keine ZIP-Archive. `FileField` und `ImageField` sind immer vom Import ausgeschlossen, da sie standardmäßig `exclude_from_import=True` haben, sodass der Assistent die Spalte `photo` beim Upload ignoriert. Importieren Sie erneut eine reine Datendatei und hängen Sie dann Dateien über die Erstellen- oder Bearbeiten-Formulare an.


## Einen benutzerdefinierten Exporter schreiben

Um einen benutzerdefinierten Exporter zu schreiben, subclassen Sie `BaseExporter` und implementieren die Methode `generate`. Die Basisklasse übernimmt das Wrappen in ZIP, Dateidownloads und Response-Header:

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

Die Daten in `rows` kommen bereits bereinigt an: Das Admin-Panel ersetzt zuerst jeden Wert von `FileField` und `ImageField` durch seinen ZIP-relativen Pfad-String, sodass Ihre Methode `generate` nie mit Datei-Dictionaries umgehen muss. Registrieren Sie `MarkdownExporter()` in Ihrer Liste `exporters`, um ihn im Format-Dropdown-Menü anzuzeigen.

## Einen benutzerdefinierten Importer schreiben

Um einen benutzerdefinierten Importer zu schreiben, subclassen Sie `BaseImporter` und implementieren `parse` als Async-Generator, der pro Zeile ein Dictionary liefert:

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

## Was kommt als Nächstes

* **[File Storage](file-storage.md):** Konfigurieren Sie die im Export-ZIP-Bundle referenzierten Storage-Backends.
* **[Security](security.md):** Export-Zeilenlimits und Import-Uploadgrößenbegrenzungen.
* **[Actions](actions.md):** Fügen Sie Massen- und Zeilenaktionen neben Export und Import hinzu.
