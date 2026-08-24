---
title: Sicherheit
description: Entdecken Sie die integrierten Sicherheitsfunktionen von starlette-admin,
  darunter CSRF-Schutz, sichere Datei-Uploads und Zugriffskontrolle.
source_hash: d16d4b0beefd5dc8580f8d65abaa28fda407896efff2ea2c3988ec3bf93277a4
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/security/)
<!-- translation-notice:end -->

# Sicherheit

`starlette-admin` enthält Schutzmechanismen gegen die Risiken, die mit dem Betrieb eines Admin-Panels einhergehen. Der Schutz vor Cross-Site-Request-Forgery (CSRF) sowie die Begrenzungen der Export- und Import-Payloadgrößen sind aktiv, sobald Sie die Klasse `Admin` instanziieren.

Diese Defaults härten das Interface gegen gängige Angriffe, ersetzen aber nicht die übliche Deployment-Sicherheit. Sie sind weiterhin verantwortlich für Transportschichtsicherheit (HTTPS/TLS), Netzwerk-Zugriffskontrolle, Benutzerauthentifizierung (siehe [Authentifizierung](auth.md)), Dependency-Updates und Security-Reviews. Diese Seite behandelt die automatischen Schutzmechanismen, diejenigen, die Sie konfigurieren können, und die Einstellung `secret_key`, die Sie in der Produktion benötigen.

## Was Sie automatisch erhalten

```python
from sqlalchemy import create_engine
from starlette.applications import Starlette
from starlette_admin.contrib.sqla import Admin

engine = create_engine("sqlite:///admin.sqlite")
app = Starlette()
admin = Admin(engine, title="My Admin")
admin.mount_to(app)
```

Auch ohne Sicherheitsparameter wehrt sich die Admin-Instanz gegen mehrere gängige Schwachstellen:

* **CSRF-Schutz:** Aktiv bei jedem Formular und jedem jQuery-AJAX-Aufruf, einschließlich Zeilenaktionen und Bestätigungsdialogen.
* **Flash-Nachrichten:** In einem signierten Cookie übertragen, sodass Sie keine `SessionMiddleware` benötigen.
* **Bereinigung von Dateinamen:** Angewendet auf jeden Datei-Upload, der durch ein Storage-Backend läuft.
* **Verifizierung des Bildinhalts:** Validiert `ImageField`-Uploads auf Byte-Ebene mit Pillow, sofern installiert.
* **Export-Limits:** Auf 100.000 Zeilen pro Request begrenzt, um Ressourcenerschöpfung und Denial of Service zu verhindern.
* **Import-Limits:** Auf 10 MB pro Request begrenzt, um Speichererschöpfung einzudämmen.

