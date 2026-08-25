---
title: Sicherheit
description: Entdecken Sie die integrierten Sicherheitsfunktionen von starlette-admin,
  darunter CSRF-Schutz, sichere Datei-Uploads und Zugriffskontrolle.
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# Sicherheit

`starlette-admin` enthält Schutzmechanismen für die Risiken, die mit dem Betrieb eines Administrationspanels verbunden sind. Der Schutz vor Cross-Site Request Forgery (CSRF) sowie die Begrenzung der Export- und Import-Payload-Größen sind aktiv, sobald Sie die Klasse `Admin` instanziieren.

Diese Standardeinstellungen härten die Oberfläche gegen gängige Angriffe, ersetzen jedoch nicht die übliche Absicherung der Deployment-Umgebung. Sie sind weiterhin verantwortlich für die Sicherheit auf der Transportschicht (HTTPS/TLS), die Netzwerk-Zugriffskontrolle, die Benutzerauthentifizierung (siehe [Authentication](auth.md)), Aktualisierungen der Abhängigkeiten und Sicherheitsüberprüfungen. Diese Seite behandelt die automatischen Schutzmechanismen, diejenigen, die Sie konfigurieren können, und die Einstellung `secret_key`, die Sie in der Produktion benötigen.

## Automatisch enthaltene Schutzmechanismen

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

Auch ohne Sicherheitsparameter wehrt die Admin-Instanz mehrere häufige Schwachstellen ab:

* **CSRF-Schutz:** Auf jedem Formular und jedem jQuery-AJAX-Aufruf aktiv, einschließlich Zeilenaktionen und Bestätigungsdialogen.
* **Flash-Messages:** In einem signierten Cookie übertragen, sodass Sie `SessionMiddleware` nicht benötigen.
* **Bereinigung von Dateinamen:** Wird auf jeden Datei-Upload angewendet, der ein Storage-Backend durchläuft.
* **Verifizierung des Bildinhalts:** Validiert Uploads von `ImageField` auf Byte-Ebene mit Pillow, sofern es installiert ist.
* **Export-Limits:** Begrenzt auf 100.000 Zeilen pro Anfrage, um Ressourcenerschöpfung und Denial of Service zu verhindern.
* **Import-Limits:** Begrenzt auf 10 MB pro Anfrage, um eine Speichererschöpfung einzudämmen.

