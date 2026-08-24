---
title: Felder
description: Umfassende Referenz für alle integrierten Felder in starlette-admin,
  um Ihre Datenbankspalten auf UI-Komponenten abzubilden.
source_hash: 3c9c4a5f2b25717d80f8f6130fa12fdb5e0ae0ff8ef86c4c692b63f3a6f4bada
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/fields/)
<!-- translation-notice:end -->

# Felder

Felder sind die Bausteine Ihrer Views. Unter der Haube sind sie schlichte Python-Dataclasses: Jedes Attribut, das Sie an einen Feldkonstruktor übergeben, wird zu einem Dataclass-Feld, und jeder Feldtyp erbt von `BaseField`, sodass Sie ihn inspizieren, als Subklasse implementieren oder direkt instanziieren können.

## Gemeinsame Attribute

Jeder Feldtyp erbt diese Konfigurationsattribute von `BaseField`.

| Attribut | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `name` | `str` | **Erforderlich** | Der Attributname auf Ihrem Modell. |
| `label` | `str | None` | `name` in Title-Case | Der Spaltenkopf und das Formularlabel. |
| `help_text` | `str | None` | `None` | Hinweistext unterhalb des Formulareingabefelds. |
| `required` | `bool` | `False` | Erfordert einen Wert in Formularen, sowohl auf dem Client als auch auf dem Server. |
| `validators` | `list[Validator]` | `[]` | Serverseitige Validatoren, die gegen den eingereichten Wert laufen. Siehe [Validierung](#validierung). |
| `disabled` | `bool` | `False` | Graut das Eingabefeld in Formularen aus und sperrt es. |
| `read_only` | `bool` | `False` | Zeigt das Feld, blockiert aber Änderungen. |
| `default` | `Any | Callable` | `None` | Der Vorbelegungswert im Erstellen-Formular. |
| `getter` | `Callable | None` | `None` | Ersetzt den Modellattribut-Zugriff beim Lesen des Werts. Siehe [Werte berechnen, formatieren und parsen](#werte-berechnen-formatieren-und-parsen). |
| `formatter` | `dict[RequestAction, Callable] | None` | `None` | Anzeigeformatierung pro Aktion, die die Serialisierung für diese Aktion ersetzt. Siehe [Werte berechnen, formatieren und parsen](#werte-berechnen-formatieren-und-parsen). |
| `parser` | `dict[RequestAction, Callable] | None` | `None` | Eingabeparsing pro Aktion, das das Standard-Parsing des Felds ersetzt. Siehe [Werte berechnen, formatieren und parsen](#werte-berechnen-formatieren-und-parsen). |
| `searchable` | `bool` | `True` | Wird einbezogen, wenn der Suchparameter `q` matcht. |
| `orderable` | `bool` | `True` | Fügt einen Sortierlink im Listenkopf hinzu. |
| `copy_to_clipboard` | `bool` | `False` | Fügt neben dem Wert auf der Detailseite eine Kopierschaltfläche hinzu. |
| `filters` | `list | None` | `None` | Explizite Überschreibung für die Filter der Listenseite. |
| `extra` | `dict[str, Any]` | `{}` | Ein Dictionary für Ihre eigenen Metadaten. |

### Sichtbarkeitssteuerung

Verwenden Sie diese booleschen Flags, alle standardmäßig `False`, um zu steuern, wo ein Feld erscheint:

* `exclude_from_list`
* `exclude_from_detail`
* `exclude_from_create`
* `exclude_from_edit`
* `exclude_from_export`
* `exclude_from_import`

### Defaultwerte definieren

Das Attribut `default` akzeptiert einen statischen Wert, eine aufrufbare Funktion ohne Argumente oder eine request-bezogene Funktion:

```python
from datetime import datetime
from starlette_admin import DateTimeField, StringField

StringField("status", default="draft")  # Static value
DateTimeField("created_at", default=datetime.utcnow)  # Zero-arg callable
StringField(
    "locale", default=lambda request: request.state.admin_user.locale
)  # Request-aware
```

### Werte berechnen, formatieren und parsen

Jedes Feld akzeptiert drei aufrufbare Hooks, `getter`, `formatter` und `parser`, die Daten abfangen und transformieren, während sie zwischen Ihrem Modell und dem UI wandern. Jeder davon akzeptiert eine synchrone oder eine asynchrone Funktion.

#### `getter`: benutzerdefinierte Werte lesen

Der Hook `getter` ersetzt den Standardzugriff via `getattr()`, wenn das Feld eine Modellinstanz liest. Das Feld ruft `getter(request, obj)` auf und zeigt den Rückgabewert an.

```python
from starlette_admin import StringField

# Displays a related author's email instead of a direct column value
StringField("author_email", getter=lambda request, obj: obj.author.email)
```

Da `getter`-Werte selten einer physischen Datenbankspalte entsprechen, passen sie am besten zu einer schreibgeschützten Anzeige. [`ComputedField`](#computedfield) ist ein integriertes Kürzel für genau diese Kombination.

#### `formatter`: Anzeigeausgabe transformieren

Der Hook `formatter` legt fest, wie ein gespeicherter Wert auf bestimmten Seiten gerendert wird. Er bildet eine `RequestAction`, etwa `LIST`, `DETAIL` oder `EXPORT`, auf eine `(request, value) -> value`-Funktion ab.

```python
from starlette_admin import RequestAction, StringField

StringField(
    "api_key",
    formatter={
        # Mask the key on list views; show the full key on detail/export views
        RequestAction.LIST: lambda request, value: (
            f"{value[:4]}..." if value else "unset"
        ),
    },
)
```

**Formatierungsverhalten, das Sie beachten sollten:**

* **Nulls erreichen den Formatter:** Anders als bei der Standardserialisierung erhalten Formatter auch `None`-Werte, sodass Sie Fallback-Text liefern können, etwa `"unset"` oben.
* **Serialisierung wird umgangen:** Ein passender Formatter ersetzt die Methoden `serialize_value` und `serialize_none_value` des Felds. Der Rückgabewert wird unverändert verwendet, sodass der Formatter vollständig für die finale Ausgabe verantwortlich ist.
* **JSON-Anforderung:** Für die Aktionen `LIST` und `RELATION_LOOKUP` zurückgegebene Werte müssen JSON-serialisierbar bleiben.

#### `parser`: eingehende Daten verarbeiten

Der Hook `parser` überschreibt das Standard-Parsing des Felds für eingereichte oder importierte Daten. Er bildet eine `RequestAction` auf eine `(request, raw) -> value`-Funktion ab.

* **Formulare (`CREATE`, `EDIT`, `INLINE_EDIT`):** `raw` ist die eingereichte Formulareingabe, bzw. eine Liste, wenn `multiple=True`.
* **Importe (`IMPORT`):** `raw` ist der unverarbeitete Zellwert aus der Datei.

```python
from starlette_admin import IntegerField, RequestAction

IntegerField(
    "price",
    parser={
        # Strip currency symbols during import and convert to integer cents
        RequestAction.IMPORT: lambda request, raw: int(
            float(str(raw).strip("$")) * 100
        ),
    },
)
```

Nach dem Parsing durchläuft der zurückgegebene Wert die übliche Validierungskette, erst `required` und dann `validators`, genau so, als hätte das Feld die Daten selbst geparst.

!!! tip "Hooks oder eine Subklasse?"
    Für eine einmalige Anpassung an einem einzelnen Feld brauchen Sie selten eine Subklasse. Übergeben Sie diese Hooks als Konstruktorargumente, um das Lesen, die Anzeigeformatierung und das Eingabeparsing zu handhaben. [Implementieren Sie eine Subklasse des Felds](../advanced/custom-fields.md), wenn Sie die Logik über mehrere Views hinweg wiederverwenden oder wenn Sie die HTML-Rendering-Templates ändern möchten.

### Validierung

Serverseitige Validierung läuft bei jedem Feld, wenn ein Erstellen- oder Bearbeiten-Formular eingereicht wird, sodass fehlerhafte Daten nie die Datenbank erreichen.

Der Lebenszyklus ist festgelegt:

1. **Leere Werte:** Wenn ein eingereichter Wert leer ist, etwa `None`, `""` oder eine leere Collection, wird nur das Flag `required` geprüft. Die Validatoren werden übersprungen.
2. **Gefüllte Werte:** Wenn Daten vorhanden sind, läuft jede Funktion in der Liste `validators` der Reihe nach gegen den geparsten Wert.

#### Signatur eines Validators

Ein Validator erhält vier Argumente: `(request, field, value, form_values)`.

* **`request`:** Das aktuelle Starlette-Request-Objekt.
* **`field`:** Die gerade validierte Feldinstanz.
* **`value`:** Der für dieses Feld eingereichte geparste Wert.
* **`form_values`:** Ein Dictionary mit allen geparsten Formulardaten, nach Feldnamen verschlüsselt, damit Sie andere Felder prüfen können.

Um einen Wert abzulehnen, werfen Sie eine `ValueError`. Das Admin-Panel fängt den ersten Fehler eines Felds ab, überspringt die restlichen Validatoren dieses Felds und sammelt alle Fehler, um sie neben den zugehörigen Eingabefeldern anzuzeigen.

#### Integrierte Validatoren

Das Modul [`starlette_admin.validators`](../api/validators.md) stellt Standardregeln bereit:

```python
from starlette_admin import IntegerField, StringField
from starlette_admin.validators import length, number_range

StringField("title", validators=[length(min=3, max=100)])
IntegerField("price", validators=[number_range(min=0)])
```

#### Benutzerdefinierte und asynchrone Validierung

Schreiben Sie benutzerdefinierte Validatoren als synchrone oder asynchrone Funktionen. Sie erhalten den `request`, sodass sie die Datenbank abfragen können, um komplexe Constraints zu prüfen.

```python
async def unique_slug(request, field, value, form_values):
    if await slug_exists(request.state.session, value):
        raise ValueError("This slug is already taken")


StringField("slug", validators=[unique_slug])
```

Mit dem Argument `form_values` kann ein Validator auf Feldebene auch eine Regel erzwingen, die von einem anderen eingereichten Feld abhängt.

```python
def not_before_start(request, field, value, form_values):
    start = form_values.get("start_date")
    if start is not None and value < start:
        raise ValueError("End date cannot precede the start date")


DateField("end_date", validators=[not_before_start])
```

#### Kontextspezifische Validierungsregeln

* **Beziehungsfelder:** `HasOne` und `HasMany` erhalten während der Validierung die Primärschlüssel der referenzierten Datensätze.
* **Dateifelder:** Die Validierung läuft einmal pro `UploadFile` in der Payload. Siehe [Datei- & Medienfelder](#datei-medienfelder).
* **Feldübergreifende Validierung:** Verwenden Sie `form_values` für eine einfache Abhängigkeit. Für eine Regel, die sich über das gesamte Formular erstreckt, überschreiben Sie stattdessen die Methode `validate()` Ihrer View. Validierung auf View-Ebene läuft erst, nachdem jedes Feld seine eigene Validierungskette passiert hat.

### Benutzerdefinierte Metadaten speichern

`extra` ist ein schlichtes `dict`, das `starlette-admin` nie liest oder schreibt. Verwenden Sie es, um eigene Daten an eine Feldinstanz anzuhängen, etwa für ein benutzerdefiniertes Template, einen Hook in Ihrer [BaseAdmin](../api/admin.md#starlette_admin.base.BaseAdmin)-Subklasse oder jeden anderen Integrationspunkt, ohne das Feld als Subklasse zu implementieren:

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

| Zusätzliches Attribut | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `maxlength` und `minlength` | `int | None` | `None` | HTML-Längenbeschränkungen. |
| `placeholder` | `str | None` | `None` | Platzhaltertext des Eingabefelds. |
| `rows` *(nur TextArea)* | `int` | `6` | Anzahl der sichtbaren Textzeilen. |

### TinyMCEEditorField

Erweitert `TextAreaField` um einen WYSIWYG-Editor aus der TinyMCE-Bibliothek. Er benötigt das Extra-Paket `tinymce`.

```python
from starlette_admin import TinyMCEEditorField

TinyMCEEditorField("content", height=400, toolbar="undo redo | bold italic")
```

!!! note
    Die Attribute `height`, `menubar`, `statusbar` und `toolbar` steuern das UI des Editors. Übergeben Sie jede andere native TinyMCE-Konfiguration über `extra_options`.

### Formatierte Textfelder

Diese `StringField`-Varianten rendern einen passenden HTML-Eingabetyp und formatieren den Wert, wenn der Datensatz angezeigt wird.

* `EmailField` (`type="email"`)
* `URLField` (`type="url"`)
* `PhoneField` (`type="tel"`)
* `ColorField` (`type="color"`)
* `UUIDField` (`type="text"`)
* `IPAddressField` (`type="text"`)

!!! note
    `EmailField`, `URLField`, `UUIDField` und `IPAddressField` fügen jeweils einen passenden Validator hinzu (`email`, `url`, `uuid` und `ip_address` aus [`starlette_admin.validators`](../api/validators.md)), wenn Sie `validators` leer lassen. Übergeben Sie Ihre eigenen `validators`, um dies zu überschreiben.

    `UUIDField` setzt standardmäßig `copy_to_clipboard=True`. `IPAddressField` akzeptiert `ipv4`, standardmäßig `True`, und `ipv6`, standardmäßig `False`, was steuert, welche Adressfamilien sein Standardvalidator akzeptiert.

### PasswordField

Rendert in Formularen ein `<input type="password">`-Element, um zu verschleiern, was die Person tippt.

!!! danger
    `PasswordField` maskiert die Eingabe nur in Erstellen- und Bearbeiten-Formularen. Es überschreibt nicht die Anzeige-Templates, daher werden Werte auf Listen- und Detailseiten als **Klartext** gerendert, und es protokolliert rohe eingereichte Werte auf `DEBUG`-Ebene.

    Setzen Sie `exclude_from_list = True` und `exclude_from_detail = True` auf Passwortfeldern und deaktivieren Sie das `DEBUG`-Logging in der Produktion.

## Numerische Felder

Numerische Felder handhaben Integer, Floats und Dezimalzahlen.

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
| `min` und `max` | Integer, Decimal | Minimaler und maximal zulässiger Wert. |
| `step` | Integer, Decimal | Die Inkrement-Schrittweite. |

!!! note
    `FloatField` funktioniert anders: Es rendert als schlichtes Texteingabefeld, wandelt die Eingabe in einen `float` um und unterstützt weder `min`, `max` noch `step`.

## Datums- & Zeitfelder

Diese Felder verwenden die nativen Datums- und Zeitauswahldialoge des Browsers, gestützt auf die passenden Typen der Standardbibliothek (`datetime.date`, `datetime.datetime` und `datetime.time`).

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

| Zusätzliches Attribut | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `output_format` | `str | None` | `None` | Babel-Anzeigeformat: `"short"`, `"medium"`, `"long"`, `"full"` oder ein eigenes Muster. |
| `search_format` | `str | None` | ORM-spezifisch | Format, das zum Aufbau von Datenbank-Suchqueries verwendet wird. |

!!! note
    Wenn Zeitzonenunterstützung aktiviert ist, konvertiert `DateTimeField` für Sie zwischen der Anzeigezeitzone und der Datenbankzeitzone.

### ArrowField

Eine `DateTimeField`-Variante, gestützt auf ein `Arrow`-Objekt. Außerhalb von Bearbeiten-Formularen zeigt sie eine humanisierte relative Zeit an, etwa „vor 3 Stunden“. Sie benötigt das Paket `arrow`.

## Auswahl- & Collection-Felder

### EnumField

Das universelle Auswahlfeld. Es rendert ein `<select>`-Dropdown-Menü, bzw. ein `select2`-Multi-Select, wenn `multiple=True`. Stützen Sie es auf eine Python-`Enum`-Subklasse, eine Liste von Tupeln oder zur Request-Zeit geladene Choices.

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
| `enum` | `type[Enum] | None` | Baut Choices aus einer Python-`Enum`-Klasse. |
| `choices` | `Sequence | None` | Statische `(value, label)`-Paare oder bloße Werte. |
| `choices_loader` | `Callable | None` | Berechnet Choices pro Request. |
| `multiple` | `bool` | Aktiviert Multi-Select und speichert Werte als Liste. |

!!! important
    Geben Sie genau eines von `enum`, `choices` oder `choices_loader` an.

`TimeZoneField`, `CountryField` und `CurrencyField` sind `EnumField`-Subklassen, gestützt auf Babel-Locale-Daten, wofür das Extra `i18n` benötigt wird. Sie lokalisieren ihre Labels für den aktuellen Request.

### TagsField

Ein Freitext-Tagging-Eingabefeld, aufgebaut auf `select2`. Es speichert eine `list[str]` und benötigt keine vordefinierten Choices.

### ListField

Wrappt ein anderes Feld, um eine geordnete Liste von Werten dieses Typs zu speichern. Es rendert als wiederholbare Zeilen mit Steuerelementen zum Hinzufügen und Entfernen. Der Name des gewrappten Felds wird zum Namen des `ListField`s.

```python
from starlette_admin import ListField, StringField

# Renders a repeatable list of string inputs
fields = [ListField(StringField("gallery_urls"))]
```

### CollectionField

Gruppiert mehrere Unterfelder zu einem verschachtelten Objekt. Verwenden Sie es für eingebettete oder struct-artige Daten, etwa ein eingebettetes MongoDB-Dokument.

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

Rendert einen JSON-Baum und einen Code-Editor und speichert ein Python-`dict`. Übergeben Sie ein standardmäßiges JSON-Schema-Dictionary an `validation_schema` für Feedback auf Client-Seite.

### SlugField

Eine `StringField`-Variante, die sich auf dem Client automatisch aus der Eingabe eines anderen Felds füllt. Eine manuelle Bearbeitung stoppt das automatische Füllen.

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

Ein schreibgeschütztes, virtuelles Feld, das zur Anzeigezeit aus der Modellinstanz abgeleitet wird, ohne dass eine Datenbankspalte dahintersteht. Es baut auf dem [`getter`-Hook](#werte-berechnen-formatieren-und-parsen) auf, den jedes Feld besitzt, und ergänzt die Defaults, die eine virtuelle Spalte braucht: aus Erstellen-Formularen ausgeschlossen, schreibgeschützt, nicht durchsuchbar und nicht sortierbar.

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

Für komplexe oder wiederverwendbare Logik implementieren Sie eine Subklasse von `ComputedField` und überschreiben `parse_obj()`, statt einen Inline-`getter` zu übergeben:

```python
class FullNameField(ComputedField):
    async def parse_obj(self, request, obj) -> str:
        return f"{obj.first_name} {obj.last_name}"
```

`getter` und `parse_obj` erledigen dieselbe Aufgabe: Verwenden Sie `getter` für kurze Ausdrücke, und implementieren Sie eine Subklasse von `ComputedField`, wenn die Logik mehrere Zeilen umfasst oder über Views hinweg wiederverwendet wird. In Bearbeiten-Formularen erscheint das Feld weiterhin als Klartext-Anzeige, sodass die Person den aktuell berechneten Wert sieht.

Jede `ComputedField`-Subklasse behält das Rendering von `StringField`. Um einen Wert zu berechnen, der als anderer Typ gerendert werden soll, etwa ein Datum, ein Badge oder ein Bild, setzen Sie `getter=` direkt auf diesem Feldtyp, zusammen mit den passenden Flags `read_only` und `exclude_from_*`.

## Datei- & Medienfelder

`FileField` rendert ein Datei-Upload-Eingabefeld, und `ImageField` ergänzt eine Bildvorschau und eine Gültigkeitsprüfung. Hängen Sie ein `storage=`-Backend an, um Uploads automatisch zu speichern und ein JSON-`FileInfo`-Dictionary in der Datenbank abzulegen. Die vollständige Konfiguration finden Sie im [File-Storage-Leitfaden](file-storage.md).

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

| Zusätzliches Attribut | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `accept` | `str | None` | `None` | Kommagetrennte Liste akzeptierter Dateiendungen oder MIME-Typen, an das HTML-Attribut `accept` weitergereicht. |
| `multiple` | `bool` | `False` | Akzeptiert mehrere Dateien in einem Feld. |
| `storage` | `BaseStorage | None` | `None` | Storage-Backend, das die Uploads speichert. Ohne dieses übergibt das Feld rohe Uploads an Ihr Backend. |
| `upload_folder` | `str` | `""` | Der relativ zum Storage liegende Ordner für gespeicherte Dateien. |
| `max_size` | `int | None` | `None` | Maximal akzeptierte Uploadgröße in Bytes. |
| `validators` | `list[Validator]` | `[]` | Benutzerdefinierte Validatoren, jeweils aufgerufen als `(request, field, upload)` einmal pro hochgeladener Datei, nach den Prüfungen `accept` und `max_size`. Werfen Sie eine `ValueError`, um abzulehnen. |
| `thumbnail_size` | `tuple[int, int] | None` | `None` | Nur `ImageField`. Wenn gesetzt, generiert Pillow beim Speichern ein begrenztes Thumbnail, und die Listenseite verwendet es anstelle des vollständigen Bildes. |

!!! note
    `ImageField` stellt der `validators`-Liste eine bildbasierte Gültigkeitsprüfung mit Pillow voran. Wenn Pillow installiert ist und ein Storage konfiguriert ist, zeichnet es außerdem `width` und `height` im resultierenden `FileInfo` auf.

Wenn `thumbnail_size` gesetzt ist, generiert das Admin-Panel ein Thumbnail neben dem vollständigen Bild, bewahrt das Seitenverhältnis und skaliert nie hoch, und speichert es unter seinem eigenen Schlüssel. Beispielsweise erhält `covers/cat.jpg` ein Geschwister `covers/cat.thumb.jpg`. Die Listenseite verwendet das Thumbnail automatisch. Zeilen ohne eines, sei es aus bereits vorhandenen Daten oder weil `thumbnail_size` nicht gesetzt ist, fallen auf das vollständige Bild zurück. Ein Fehler bei der Thumbnail-Generierung wird protokolliert und lässt den Upload niemals scheitern.

Die Detailseite öffnet jedes `ImageField`-Bild in einem Lightbox-Dialog, sodass Betrachtende durch Bilder in voller Auflösung blättern können. Bilder, die zum selben Feld gehören (`multiple=True`), werden zu einer Galerie gruppiert.

Sehen Sie sich [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage) für eine vollständig lauffähige App an, einschließlich eines benutzerdefinierten MIME-Type-Validators.

### Ohne einen Storage

Ohne angehängtes `storage=` übergibt das Feld Uploads roh an Ihr Backend, statt sie zu speichern:

* **In Erstellen- und Bearbeiten-Formularen** ist der geparste Wert ein Tupel, `(UploadFile | list[UploadFile] | None, bool)`. Das erste Element ist die rohe Starlette-`UploadFile`, eine Liste, wenn `multiple=True`, oder `None`, wenn nichts ausgewählt wurde. Das zweite Element ist `True`, wenn die Person auf dem Bearbeiten-Formular die Löschen-Checkbox auswählt, was bedeutet, dass sie die vorhandene Datei ohne Ersatz entfernen möchte. Die `create()`- und `edit()`-Logik Ihres Backends speichert den Upload und beachtet das Löschen-Flag.
* **Auf Listen- und Detailseiten** erwartet das Feld, dass der Wert drei Schlüssel als `dict` oder drei Attribute als Objekt bereitstellt: `url`, erforderlich, das Linkziel; `filename`, das Anzeige-Label; und `content_type`, das das Dateityp-Icon auswählt.

Dieser Vertrag ist der Weg, über den die folgenden ORM-Integrationen ihre eigene Dateibehandlung in dasselbe Feld einhängen.

### ORM-native Dateispalten

**MongoEngine** unterstützt `mongoengine.FileField` und `mongoengine.ImageField` out of the box, mit **GridFS** als Storage. Das Admin-Panel lädt für Sie in GridFS hoch, liefert daraus Dateien aus und löscht dort Dateien. Sie benötigen keine `storage=`-Konfiguration: Listen Sie das Feld namentlich auf.

**SQLAlchemy** erhält dieselbe Behandlung durch [sqlalchemy-file](https://jowilf.github.io/sqlalchemy-file/). Deklarieren Sie dessen Spaltentypen `FileField` oder `ImageField` auf Ihren Modellen, und `starlette-admin` erkennt sie, rendert das passende Admin-Feld und registriert eine Route, um die gespeicherten Dateien auszuliefern. Sie konfigurieren den Storage über sqlalchemy-files eigenes `StorageManager`, gestützt auf Apache-Libcloud-Container, und Uploads treten der Session-Transaktion bei, sodass eine zurückgerollte Session die gespeicherte Datei verwirft.

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

Sehen Sie sich [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file) für eine vollständige App mit mehreren Storages, Content-Type-Validierung und `multiple=True`-Feldern an.

## HasOne & HasMany

Beziehungsfelder, die als `select2`-Eingabefelder gerendert werden, gestützt auf den Suchendpoint der referenzierten View.

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

Der Parameter `key` zeigt auf die passende `ModelView`. Registrieren Sie beide Views auf derselben `Admin`-Instanz, damit die Schlüssel aufgelöst werden.

---

## Was kommt als Nächstes

* [Filter](filters.md): Den Filterbuilder auf Ihren Listenseiten anpassen.
* [File Storage](file-storage.md): Storage-Backends für `FileField` und `ImageField` konfigurieren.
* [Benutzerdefinierte Felder](../advanced/custom-fields.md): Ein benutzerdefiniertes Feld bauen.