Ein weiterer Schutz ist verfügbar, ist aber standardmäßig deaktiviert: Escaping, das Formel-Injection in CSV- und Tabellenkalkulationsexporten (XLSX, XLS, ODS) verhindert. Siehe [Formel-Injection](#formel-injection).

Die folgenden Abschnitte erläutern diese Schutzmechanismen und wie Sie die Schwellenwerte anpassen, die Sie steuern können.

## Der Secret Key

```python
admin = Admin(engine, title="My Admin", secret_key="a-long-random-string")
```

Der `secret_key` ist die kryptografische Wurzel für die Signierung zweier Cookies: dem CSRF-Token und dem Flash-Nachrichten-Cookie. Beide verwenden [itsdangerous](https://itsdangerous.palletsprojects.com/), sodass Clients die Cookies zwar lesen, die Payload aber ohne den Schlüssel weder fälschen noch manipulieren können.

!!! warning "Setzen Sie in der Produktion immer einen expliziten Secret Key"
    Wenn Sie `secret_key` weglassen, generiert die `Admin`-Instanz beim Start einen zufälligen Schlüssel und gibt eine `UserWarning` aus. Das ist für eine lokale Demo in Ordnung, bricht aber in Multi-Worker-Deployments. Wenn Sie mehrere Worker betreiben, etwa `uvicorn --workers 4`, Gunicorn oder mehrere Container, generiert jeder Prozess seinen eigenen Schlüssel. Ein vom Worker signiertes CSRF-Token, der das Formular ausgeliefert hat, schlägt dann bei der Validierung fehl, wenn ein anderer Worker die Übermittlung verarbeitet, was zu Fehlern wegen ungültiger CSRF-Token bei einem scheinbar zufälligen Anteil der Requests führt. Setzen Sie `secret_key` explizit, bevor Sie über einen einzelnen Prozess hinaus skalieren.

## CSRF-Schutz

`CSRFMiddleware` verwendet ein signiertes Double-Submit-Cookie-Muster, um Cross-Site-Request-Forgery zu verhindern. Es stellt ein `starlette_admin_csrftoken`-Cookie bei sicheren HTTP-Methoden aus (`GET`, `HEAD`, `OPTIONS` und `TRACE`). Bei verändernden Requests validiert es dieses Cookie gegen entweder einen `X-CSRFToken`-Header oder ein verstecktes Formularfeld `csrftoken`.

Jedes integrierte Admin-Template (`create`, `edit` und `login`) rendert das versteckte Feld für Sie:

```jinja
{{ csrf_input(request) }}

```

Das gebündelte JavaScript hängt außerdem den Header an jeden jQuery-AJAX-Aufruf an, sodass Zeilenaktionen und andere asynchrone Interaktionen ohne zusätzlichen Code geschützt sind. Rufen Sie `csrf_input(request)` selbst nur dann auf, wenn Sie benutzerdefinierte Formulare außerhalb der Standard-Templates erstellen. Siehe [Benutzerdefinierte Views](custom-views.md).

## Datei-Uploads

Jeder Upload, der durch ein [Storage](file-storage.md)-Backend läuft, wird mit `secure_filename` bereinigt. Pfadkomponenten für Directory Traversal werden entfernt, und Zeichen außerhalb von `[A-Za-z0-9_.-]` werden zu Unterstrichen (`_`). Das lässt sich nicht deaktivieren.

Legen Sie Content-Type- und Größenbeschränkungen pro Feld mit `accept` und `max_size` fest:

```python
from starlette_admin.fields import FileField


class DocumentView:
    invoice = FileField(accept=".pdf,.docx", max_size=5 * 1024 * 1024)  # 5 MB limit
```

Ohne diese akzeptiert ein `FileField` jeden Dateityp in beliebiger Größe. `ImageField` ist die Ausnahme: Es verwendet standardmäßig `accept="image/*"`, und wenn Pillow installiert ist, fügt es einen Validator hinzu, der den Upload mit `PIL.Image` öffnet, um zu bestätigen, dass die Bytes als Bild dekodierbar sind, statt auf vom Browser gelieferte Metadaten zu vertrauen.

!!! important "Erzwingen Sie Request-Größenlimits auf Webserver-Ebene"
    Verlassen Sie sich nicht allein auf `max_size`. Diese Prüfung auf Anwendungsebene läuft erst, nachdem der Server die vollständige Request-Payload empfangen hat. Um Denial-of-Service-Angriffe (DoS) zu verhindern, begrenzen Sie die Requestbody-Größe in Ihrer Webserver-Konfiguration, etwa `client_max_body_size` in NGINX oder die entsprechende Einstellung an Ihrem Load Balancer.

!!! warning "Dateiendungen und Content-Type-Header lassen sich fälschen"
    Das Attribut `accept` stützt sich auf die Dateiendung und den vom Browser bereitgestellten `Content-Type`-Header, und beides kann ein Angreifer fälschen. Eine Datei, die wie `invoice.pdf` aussieht, kann eine ausführbare Payload enthalten.

    Kombinieren Sie für Nicht-Bilddateien `accept` mit einem benutzerdefinierten Validator, der die Magic Bytes der Datei prüft. Bibliotheken wie [`filetype`](https://github.com/h2non/filetype.py) und [`python-magic`](https://github.com/ahupp/python-magic) verifizieren das tatsächliche Dateiformat:

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

    Wenden Sie den Validator mit `FileField(..., validators=[validate_document_type])` an. Für eine vollständige Implementierung siehe [`examples/04-filestorage`](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

## Export-Limits

```python
from starlette_admin.export import ExportConfig

admin = Admin(engine, title="My Admin", export_config=ExportConfig(max_rows=50_000))
```

| Attribut | Defaultwert | Beschreibung |
| --- | --- | --- |
| `max_rows` | `100_000` | Maximale Anzahl an Zeilen pro Export-Request. Beim Überschreiten des Limits wird eine Fehlermeldung als Flash-Nachricht angezeigt und der Benutzer zur Listenseite zurückgeführt. Setzen Sie den Wert auf `None`, um das Limit zu entfernen. |
| `restrict_url_download` | `True` | Gilt für rein URL-basierte Dateireferenzen. Beschränkt das Export-ZIP auf Dateien, deren Ursprung mit der `base_url` des Admins übereinstimmt. |
| `max_download_size` | `20 MB` | Maximale Größe für einen rein URL-basierten Download, der in ein Export-ZIP gepackt wird. Größere Dateien werden übersprungen und mit einer Warnung protokolliert. |
| `safe_download_url` | `None` | Ein benutzerdefinierter Callback mit der Signatur `(url, request) -> str`. |

Informationen dazu, wie das ZIP-Bundle erstellt wird, finden Sie unter [Export & Import](export-import.md).

### Formel-Injection

Tabellenkalkulationssoftware interpretiert einen Zellwert, der mit `=`, `+`, `-` oder `@` beginnt, als Formel. Speichert ein nicht vertrauenswürdiger Benutzer eine Payload wie `=HYPERLINK(...)` in ein exportiertes Feld, führt die Tabellenkalkulationsanwendung sie aus, wenn ein Administrator die Datei öffnet. Dies ist als CSV-Injection bzw. Formel-Injection bekannt.

Da exportierte Werte genau so geschrieben werden, wie sie in der Datenbank gespeichert sind, ist das Formel-Escaping **standardmäßig deaktiviert**. Sowohl der CSV-Exporter als auch die Tablib-Exporter für Tabellenkalkulationen (`xlsx`, `xls` und `ods`) akzeptieren einen Parameter `escape_formulas`. Wenn Sie ihn einschalten, erhält jeder String, der mit einem Trigger-Zeichen beginnt, ein führendes einfaches Anführungszeichen (`'`), wodurch die Anwendung gezwungen wird, den Wert als reinen Text darzustellen.

!!! warning "Aktivieren Sie das Formel-Escaping für von Benutzern bereitgestellte Daten"
    Wenn auch nur ein Nicht-Administrator-Konto Daten in ein exportiertes Feld schreiben kann, setzen Sie `escape_formulas=True`. Andernfalls können Angreifer-kontrollierte Werte Systembefehle ausführen oder Daten exfiltrieren, wenn jemand die Datei lokal öffnet.

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

| Attribut | Defaultwert | Beschreibung |
| --- | --- | --- |
| `max_upload_size` | `10 MB` | Wird geprüft, sobald der Request ankommt, bevor irgendetwas geparst wird. |
| `max_rows` | `100_000` | Maximale Anzahl an Zeilen pro Import-Request. Der Admin zählt die Payload in einem Vorab-Durchlauf und lehnt eine größere Datei mit einer HTTP-400-Response ab, bevor er einen Datensatz in der Datenbank erstellt. Setzen Sie den Wert auf `None`, um das Limit zu entfernen. |

Der Import lehnt ZIP-Archive grundsätzlich ab, wodurch das Risiko von ZIP-Bomben-Angriffen auf diesen Endpoint entfällt. `FileField` und `ImageField` sind ebenfalls von Massenimporten ausgeschlossen, da sie standardmäßig `exclude_from_import=True` verwenden, sodass Benutzer Dateien einzeln über die Formulare zum Erstellen oder Bearbeiten anhängen.

## Was diese Seite nicht abdeckt

Die integrierten Schutzmechanismen adressieren Risiken innerhalb der Admin-Codebasis. Sie sichern Ihre Architektur nicht als Ganzes. Diese operativen Maßnahmen liegen außerhalb des Geltungsbereichs von `starlette-admin` und bleiben in Ihrer Verantwortung:

* **Transportsicherheit:** Stellen Sie das Admin-Panel über HTTPS bereit. Die CSRF- und Flash-Cookies sind signiert, aber nicht verschlüsselt, sodass jeder, der unverschlüsselten HTTP-Traffic abfängt, sie lesen kann.
* **Authentifizierung und Autorisierung:** Die `Admin`-Instanz ist öffentlich, bis Sie einen `AuthProvider` anhängen. Ohne einen solchen sind jeder Endpoint und jede Route offen. Siehe [Authentifizierung](auth.md).
* **Netzwerkexposition:** Wenn das Admin-Panel keinen öffentlichen Zugriff benötigt, stellen Sie es hinter eine Firewall, ein VPN oder eine IP-Allowlist.
* **Dependency-Hygiene:** Verfolgen Sie Security-Advisories und halten Sie `starlette-admin`, Starlette, Ihren ORM-Treiber und den Rest Ihrer Dependencies auf dem neuesten Stand.
* **Aktionen nach der Authentifizierung:** CSRF-Schutz und Upload-Validierung beschränken nicht, was ein angemeldeter Benutzer tun kann. Granulare Zugriffskontrolle ergibt sich vollständig aus den Berechtigungsprüfungen, die Sie in `is_accessible`, `can_create`, `can_edit` und `can_delete` schreiben. Siehe [Authentifizierung](auth.md).

Behandeln Sie diese Seite als Anleitung zur Konfiguration des Admin-Pakets, nicht als Checkliste zur Absicherung Ihres gesamten Production-Deployments.

---

## Nächste Schritte

* **[Export & Import](export-import.md):** Der Exportdialog, der Lebenszyklus der Importvorschau und das Layout des ZIP-Bundles.
* **[File Storage](file-storage.md):** Muster zum Konfigurieren von Storage-Backends für `FileField` und `ImageField`.
* **[Authentifizierung](auth.md):** Wie `secret_key` Login-Sessions und CSRF-Prüfungen absichert, sobald Sie einen Auth-Provider hinzufügen.
