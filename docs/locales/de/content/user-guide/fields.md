---
title: Felder
description: Umfassende Referenz für alle integrierten Felder von starlette-admin
  zur Abbildung Ihrer Datenbankspalten auf UI-Komponenten.
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# Felder

Felder sind die Bausteine Ihrer Views. Im Hintergrund sind sie schlichte Python-Dataclasses: Jedes Attribut, das Sie an einen Feldkonstruktor übergeben, wird zu einem Dataclass-Feld, und jeder Feldtyp erbt von `BaseField`. Sie können ihn daher inspizieren, als Unterklasse implementieren oder direkt instanziieren.

## Gemeinsame Attribute

Jeder Feldtyp erbt diese Konfigurationsattribute von `BaseField`.

| Attribut | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `name` | `str` | **Erforderlich** | Der Attributname Ihres Modells. |
| `label` | `str | None` | In Title Case geschriebener `name` | Der Spaltenkopf und das Formularlabel. |
| `help_text` | `str | None` | `None` | Hinweistext unterhalb des Formulareingabefelds. |
| `required` | `bool` | `False` | Fordert einen Wert im Formular an, sowohl clientseitig als auch serverseitig. |
| `validators` | `list[Validator]` | `[]` | Serverseitige Validators, die gegen den eingereichten Wert laufen. Siehe [Validierung](#validierung). |
| `disabled` | `bool` | `False` | Graut das Eingabefeld aus und sperrt es in Formularen. |
| `read_only` | `bool` | `False` | Zeigt das Feld an, blockiert aber Änderungen. |
| `default` | `Any | Callable` | `None` | Der Vorbelegungswert im Erstellungsformular. |
| `getter` | `Callable | None` | `None` | Ersetzt den Modellattribut-Zugriff beim Auslesen des Werts. Siehe [Werte berechnen, formatieren und parsen](#computing-formatting-and-parsing-values). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Anzeigeformatierung pro Action, die die Serialisierung für diese Action ersetzt. Siehe [Werte berechnen, formatieren und parsen](#computing-formatting-and-parsing-values). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Eingabeparsing pro Action, das das Standardparsing des Felds ersetzt. Siehe [Werte berechnen, formatieren und parsen](#computing-formatting-and-parsing-values). |
| `searchable` | `bool` | `True` | Wird einbezogen, wenn der Suchparameter `q` übereinstimmt. |
| `orderable` | `bool` | `True` | Fügt im Listenkopf einen Sortierlink hinzu. |
| `copy_to_clipboard` | `bool` | `False` | Fügt auf der Detailseite eine Kopierschaltfläche neben dem Wert hinzu. |
| `filters` | `list | None` | `None` | Explizite Überschreibung der Filter der Listenseite. |
| `extra` | `dict[str, Any]` | `{}` | Ein Dictionary für Ihre eigenen Metadaten. |

### Sichtbarkeitssteuerung

Verwenden Sie diese booleschen Flags – standardmäßig alle auf `False` – um zu steuern, wo ein Feld erscheint:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Standardwerte definieren

Das Attribut `default` akzeptiert einen statischen Wert, eine aufrufbare Funktion ohne Argumente oder eine request-bezogene Funktion:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Statischer Wert
DateTimeField("created_at", default=datetime.utcnow)  # Aufrufbare Funktion ohne Argumente
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-bezogen
```

### Werte berechnen, formatieren und parsen {#computing-formatting-and-parsing-values}

Jedes Feld akzeptiert drei aufrufbare Hooks – `getter`, `formatter` und `parser` – die Daten abfangen und transformieren, während sie zwischen Ihrem Modell und der UI ausgetauscht werden. Jeder Hook akzeptiert eine synchrone oder eine asynchrone Funktion.

#### `getter`: eigene Werte lesen

Der Hook `getter` ersetzt den standardmäßigen `getattr()`-Zugriff, wenn das Feld eine Modellinstanz liest. Das Feld ruft `getter(request, obj)` auf und zeigt den Rückgabewert an.

```python
from starlette_admin import StringField

# Zeigt die E-Mail-Adresse eines verknüpften Autors statt eines direkten Spaltenwerts an
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Da `getter`-Werte selten einer physischen Datenbankspalte entsprechen, passen sie am besten zu einer reinen Anzeige ohne Bearbeitungsmöglichkeit. [`ComputedField`](#computedfield) ist ein integriertes Kürzel für genau diese Kombination.

#### `formatter`: Anzeigeausgabe transformieren

Der Hook `formatter` legt fest, wie ein gespeicherter Wert auf bestimmten Seiten gerendert wird. Er bildet eine `RequestAction`, etwa `LIST`, `DETAIL` oder `EXPORT`, auf eine aufrubare Funktion `(request, value) -> value` ab.

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Schlüssel in Listenviews maskieren; vollen Schlüssel in Detail-/Exportviews anzeigen
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**Formatierungsverhalten, das Sie beachten sollten:**

* **Nullwerte erreichen den Formatter:** Anders als bei der standardmäßigen Serialisierung erhalten Formatter auch `None`-Werte, sodass Sie Fallback-Texte liefern können, etwa `"unset"` im Beispiel oben.
* **Serialisierung wird umgangen:** Ein passender Formatter ersetzt die Methoden `serialize_value` und `serialize_none_value` des Felds. Der Rückgabewert wird unverändert verwendet, sodass der Formatter vollständig für die endgültige Ausgabe verantwortlich ist.
* **JSON-Anforderung:** Für die Actions `LIST` und `RELATION_LOOKUP` zurückgegebene Werte müssen JSON-serialisierbar bleiben.

#### `parser`: eingehende Daten verarbeiten

Der Hook `parser` überschreibt das standardmäßige Parsing des Felds für eingereichte oder importierte Daten. Er bildet eine `RequestAction` auf eine aufrufbare Funktion `(request, raw) -> value` ab.

* **Formulare (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` ist die eingereichte Formulareingabe bzw. eine Liste, wenn `multiple=True`.
* **Importe (`IMPORT`):** `raw` ist der unverarbeitete Zellwert aus der Datei.

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Währungssymbole beim Import entfernen und in ganzzahlige Cents umwandeln
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

Nach dem Parsing durchläuft der zurückgegebene Wert die übliche Validierungskette – zunächst `required`, dann `validators` – genau so, als hätte das Feld die Daten selbst geparst.

!!! tip "Hooks oder eine Unterklasse?"
    Für eine einmalige Anpassung an einem einzelnen Feld benötigen Sie selten eine Unterklasse. Übergeben Sie diese Hooks als Konstruktorargumente, um das Lesen, die Anzeigeformatierung und das Eingabeparsing abzudecken. [Leiten Sie eine Unterklasse vom Feld ab](../advanced/custom-fields.md), wenn Sie die Logik über mehrere Views hinweg wiederverwenden möchten oder wenn Sie die HTML-Rendering-Templates ändern müssen.

### Validierung

Die serverseitige Validierung läuft bei jedem Feld, wenn ein Erstellungs- oder Bearbeitungsformular abgesendet wird, sodass fehlerhafte Daten niemals die Datenbank erreichen.

Der Lebenszyklus ist festgelegt:

1. **Leere Werte:** Ist ein eingereichter Wert leer – etwa `None`, `""` oder eine leere Sammlung –, wird nur das Flag `required` geprüft. Die Validators werden übersprungen.
2. **Gefüllte Werte:** Sind Daten vorhanden, wird jede aufrufbare Funktion in der Liste `validators` der Reihe nach gegen den geparsten Wert ausgeführt.

#### Signatur eines Validators

Ein Validator erhält vier Argumente: `(request, field, value, form_values)`.

* **`request`:** Das aktuelle Starlette-Request-Objekt.
* **`field`:** Die gerade validierte Feldinstanz.
* **`value`:** Der für dieses Feld eingereichte, geparste Wert.
* **`form_values`:** Ein Dictionary mit allen geparsten Formulardaten, verschlüsselt nach Feldnamen, damit Sie andere Felder prüfen können.

Um einen Wert zurückzuweisen, lösen Sie einen `ValueError` aus. Der Admin fängt den ersten Fehler eines Felds ab, überspringt die übrigen Validators dieses Felds und sammelt alle Fehler, um sie neben den jeweiligen Eingabefeldern anzuzeigen.

#### Integrierte Validators

Das Modul [`starlette_admin.validators`](../api/validators.md) stellt Standardregeln bereit:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Eigene und asynchrone Validierung

Schreiben Sie eigene Validators als synchrone oder asynchrone Funktionen. Da sie den `request` erhalten, können sie die Datenbank abfragen, um komplexe Constraints zu prüfen.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

Über das Argument `form_values` kann ein Validator auf Feldebene auch eine Regel durchsetzen, die von einem anderen eingereichten Feld abhängt.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Kontextspezifische Validierungsregeln

* **Relationsfelder:** `HasOne` und `HasMany` erhalten während der Validierung die Primärschlüssel der verknüpften Datensätze.
* **Dateifelder:** Die Validierung läuft einmal pro `UploadFile` in der Payload. Siehe [Datei- & Medienfelder](#file-media-fields).
* **Feldübergreifende Validierung:** Verwenden Sie `form_values` für eine einfache Abhängigkeit. Für eine Regel, die sich über das gesamte Formular erstreckt, überschreiben Sie stattdessen die Methode `validate()` Ihrer View. Die Validierung auf View-Ebene läuft erst, nachdem jedes Feld seine eigene Validierungskette durchlaufen hat.

### Benutzerdefinierte Metadaten speichern

`extra` ist ein gewöhnliches `dict`, das `starlette-admin` weder liest noch beschreibt. Nutzen Sie es, um eigene Daten an eine Feldinstanz anzuhängen – etwa für ein eigenes Template, einen Hook in Ihrer [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin)-Unterklasse oder jeden anderen Integrationspunkt –, ohne vom Feld abzuleiten:

```python
from starlette_admin import StringField

StringField("sku", extra={"barcode_format": "code128"})
```

---

## Textfelder

### StringField & TextAreaField

`StringField` rendert ein einzeiliges Texteingabefeld für kurze Inhalte. `TextAreaField` erweitert es um ein `<textarea>`-Element für langen, mehrzeiligen Text.

```python
from starlette_admin import StringField, TextAreaField
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = [
        StringField("title", maxlength=200, placeholder="Post title"),
        TextAreaField("content", rows=10),
    ]
```

| Zusätzliches Attribut | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `maxlength` und `minlength` | `int | None` | `None` | HTML-Längenbeschränkungen. |
| `placeholder` | `str | None` | `None` | Platzhaltertext des Eingabefelds. |
| `rows` *(nur TextArea)* | `int` | `6` | Anzahl der sichtbaren Textzeilen. |

### TinyMCEEditorField

Erweitert `TextAreaField` um einen WYSIWYG-Editor aus der TinyMCE-Bibliothek. Es wird das Zusatzpaket `tinymce` benötigt.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    Die Attribute `height`, `menubar`, `statusbar` und `toolbar` steuern die Benutzeroberfläche des Editors. Übergeben Sie jede andere native TinyMCE-Konfiguration über `extra_options`.

### Formatierte Textfelder

Diese `StringField`-Varianten rendern einen passenden HTML-Eingabetyp und formatieren den Wert, wenn der Datensatz angezeigt wird.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` und `IPAddressField` fügen jeweils einen passenden Validator hinzu (`email`, `url`, `uuid` bzw. `ip_address` aus [`starlette_admin.validators`](../api/validators.md)), wenn Sie `validators` leer lassen. Übergeben Sie eigene `validators`, um dies zu überschreiben.

    `UUIDField` setzt standardmäßig `copy_to_clipboard=True`. `IPAddressField` akzeptiert `ipv4` (standardmäßig `True`) und `ipv6` (standardmäßig `False`), womit gesteuert wird, welche Adressfamilien sein Standardvalidator akzeptiert.

### PasswordField

Rendert in Formularen ein `<input type="password">`-Element, um die Eingaben des Benutzers zu verschleiern.

!!! danger
    `PasswordField` maskiert die Eingabe nur in Erstellungs- und Bearbeitungsformularen. Es überschreibt nicht die Anzeige-Templates, sodass Werte auf Listen- und Detailseiten als **Klartext** gerendert werden; zudem werden eingereichte Rohwerte auf `DEBUG`-Ebene protokolliert.

    Setzen Sie bei Passwortfeldern `exclude_from_list = True` und `exclude_from_detail = True` und deaktivieren Sie das `DEBUG`-Logging in Produktionsumgebungen.

## Numerische Felder

Numerische Felder verarbeiten Ganzzahlen, Gleitkommazahlen und Dezimalzahlen.

```python
from starlette_admin import DecimalField, FloatField, IntegerField
from starlette_admin.contrib.sqla import ModelView


class ProductView(ModelView):
    fields = [
        IntegerField("stock", min=0, max=10_000),
        FloatField("rating"),
        DecimalField("price", min=0, step="0.01"),
    ]
```

| Zusätzliches Attribut | Gilt für | Beschreibung |
| --- | --- | --- |
| `min` und `max` | Integer, Decimal | Minimal und maximal zulässige Werte. |
| `step` | Integer, Decimal | Die Schrittwerte-Beschränkung. |

!!! note
    `FloatField` funktioniert anders: Es rendert als einfaches Texteingabefeld, wandelt die Eingabe in einen `float` um und unterstützt weder `min`, `max` noch `step`.

## Datums- und Zeitfelder

Diese Felder nutzen die nativen Datums- und Zeitauswahldialoge des Browsers und basieren auf den entsprechenden Typen der Standardbibliothek (`datetime.date`, `datetime.datetime` und `datetime.time`).

```python
from starlette_admin import DateField, DateTimeField, TimeField
from starlette_admin.contrib.sqla import ModelView


class EventView(ModelView):
    fields = [
        DateField("event_date"),
        DateTimeField("starts_at", output_format="medium"),
        TimeField("daily_reminder"),
    ]
```

| Zusätzliches Attribut | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Babel-Anzeigeformat: `"short"`, `"medium"`, `"long"`, `"full"` oder ein eigenes Muster. |
| `search_format` | `str | None` | ORM-spezifisch | Format zum Aufbau der Datenbanksuchanfragen. |

!!! note
    Wenn die Zeitzonenunterstützung aktiviert ist, konvertiert `DateTimeField` für Sie zwischen der Anzeigezeitzone und der Datenbankzeitzone.

### ArrowField

Eine `DateTimeField`-Variante, die auf einem `Arrow`-Objekt basiert. Außerhalb von Bearbeitungsformularen zeigt sie eine verbalisierte relative Zeit an, etwa „vor 3 Stunden“. Es wird das Paket `arrow` benötigt.

## Auswahl- und Sammlungsfelder

### EnumField

Das universelle Auswahlfeld. Es rendert ein `<select>`-Dropdown bzw. eine `select2`-Mehrfachauswahl, wenn `multiple=True`. Als Grundlage dienen eine Python-`Enum`-Unterklasse, eine Liste von Tupeln oder zur Laufzeit geladene Auswahlmöglichkeiten.

```python
import enum
from starlette_admin import EnumField
from starlette_admin.contrib.sqla import ModelView


class Status(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"


class PostView(ModelView):
    fields = [
        EnumField("status", enum=Status),
        EnumField("language", choices=[("en", "English"), ("fr", "French")]),
    ]
```

| Zusätzliches Attribut | Typ | Beschreibung |
| --- | --- | --- |
| `enum` | `type[Enum] | None` | Baut die Auswahlmöglichkeiten aus einer Python-`Enum`-Klasse auf. |
| `choices` | `Sequence | None` | Statische `(value, label)`-Paare oder bloße Werte. |
| `choices_loader` | `Callable | None` | Berechnet die Auswahlmöglichkeiten pro Request. |
| `multiple` | `bool` | Aktiviert die Mehrfachauswahl und speichert die Werte als Liste. |

!!! important
    Geben Sie genau eines von `enum`, `choices` oder `choices_loader` an.

`TimeZoneField`, `CountryField` und `CurrencyField` sind `EnumField`-Unterklassen, die auf Babel-Lokalisierungsdaten basieren; dafür wird das Zusatzpaket `i18n` benötigt. Ihre Labels werden an die Sprache des aktuellen Requests angepasst.

### TagsField

Ein Freitext-Tagging-Eingabefeld auf Basis von `select2`. Es speichert eine `list[str]` und benötigt keine vordefinierten Auswahlmöglichkeiten.

### ListField

Umschließt ein anderes Feld, um eine geordnete Liste von Werten dieses Typs zu speichern. Es rendert wiederholbare Zeilen mit Steuerelementen zum Hinzufügen und Entfernen. Der Name des umschlossenen Felds wird zum Namen des `ListField`s.

```python
from starlette_admin import ListField, StringField

# Rendert eine wiederholbare Liste von String-Eingabefeldern
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Gruppiert mehrere Unterfelder zu einem verschachtelten Objekt. Verwenden Sie es für eingebettete oder struktartige Daten, etwa ein eingebettetes MongoDB-Dokument.

```python
from starlette_admin import CollectionField, IntegerField, StringField

fields = [
    CollectionField(
        "shipping_address",
        fields=[
            StringField("street"),
            StringField("city"),
            IntegerField("floor", required=False),
        ],
    ),
]
```

## Spezialisierte Felder

### JSONField

Rendert einen JSON-Baum und einen Code-Editor und speichert ein Python-`dict`. Übergeben Sie an `validation_schema` ein standardmäßiges JSON-Schema-Dictionary für clientseitiges Feedback.

### SlugField

Eine `StringField`-Variante, die sich clientseitig automatisch aus der Eingabe eines anderen Felds füllt. Eine manuelle Bearbeitung stoppt das automatische Ausfüllen.

```python
from starlette_admin import SlugField, StringField

fields = [
    StringField("title"),
    SlugField("slug", populate_from="title"),
]
```

!!! important
    `populate_from` ist erforderlich und muss auf ein anderes Feld desselben Formulars zeigen. Der generierte Slug wird wie jeder andere String eingereicht und gespeichert.

### ComputedField

Ein schreibgeschütztes, virtuelles Feld, das zur Anzeigezeit aus der Modellinstanz abgeleitet wird und dem keine Datenbankspalte zugrunde liegt. Es baut auf dem [`getter`-Hook](#computing-formatting-and-parsing-values) auf, den jedes Feld besitzt, und ergänzt die Standardwerte, die eine virtuelle Spalte benötigt: aus Erstellungsformularen ausgeschlossen, schreibgeschützt, nicht durchsuchbar und nicht sortierbar.

```python
from starlette_admin import ComputedField

fields = [
    "first_name",
    "last_name",
    ComputedField(
        "full_name", getter=lambda request, obj: f"{obj.first_name} {obj.last_name}"
    ),
]
```

Für komplexe oder wiederverwendbare Logik leiten Sie eine Unterklasse von `ComputedField` ab und überschreiben `parse_obj()`, statt einen Inline-`getter` zu übergeben:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` und `parse_obj` erfüllen denselben Zweck: Verwenden Sie `getter` für kurze Ausdrücke, und leiten Sie eine Unterklasse von `ComputedField` ab, wenn die Logik mehrere Zeilen umfasst oder über Views hinweg wiederverwendet wird. In Bearbeitungsformularen erscheint das Feld weiterhin als reine Textanzeige, sodass der Benutzer den aktuell berechneten Wert sieht.

Jede `ComputedField`-Unterklasse behält das Rendering von `StringField` bei. Um einen Wert zu berechnen, der als anderer Typ gerendert werden soll – etwa ein Datum, ein Badge oder ein Bild –, setzen Sie direkt bei diesem Feldtyp `getter=` zusammen mit den passenden Flags `read_only` und `exclude_from_*`.

## Datei- & Medienfelder {#file-media-fields}

`FileField` rendert ein Datei-Upload-Eingabefeld, und `ImageField` ergänzt eine Bildvorschau sowie eine Gültigkeitsprüfung. Hängen Sie ein `storage=`-Backend an, um Uploads automatisch zu speichern und ein JSON-`FileInfo`-Dictionary in der Datenbank abzulegen. Die vollständige Konfiguration finden Sie im [File-Storage-Leitfaden](file-storage.md).

```python
from starlette_admin import FileField, ImageField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

covers_storage = LocalStorage(base_dir="uploads/covers", name="covers")
documents_storage = LocalStorage(base_dir="uploads/documents", name="documents")


class ArticleView(ModelView):
    fields = [
        "id",
        "title",
        ImageField(
            "cover",
            storage=covers_storage,
            upload_folder="covers",
            max_size=5 * 1024 * 1024,
            thumbnail_size=(50, 50),
        ),
        FileField(
            "document",
            storage=documents_storage,
            upload_folder="documents",
            accept=".pdf,.doc,.docx",
        ),
    ]
```

| Zusätzliches Attribut | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Kommagetrennte Liste akzeptierter Dateierweiterungen oder MIME-Typen, die an das HTML-Attribut `accept` übergeben wird. |
| `multiple` | `bool` | `False` | Akzeptiert mehrere Dateien in einem Feld. |
| `storage` | `BaseStorage | None` | `None` | Storage-Backend, das die Uploads speichert. Ohne dieses Backend reicht das Feld die rohen Uploads an Ihr Backend weiter. |
| `upload_folder` | `str` | `""` | Der relativ zum Storage liegende Ordner für gespeicherte Dateien. |
| `max_size` | `int | None` | `None` | Maximal akzeptierte Uploadgröße in Bytes. |
| `validators` | `list[Validator]` | `[]` | Eigene Validators, die jeweils als `(request, field, upload)` einmal pro hochgeladener Datei aufgerufen werden – nach den Prüfungen `accept` und `max_size`. Lösen Sie einen `ValueError` aus, um zurückzuweisen. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | Nur `ImageField`. Wenn gesetzt, erzeugt Pillow beim Speichern eine Thumbnail in begrenzter Größe, und die Listenseite verwendet sie anstelle des vollständigen Bilds. |

!!! note
    `ImageField` stellt der `validators`-Liste eine bildbezogene Gültigkeitsprüfung auf Basis von Pillow voran. Wenn Pillow installiert und ein Storage konfiguriert ist, werden außerdem `width` und `height` in der resultierenden `FileInfo` aufgezeichnet.

Ist `thumbnail_size` gesetzt, erzeugt der Admin neben dem vollständigen Bild eine Thumbnail, wobei das Seitenverhältnis erhalten bleibt und nie hochskaliert wird; sie wird unter einem eigenen Schlüssel gespeichert. Beispielsweise erhält `covers/cat.jpg` ein Geschwister namens `covers/cat.thumb.jpg`. Die Listenseite verwendet die Thumbnail automatisch. Zeilen ohne eine solche – sei es wegen bereits vorhandener Daten oder weil `thumbnail_size` nicht gesetzt ist – greifen auf das vollständige Bild zurück. Ein Fehler bei der Thumbnail-Erzeugung wird protokolliert und lässt den Upload niemals fehlschlagen.

Auf der Detailseite öffnet sich jedes `ImageField`-Bild in einem Lightbox-Dialog, sodass Betrachter durch Bilder in voller Auflösung blättern können. Bilder, die zum selben Feld gehören (`multiple=True`), werden zu einer Galerie zusammengefasst.

Unter [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) finden Sie eine vollständig lauffähige App, einschließlich eines eigenen MIME-Type-Validators.

### Ohne Storage

Ohne angehängtes `storage=` reicht das Feld die Uploads unmittelbar an Ihr Backend weiter, statt sie selbst zu speichern:

* **In Erstellungs- und Bearbeitungsformularen** ist der geparste Wert ein Tupel, `(UploadFile | list[UploadFile] | None, bool)`. Das erste Element ist die rohe Starlette-`UploadFile`, eine Liste, wenn `multiple=True`, oder `None`, wenn der Benutzer nichts ausgewählt hat. Das zweite Element ist `True`, wenn der Benutzer auf dem Bearbeitungsformular das Kontrollkästchen zum Löschen anwählt – das bedeutet, dass die vorhandene Datei ohne Ersatz entfernt werden soll. Die `create()`- und `edit()`-Logik Ihres Backends speichert den Upload und beachtet das Löschflag.
* **Auf Listen- und Detailseiten** erwartet das Feld, dass der Wert drei Schlüssel als `dict` oder drei Attribute als Objekt bereitstellt: `url` (erforderlich), das Linkziel; `filename`, das Anzeigelabel; und `content_type`, das das Dateityp-Symbol auswählt.

Dieser Vertrag ist die Grundlage dafür, dass die folgenden ORM-Integrationen ihre eigene Dateiverarbeitung in dasselbe Feld einhängen können.

### ORM-native Dateispalten

**MongoEngine** unterstützt `mongoengine.FileField` und `mongoengine.ImageField` ab Werk, mit **GridFS** als Storage. Der Admin lädt Dateien für Sie nach GridFS hoch, stellt sie von dort bereit und löscht sie dort. Sie benötigen keine `storage=`-Konfiguration: Führen Sie das Feld einfach namentlich auf.

**SQLAlchemy** erhält dieselbe Behandlung über [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Deklarieren Sie dessen Spaltentypen `FileField` oder `ImageField` in Ihren Modellen, dann erkennt `starlette-admin` sie, rendert das passende Admin-Feld und registriert eine Route, um die gespeicherten Dateien bereitzustellen. Den Storage konfigurieren Sie über sqlalchemy-files eigenen `StorageManager`, der auf Apache-Libcloud-Containern basiert; zudem gehen Uploads in die Session-Transaktion ein, sodass ein Rollback der Session auch die gespeicherte Datei verwirft.

```python
import os

from libcloud.storage.drivers.local import LocalStorageDriver
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy_file import ImageField
from sqlalchemy_file.storage import StorageManager
from sqlalchemy_file.validators import SizeValidator
from starlette_admin.contrib.sqla import ModelView


class Base(DeclarativeBase):
    pass


class Author(Base):
    __tablename__ = "author"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    avatar = mapped_column(
        ImageField(
            upload_storage="avatar",
            thumbnail_size=(50, 50),
            validators=[SizeValidator("200k")],
        )
    )


# sqlalchemy-file storage setup, independent of starlette-admin's BaseStorage
os.makedirs("upload/avatars", exist_ok=True)
StorageManager.add_storage(
    "avatar", LocalStorageDriver("upload").get_container("avatars")
)


class AuthorView(ModelView):
    fields = ["id", "name", "avatar"]
```

Unter [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) finden Sie eine vollständige App mit mehreren Storages, Content-Type-Validierung und Feldern mit `multiple=True`.

## HasOne & HasMany

Relationsfelder, die als `select2`-Eingabefelder gerendert werden und auf dem Such-endpoint der verknüpften View basieren.

```python
from starlette_admin import HasMany, HasOne, IntegerField, StringField
from starlette_admin.contrib.sqla import Admin, ModelView


class AuthorView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("name"),
        HasMany("books", key="book"),
    ]


class BookView(ModelView):
    fields = [
        IntegerField("id"),
        StringField("title"),
        HasOne("author", key="author"),
    ]
```

Der Parameter `key` verweist auf die passende `ModelView`. Registrieren Sie beide Views auf derselben `Admin`-Instanz, damit die Schlüssel aufgelöst werden können.

---

## Nächste Schritte

* [Filter](filters.md): Passen Sie den Filter-Builder Ihrer Listenseiten an.
* [File Storage](file-storage.md): Konfigurieren Sie Storage-Backends für `FileField` und `ImageField`.
* [Eigene Felder](../advanced/custom-fields.md): Bauen Sie ein benutzerdefiniertes Feld.
