---
title: Dateispeicher
description: Verwalten Sie Datei- und Bild-Uploads in starlette-admin mit LocalStorage
  oder einem S3-kompatiblen Storage-Backend.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Dateispeicher

`FileField` und `ImageField` speichern hochgeladene Dateien über ein Storage-Backend, das Sie mit dem Parameter `storage` des Felds festlegen.

Erstellen Sie ein Storage-Backend einmal und verwenden Sie es für jedes Feld wieder, das Dateien am selben Ort ablegt.


## Minimalbeispiel

```python hl_lines="8 12 31"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import JSON, Integer, String, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from starlette_admin import ImageField
from starlette_admin.contrib.sqla import Admin, ModelView
from starlette_admin.storage import LocalStorage

engine = create_engine("sqlite:///admin.sqlite")

local = LocalStorage(base_dir="uploads", name="local")


class Base(DeclarativeBase):
    pass


class Book(Base):
    __tablename__ = "book"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    cover: Mapped[dict | None] = mapped_column(JSON, nullable=True)


class BookView(ModelView):
    fields = [
        "id",
        "title",
        ImageField("cover", storage=local, upload_folder="covers"),
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(lifespan=lifespan)

admin = Admin(engine, title="Bookstore", secret_key="change-me")
admin.add_view(BookView(Book))
admin.mount_to(app)
```

Wenn ein Benutzer über das Admin-Panel ein Cover hochlädt, dann:

* speichert das Admin-Panel die Datei unter `uploads/covers/`
* legt das Admin-Panel ein JSON-Metadatenobjekt in der Spalte `cover` ab

Die Datenbank enthält niemals die Datei selbst, einen Dateisystempfad oder Binärdaten.


## Was in der Datenbank gespeichert wird

Das Admin-Panel repräsentiert einen Upload als serialisiertes [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo)-Objekt im Modellfeld.

```json
{
  "filename": "product-photo.jpg",
  "content_type": "image/jpeg",
  "size": 204800,
  "storage": "s3",
  "key": "uploads/products/a1b2c3_product-photo.jpg",
  "url": "https://..."
}
```

* `filename`: bereinigter ursprünglicher Dateiname, wird zur Anzeige verwendet
* `content_type`: beim Upload erkannter MIME-Typ
* `size`: Dateigröße in Bytes
* `storage`: registrierter Name des Backends, wird verwendet, um den Dateispeicherort für die URL-Generierung und die Löschung aufzulösen
* `key`: relativer Pfad oder Objektschlüssel innerhalb des Storages
* `url`: zwischengespeicherte öffentliche URL

`LocalStorage` speichert einen leeren Wert für `url`, da URLs vom aktiven Request abhängen. `S3Storage` speichert eine öffentliche oder eine Presigned-URL, je nach Ihrer Konfiguration.

Unabhängig vom Backend generiert `FileField` die URL zur Renderzeit mit `storage.url()` neu, statt dem gespeicherten Wert zu vertrauen.

`ImageField` fügt `width` und `height` hinzu.

Das Admin-Panel bereinigt jeden Dateinamen mit `secure_filename`, bevor er gespeichert wird: Es entfernt Pfadkomponenten und ersetzt Zeichen außerhalb von `[A-Za-z0-9_.-]` durch `_`. Siehe [Sicherheit](security.md).


## Storage-Backends

### Lokaler Speicher

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | erforderlich | Stammverzeichnis für gespeicherte Dateien. Wird für Sie erstellt, falls es nicht existiert. |
| `name` | `str | None` | `"local"` | Registrierungsname, der das Backend identifiziert. Muss eindeutig sein, wenn Sie mehrere Instanzen verwenden. |

Das Admin-Panel stellt Dateien über diese Route bereit:

```
/_files/{storage}/{path}
```

Sie benötigen keine zusätzliche Konfiguration für statische Dateien.

`LocalStorage.url()` baut URLs aus dem aktuellen Request-Kontext auf, daher bleibt das gespeicherte Feld `url` leer und wird bei Bedarf neu berechnet.