Ein weiterer Schutzmechanismus ist verfügbar, aber standardmäßig deaktiviert: das Escaping, das Formel-Injection in CSV- und Tabellenkalkulationsexports (XLSX, XLS, ODS) verhindert. Siehe [Formel-Injection](#formula-injection).

Die folgenden Abschnitte erläutern diese Schutzmechanismen und wie Sie die Schwellenwerte anpassen, die Sie steuern können.

## Der Secret Key

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

Der `secret_key` ist die kryptografische Grundlage für die Signierung zweier Cookies: des CSRF-Tokens und des Flash-Message-Cookies. Beide verwenden [itsdangerous](https://itsdangerous.palletsprojects.com/), sodass Clients die Cookies zwar lesen, aber die Payload ohne den Schlüssel weder fälschen noch manipulieren können.

!!! warning "Setzen Sie in der Produktion immer einen expliziten Secret Key"
    Wenn Sie `secret_key` auslassen, generiert die `Admin`-Instanz beim Start einen zufälligen Schlüssel und gibt ein `UserWarning` aus. Für eine lokale Demo ist das unproblematisch, in Multi-Worker-Deployments führt es jedoch zu Fehlern. Wenn Sie mehrere Worker betreiben, etwa `uvicorn --workers 4`, Gunicorn oder mehrere Container, generiert jeder Prozess seinen eigenen Schlüssel. Ein vom Worker signiertes CSRF-Token, der das Formular ausgeliefert hat, schlägt dann bei der Validierung fehl, wenn ein anderer Worker die Übermittlung verarbeitet – dies führt zu Fehlern wegen ungültiger CSRF-Token bei einem scheinbar zufälligen Anteil der Anfragen. Setzen Sie `secret_key` explizit, bevor Sie über einen einzelnen Prozess hinaus skalieren.

## CSRF-Schutz

`CSRFMiddleware` verwendet ein signiertes Double-Submit-Cookie-Muster, um Cross-Site Request Forgery zu verhindern. Es setzt ein Cookie namens `starlette_admin_csrftoken` bei sicheren HTTP-Methoden (`GET`, `HEAD`, `OPTIONS` und `TRACE`). Bei verändernden Anfragen validiert es dieses Cookie entweder gegen einen `X-CSRFToken`-Header oder ein verstecktes Formularfeld namens `csrftoken`.

Jede eingebaute Admin-Vorlage (`create`, `edit` und `login`) rendert das versteckte Feld für Sie:

```jinja
{{ csrf_input(request) }}

```

Das gebündelte JavaScript fügt außerdem den Header an jeden jQuery-AJAX-Aufruf an, sodass Zeilenaktionen und andere asynchrone Interaktionen ohne zusätzlichen Code geschützt sind. Rufen Sie `csrf_input(request)` nur selbst auf, wenn Sie eigene Formulare außerhalb der Standardvorlagen erstellen. Siehe [Custom Views](custom-views.md).

## Datei-Uploads

Jeder Upload, der ein [Storage](file-storage.md)-Backend durchläuft, wird mit `secure_filename` bereinigt. Pfadkomponenten für Directory Traversal werden entfernt, und Zeichen außerhalb von `[A-Za-z0-9_.-]` werden durch Unterstriche (`_`) ersetzt. Dies lässt sich nicht deaktivieren.

Legen Sie Einschränkungen für Content-Type und Größe pro Feld mit `accept` und `max_size` fest:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

Ohne diese Angaben akzeptiert ein `FileField` beliebige Dateitypen und -größen. Eine Ausnahme bildet `ImageField`: Es verwendet standardmäßig `accept="image/*"`, und wenn Pillow installiert ist, fügt es einen Validator hinzu, der den Upload mit `PIL.Image` öffnet, um zu bestätigen, dass die Bytes als Bild dekodierbar sind – statt sich auf vom Browser gelieferte Metadaten zu verlassen.

!!! important "Erzwingen Sie Größenlimits für Anfragen auf Webserver-Ebene"
    Verlassen Sie sich nicht allein auf `max_size`. Diese Prüfung auf Anwendungsebene läuft erst, nachdem der Server die vollständige Request-Payload empfangen hat. Um Denial-of-Service-Angriffe (DoS) zu verhindern, begrenzen Sie die Größe des Request-Bodys in Ihrer Webserver-Konfiguration, etwa über `client_max_body_size` in NGINX oder die entsprechende Einstellung Ihres Load Balancers.

!!! warning "Dateiendungen und Content-Type-Header lassen sich fälschen"
    Das Attribut `accept` stützt sich auf die Dateiendung und den vom Browser bereitgestellten `Content-Type`-Header, und ein Angreifer kann beides manipulieren. Eine Datei, die wie `invoice.pdf` aussieht, kann eine ausführbare Payload enthalten.

    Kombinieren Sie für Nicht-Bilddateien `accept` mit einem eigenen Validator, der die Magic Bytes der Datei prüft. Bibliotheken wie [`filetype`](https://github.com/h2non/filetype.py) und [`python-magic`](https://github.com/ahupp/python-magic) verifizieren das tatsächliche Dateiformat:

    ```python
    import filetype
    from starlette.datastructures import UploadFile
    from starlette.requests import Request
    from starlette_admin.fields import BaseField

    ALLOWED_DOCUMENT_MIME_TYPES = {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def validate_document_type(
        request: Request, field: BaseField, upload: UploadFile, form_values: dict
    ) -> None:
        upload.file.seek(0)
        try:
            header = upload.file.read(2048)
            kind = filetype.guess(header)
            detected = kind.mime if kind else "application/octet-stream"
        finally:
            upload.file.seek(0)

        if detected not in ALLOWED_DOCUMENT_MIME_TYPES:
            raise ValueError(
                f"Invalid file type '{detected}'. Only PDF, DOC, and DOCX are allowed."
            )
    ```

    Wenden Sie den Validator mit `FileField(..., validators=[validate_document_type])` an. Eine vollständige Implementierung finden Sie unter [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

## Export-Limits

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribut | Standardwert | Beschreibung |
| --- | --- | --- |
| `max_rows` | `100_000` | Maximale Anzahl an Zeilen pro Exportanfrage. Bei Überschreitung des Limits wird eine Fehlermeldung angezeigt und der Benutzer zur Listenansicht zurückgeführt. Setzen Sie den Wert auf `None`, um das Limit zu entfernen. |
| `restrict_url_download` | `True` | Gilt ausschließlich für Dateireferenzen per URL. Beschränkt das Export-ZIP auf Dateien, deren Ursprung mit dem `base_url` des Admins übereinstimmt. |
| `max_download_size` | `20 MB` | Maximale Größe eines URL-basierten Downloads, der in ein Export-ZIP gepackt wird. Größere Dateien werden übersprungen und mit einer Warnung protokolliert. |
| `safe_download_url` | `None` | Ein eigener Callback mit der Signatur `(url, request) -> str`. |

Wie das ZIP-Archiv zusammengesetzt wird, erfahren Sie unter [Export & Import](export-import.md).

### Formel-Injection {#formula-injection}

Tabellenkalkulationssoftware interpretiert einen Zellwert, der mit `=`, `+`, `-` oder `@` beginnt, als Formel. Speichert ein nicht vertrauenswürdiger Benutzer eine Payload wie `=HYPERLINK(...)` in einem exportierten Feld, führt die Tabellenkalkulationsanwendung sie aus, sobald ein Administrator die Datei öffnet. Dies ist als CSV-Injection bzw. Formel-Injection bekannt.

Da exportierte Werte exakt so geschrieben werden, wie sie in der Datenbank gespeichert sind, ist das Formel-Escaping **standardmäßig deaktiviert**. Sowohl der CSV-Exporter als auch die Tablib-Exporter für Tabellenformate (`xlsx`, `xls` und `ods`) akzeptieren einen Parameter `escape_formulas`. Wenn Sie ihn aktivieren, erhält jede Zeichenfolge, die mit einem Trigger-Zeichen beginnt, ein führendes einfaches Anführungszeichen (`'`), wodurch die Anwendung den Wert als reinen Text rendert.

!!! warning "Aktivieren Sie das Formel-Escaping für benutzergelieferte Daten"
    Wenn auch Nicht-Administrator-Konten Daten in ein exportiertes Feld schreiben können, setzen Sie `escape_formulas=True`. Andernfalls können Angreifer gesteuerte Werte Systembefehle ausführen oder Daten exfiltrieren, sobald jemand die Datei lokal öffnet.

Um das Escaping zu aktivieren, ersetzen Sie den Formatstring durch eine explizite Exporter-Instanz:

```python
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.export import CsvExporter, TablibExporter


class ProductView(ModelView):
    exporters = [
        CsvExporter(escape_formulas=True),
        TablibExporter("xlsx", escape_formulas=True),
        "json",
    ]
```

## Import-Limits

```python
from starlette_admin.importers import ImportConfig

admin = Admin(
    engine,
    title="My Admin",
    import_config=ImportConfig(
        max_upload_size=5 * 1024 * 1024,
        max_rows=50_000,
    ),
)
```

| Attribut | Standardwert | Beschreibung |
| --- | --- | --- |
| `max_upload_size` | `10 MB` | Wird geprüft, sobald die Anfrage eingeht, noch vor jeglichem Parsing. |
| `max_rows` | `100_000` | Maximale Anzahl an Zeilen pro Importanfrage. Der Admin zählt die Payload in einem Vorablauf und lehnt größere Dateien mit einer HTTP-400-Antwort ab, bevor ein Datensatz in der Datenbank erstellt wird. Setzen Sie den Wert auf `None`, um das Limit zu entfernen. |

Der Import lehnt ZIP-Archive grundsätzlich ab, womit das Risiko von ZIP-Bomben-Angriffen auf diesen Endpoint entfällt. `FileField` und `ImageField` sind zudem von Bulk-Imports ausgeschlossen, da sie standardmäßig `exclude_from_import=True` verwenden; Benutzer hängen Dateien daher einzeln über die Create- oder Edit-Formulare an.

## Was diese Seite nicht abdeckt

Die eingebauten Schutzmechanismen adressieren Risiken innerhalb der Admin-Codebasis. Sie sichern Ihre Architektur nicht als Ganzes. Die folgenden operativen Maßnahmen liegen außerhalb des Geltungsbereichs von `starlette-admin` und bleiben Ihre Verantwortung:

* **Transportsicherheit:** Betreiben Sie den Admin über HTTPS. Die CSRF- und Flash-Cookies sind signiert, aber nicht verschlüsselt, sodass jeder, der unverschlüsselten HTTP-Verkehr abfängt, sie lesen kann.
* **Authentifizierung und Autorisierung:** Die `Admin`-Instanz ist öffentlich zugänglich, bis Sie einen `AuthProvider` anhängen. Ohne einen solchen sind alle Endpoints und Routen offen. Siehe [Authentication](auth.md).
* **Netzwerk-Exposition:** Benötigt das Admin-Panel keinen öffentlichen Zugriff, platzieren Sie es hinter einer Firewall, einem VPN oder einer IP-Allowlist.
* **Abhängigkeits-Hygiene:** Verfolgen Sie Security Advisories und halten Sie `starlette-admin`, Starlette, Ihren ORM-Treiber und die übrigen Abhängigkeiten aktuell.
* **Aktionen nach der Authentifizierung:** CSRF-Schutz und Upload-Validierung schränken nicht ein, was ein angemeldeter Benutzer tun darf. Granulare Zugriffskontrolle ergibt sich ausschließlich aus den Berechtigungsprüfungen, die Sie in `is_accessible`, `can_create`, `can_edit` und `can_delete` schreiben. Siehe [Authentication](auth.md).

Behandeln Sie diese Seite als Leitfaden zur Konfiguration des Admin-Pakets, nicht als Checkliste zur Absicherung Ihres gesamten Produktions-Deployments.

---

## Wie es weitergeht

* **[Export & Import](export-import.md):** Der Export-Dialog, der Lebenszyklus der Importvorschau und das Layout des ZIP-Archivs.
* **[File Storage](file-storage.md):** Muster zur Konfiguration von Storage-Backends für `FileField` und `ImageField`.
* **[Authentication](auth.md):** Wie `secret_key` Anmeldesitzungen und CSRF-Prüfungen steuert, sobald Sie einen Auth-Provider hinzufügen.
