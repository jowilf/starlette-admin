---
title: Dateispeicher
description: Verwalten Sie Datei- und Bild-Uploads in starlette-admin mit LocalStorage
  oder S3-kompatiblem Backend-Speicher.
source_hash: 6f3d18d6107bfa818c48507b0807fb14bf6fcbe8825d9e5c824ed02e0ff2dd5c
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/user-guide/file-storage/)
<!-- translation-notice:end -->

# Dateispeicher

`FileField` und `ImageField` speichern hochgeladene Dateien über ein Storage-Backend, das Sie mit dem Parameter `storage` des Felds festlegen.

Erstellen Sie ein Storage-Backend einmalig und verwenden Sie es für alle Felder wieder, die Dateien am selben Ort ablegen.


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

Wenn ein Benutzer über das Admin-Interface ein Cover hochlädt, führt das Admin-Interface Folgendes aus:

* es speichert die Datei unter `uploads/covers/`
* es legt ein JSON-Metadatenobjekt in der Spalte `cover` ab

Die Datenbank enthält niemals die Datei selbst, einen Dateisystempfad oder Binärdaten.


## Was in der Datenbank gespeichert wird

Das Admin-Interface repräsentiert einen Datei-Upload als serialisiertes [`FileInfo`](../api/storage.md#starlette_admin.storage.base.FileInfo)-Objekt im Modellfeld.

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

* `filename`: bereinigter ursprünglicher Dateiname, wird für die Anzeige verwendet
* `content_type`: beim Upload erkannter MIME-Typ
* `size`: Dateigröße in Bytes
* `storage`: registrierter Backend-Name, wird verwendet, um den Speicherort der Datei für die URL-Generierung und das Löschen aufzulösen
* `key`: relativer Pfad oder Objektschlüssel innerhalb des Storages
* `url`: zwischengespeicherte öffentliche URL

`LocalStorage` speichert einen leeren `url`-Wert, da URLs vom aktiven Request abhängen. `S3Storage` speichert eine öffentliche oder vorsignierte URL, je nach Ihrer Konfiguration.

Unabhängig vom Backend generiert `FileField` die URL zur Renderzeit mit `storage.url()` neu, statt dem gespeicherten Wert zu vertrauen.

`ImageField` ergänzt zusätzlich `width` und `height`.

Das Admin-Interface bereinigt jeden Dateinamen mit `secure_filename`, bevor er gespeichert wird: Es entfernt Pfadkomponenten und ersetzt Zeichen außerhalb von `[A-Za-z0-9_.-]` durch `_`. Weitere Informationen finden Sie unter [Security](security.md).


## Storage-Backends

### Lokaler Speicher

```python
from starlette_admin.storage import LocalStorage

local = LocalStorage(base_dir="uploads", name="local")
```

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `base_dir` | `str | Path` | erforderlich | Stammverzeichnis für gespeicherte Dateien. Wird bei Bedarf automatisch erstellt. |
| `name` | `str | None` | `"local"` | Registrierungsname, der das Backend identifiziert. Muss eindeutig sein, wenn Sie mehrere Instanzen verwenden. |

Das Admin-Interface stellt Dateien über diese Route bereit:

```
/_files/{storage}/{path}
```

Sie benötigen keine zusätzliche Konfiguration für statische Dateien.

`LocalStorage.url()` baut URLs aus dem aktuellen Request-Kontext auf, daher bleibt das gespeicherte `url`-Feld leer und wird bei Bedarf neu berechnet.

!!! note
    Ein Codebeispiel finden Sie unter [examples/04-filestorage](https://github.com/jowilf/starlette-admin/tree/main/examples/04-filestorage).

### Amazon S3 Storage

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

Dadurch wird `aiobotocore` installiert.

| Parameter | Typ | Standardwert | Beschreibung |
| --- | --- | --- | --- |
| `bucket` | `str` | erforderlich | Name des S3-Buckets. |
| `prefix` | `str` | `"uploads/"` | Schlüsselpräfix, das auf jedes gespeicherte Objekt angewendet wird. |
| `region` | `str` | `"us-east-1"` | AWS-Region, die für Signierung und URL-Generierung verwendet wird. |
| `access_key` und `secret_key` | `str | None` | `None` | Optionale Zugangsdaten. Fällt auf die Standard-AWS-Credential-Chain zurück. |
| `public` | `bool` | `True` | Bei `True` wird eine öffentliche URL zurückgegeben. Bei `False` werden vorsignierte URLs generiert. |
| `expires` | `int` | `3600` | Ablaufzeit für vorsignierte URLs, in Sekunden. |
| `endpoint_url` | `str | None` | `None` | Benutzerdefinierter S3-kompatibler Endpoint, z. B. MinIO, R2 oder B2. |
| `name` | `str | None` | `"s3"` | Registrierungsname, der das Backend identifiziert. |

Wenn Sie `endpoint_url` angeben, baut das Admin-Interface URLs wie folgt auf:

```
{endpoint_url}/{bucket}/{key}
```

statt das virtuelle Hosting-Format von AWS zu verwenden.


!!! important
    Dateifelder müssen auf eine datenbankseitige Spalte mit JSON-Unterstützung abgebildet werden. Die Datenbank enthält ausschließlich die Metadaten. Das Storage-Backend enthält die Datei selbst.


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

Die Datenbank speichert eine JSON-Liste von `FileInfo`-Objekten, und das Admin-Interface verarbeitet jede Datei unabhängig durch Validierung und Speicherung.


!!! warning
    Beim Speichern des Formulars wird die gesamte Dateiliste durch die übermittelten Dateien ersetzt. Es ist nicht möglich, eine einzelne Datei hinzuzufügen oder zu entfernen. Für ein per-Datei-Lifecycle-Management verwenden Sie ein Inline-Modell mit eigenem `FileField`.

!!! important
    `ListField(FileField(...))` wird nicht unterstützt. Verwenden Sie `multiple=True` für einfache Sammlungen und Inline-Modelle für strukturierte Dateidaten.

## Validierung

Die Validierung läuft in dieser Reihenfolge ab:

1. `accept`
2. `max_size`
3. benutzerdefinierte `validators`

Ein benutzerdefinierter Validator ist eine aufrufbare Funktion, die den Request, das Feld, ein `UploadFile` sowie die vollständig übermittelten Formularwerte erhält. Er muss `None` zurückgeben oder einen `ValueError` auslösen.

Das folgende Beispiel validiert den tatsächlichen Dateiinhalt mit der Bibliothek `filetype`:

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

!!! important "Dateizeiger zurücksetzen"
    Setzen Sie den Dateizeiger mit `seek(0)` immer vor und nach der Prüfung zurück, damit die Storage-Schicht die vollständige Datei lesen kann.

!!! note
    Validatoren werden pro Datei ausgeführt, sodass bei `multiple=True` jede Datei unabhängig validiert wird. `ImageField` wendet seine eigene Bildvalidierung an, bevor ein benutzerdefinierter Validator zum Einsatz kommt.


!!! tip "Best Practices"
    Verwenden Sie `accept` und `max_size` für eine leichte Validierung.

    Verwenden Sie benutzerdefinierte Validatoren, wenn Sie Dateiinhalte prüfen oder anwendungsspezifische Regeln durchsetzen möchten.

    Verlassen Sie sich bei sicherheitskritischen Validierungen nicht auf Dateierweiterungen oder `Content-Type`-Header. Prüfen Sie stattdessen den Inhalt, beispielsweise mit einer Bibliothek wie `filetype` oder `python-magic`.


## Einschränkungen bei der Dateibereinigung

`starlette-admin` lädt Dateien in das Storage-Backend hoch und schreibt `FileInfo`-Metadaten in die Datenbank, führt jedoch keine Bereinigung von Dateien nach einem Fehler oder einer Löschung durch. Daraus ergeben sich zwei Verhaltensweisen:

* **Fehlgeschlagene Transaktionen:** Wenn eine Datenbanktransaktion nach Abschluss eines Uploads zurückgerollt wird, bleibt die Datei im Storage-Backend bestehen. Schreibvorgänge im Storage verfügen über keinen Rollback-Mechanismus.
* **Löschungen und Aktualisierungen:** Beim Löschen einer Zeile oder Ersetzen einer Datei wird die `FileInfo`-Referenz aus der Datenbank entfernt, die alte Datei bleibt jedoch in `LocalStorage` oder `S3Storage` bestehen.

Dieses Design hält die Storage-Schicht einfach und verhindert, dass Fehler auf Anwendungsebene destruktive Operationen auslösen. Der Nachteil ist, dass sich verwaiste Dateien ansammeln. Damit der Speicher nicht unbegrenzt wächst, gleichen Sie diese selbst ab. Ein verbreitetes Muster ist ein periodisch laufender Background-Job, der die Schlüssel in Ihrem Storage-Backend mit den aktiven `FileInfo`-Referenzen in Ihrer Datenbank abgleicht.

### Transaktionelle Alternative

Wenn Ihre Anwendung erfordert, dass Datei-Storage-Operationen transaktional mit den Datenbankschreibvorgängen erfolgen, verwenden Sie eine Bibliothek, die den Dateispeicher mit der SQLAlchemy Unit of Work verknüpft.

Verwenden Sie anstelle des Parameters `storage=` des Felds [sqlalchemy-file](https://github.com/jowilf/sqlalchemy-file). Es speichert Dateien als Teil des ORM-Flush- und Rollback-Zyklus, sodass eine fehlgeschlagene Transaktion oder das Löschen einer Zeile den entsprechenden Schreibvorgang der Datei rückgängig macht. Ein funktionierendes Beispiel finden Sie unter [examples/13-sqlachemy-file](https://github.com/jowilf/starlette-admin/tree/main/examples/13-sqlachemy-file).

---

## Was kommt als Nächstes?

* **[Fields](fields.md):** Referenz zu `FileField` und `ImageField`.
* **[Export & Import](export-import.md):** Wie Dateien in Export-Bundles berücksichtigt werden.
* **[Security](security.md):** Automatisches Bereinigen und Validierungsverhalten.