!!! note
    Ein Codebeispiel finden Sie unter [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

### Amazon-S3-Speicher

```python
from starlette_admin.storage import S3Storage

s3 = S3Storage(
    bucket="my-bucket",
    prefix="admin/",
    region="eu-west-1",
    public=False,
)
```

Installieren Sie die optionalen Abhängigkeiten:

```bash
pip install starlette-admin[s3]
```

Dies installiert `aiobotocore`.

| Parameter | Typ | Defaultwert | Beschreibung |
| --- | --- | --- | --- |
| `bucket` | `str` | erforderlich | Name des S3-Buckets. |
| `prefix` | `str` | `"uploads/"` | Key-Präfix, das auf jedes gespeicherte Objekt angewendet wird. |
| `region` | `str` | `"us-east-1"` | AWS-Region, die für Signierung und URL-Generierung verwendet wird. |
| `access_key` und `secret_key` | `str | None` | `None` | Optionale Zugangsdaten. Fällt auf die Standard-AWS-Credential-Chain zurück. |
| `public` | `bool` | `True` | Bei `True` wird eine öffentliche URL zurückgegeben. Bei `False` werden Presigned-URLs generiert. |
| `expires` | `int` | `3600` | Ablaufzeit für Presigned-URLs, in Sekunden. |
| `endpoint_url` | `str | None` | `None` | Benutzerdefinierter S3-kompatibler Endpoint, z. B. MinIO, R2 oder B2. |
| `name` | `str | None` | `"s3"` | Registrierungsname, der das Backend identifiziert. |

Wenn Sie `endpoint_url` angeben, baut das Admin-Panel URLs wie folgt auf:

```
{endpoint_url}/{bucket}/{key}
```

statt das AWS-Virtual-Hosted-Format zu verwenden.


!!! important
    Dateifelder müssen auf eine JSON-fähige Datenbankspalte abgebildet werden. Die Datenbank enthält nur die Metadaten. Das Storage-Backend enthält die Datei selbst.


## Mehrere Dateien (`multiple=True`)

Setzen Sie `multiple=True` auf einem `FileField` oder `ImageField`, um mehrere Uploads in einem Feld zu akzeptieren.

```python
from starlette_admin import FileField
from starlette_admin.contrib.sqla import ModelView
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads/attachments", name="attachments")


class TicketView(ModelView):
    fields = [
        "id",
        "subject",
        FileField(
            "attachments",
            storage=local,
            upload_folder="tickets/",
            multiple=True,
        ),
    ]
```

Die Datenbank speichert eine JSON-Liste von `FileInfo`-Objekten, und das Admin-Panel verarbeitet jede Datei unabhängig durch Validierung und Speicherung.


!!! warning
    Beim Speichern des Formulars wird die gesamte Dateiliste durch die übermittelten Dateien ersetzt. Es gibt keine Möglichkeit, eine einzelne Datei hinzuzufügen oder zu entfernen. Für ein Lifecycle-Management pro Datei verwenden Sie ein Inline-Modell mit seinem eigenen `FileField`.

!!! important
    `ListField(FileField(...))` wird nicht unterstützt. Verwenden Sie `multiple=True` für einfache Sammlungen und Inline-Modelle für strukturierte Dateidaten.

## Validierung

Die Validierung läuft in dieser Reihenfolge ab:

1. `accept`
2. `max_size`
3. benutzerdefinierte `validators`

Ein benutzerdefinierter Validator ist ein Callable, das den Request, das Feld, eine `UploadFile` und die vollständig übermittelten Formularwerte erhält. Er muss `None` zurückgeben oder einen `ValueError` auslösen.

Das folgende Beispiel validiert die tatsächlichen Dateiinhalte mit der Bibliothek `filetype`:

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

!!! important "Den Dateizeiger zurücksetzen"
    Setzen Sie den Dateizeiger mit `seek(0)` immer vor und nach der Inspektion zurück, damit die Storage-Schicht die vollständige Datei lesen kann.

!!! note
    Validatoren laufen pro Datei, daher wird bei `multiple=True` jede Datei unabhängig validiert. `ImageField` wendet seine eigene Bildvalidierung vor jedem benutzerdefinierten Validator an.


!!! tip "Bewährte Methoden"
    Verwenden Sie `accept` und `max_size` für eine leichte Validierung.

    Verwenden Sie benutzerdefinierte Validatoren, wenn Sie Dateiinhalte prüfen oder anwendungsspezifische Regeln durchsetzen müssen.

    Verlassen Sie sich bei sicherheitskritischer Validierung nicht auf Dateierweiterungen oder `Content-Type`-Header. Prüfen Sie stattdessen den Inhalt, z. B. mit einer Bibliothek wie `filetype` oder `python-magic`.


## Einschränkungen bei der Dateibereinigung

`starlette-admin` lädt Dateien in das Storage-Backend hoch und schreibt `FileInfo`-Metadaten in die Datenbank, aber es bereinigt keine Dateien nach einem Fehler oder einer Löschung. Daraus ergeben sich zwei Verhaltensweisen:

* **Fehlgeschlagene Transaktionen:** Wenn eine Datenbanktransaktion nach Abschluss eines Uploads zurückgerollt wird, bleibt die Datei im Storage-Backend. Storage-Schreibvorgänge haben keinen Rollback-Mechanismus.
* **Löschungen und Aktualisierungen:** Das Löschen einer Zeile oder das Ersetzen einer Datei entfernt die `FileInfo`-Referenz aus der Datenbank, aber die alte Datei bleibt in `LocalStorage` oder `S3Storage`.

Dieses Design hält die Storage-Schicht einfach und verhindert, dass Fehler auf Anwendungsebene destruktive Operationen auslösen. Der Nachteil ist, dass sich verwaiste Dateien ansammeln. Damit der Speicher nicht unbegrenzt wächst, gleichen Sie sie selbst ab. Ein gängiges Muster ist ein periodisch laufender Hintergrundjob, der die Keys in Ihrem Storage-Backend mit den aktiven `FileInfo`-Referenzen in Ihrer Datenbank abgleicht.

### Transaktionale Alternative

Wenn Ihre Anwendung benötigt, dass Dateispeicheroperationen transaktional mit Datenbankschreibvorgängen erfolgen, verwenden Sie eine Bibliothek, die den Dateispeicher an die SQLAlchemy Unit of Work koppelt.

Verwenden Sie statt des Parameters `storage=` des Felds [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Es speichert Dateien als Teil des ORM-Flush- und Rollback-Zyklus, sodass eine fehlgeschlagene Transaktion oder das Löschen einer Zeile den entsprechenden Dateischreibvorgang rückgängig macht. Ein funktionierendes Beispiel finden Sie unter [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Nächste Schritte

* **[Felder](fields.md):** Referenz zu `FileField` und `ImageField`.
* **[Export & Import](export-import.md):** Wie Dateien in Exportpaketen enthalten sind.
* **[Sicherheit](security.md):** Automatisches Bereinigungs- und Validierungsverhalten.
