---
title: Installation
description: Erfahren Sie, wie Sie starlette-admin und seine optionalen Abhängigkeiten
  installieren, um eine Admin-Oberfläche für Ihre FastAPI- oder Starlette-Anwendung
  zu erstellen.
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# Installation

Installieren Sie **starlette-admin** mit dem Paketmanager Ihrer Wahl.

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin erfordert **Python 3.11 oder neuer**.

Das Kernpaket ist backend-agnostisch. Um eine Admin-Oberfläche für Ihre Anwendung zu erstellen, installieren Sie die passende Integration für Ihre Datenschicht (wie SQLAlchemy, Beanie, MongoEngine oder Tortoise ORM) zusammen mit dem Basispaket.

## Enthaltene Abhängigkeiten

Die Basisinstallation umfasst alles, was für den Betrieb der Admin-Oberfläche erforderlich ist. Standardmäßig werden keine optionalen Abhängigkeiten installiert.

| Abhängigkeit | Zweck |
| --- | --- |
| [Starlette](https://www.starlette.io/) | Hostet die Admin-Anwendung. |
| [Jinja2](https://jinja.palletsprojects.com/) | Stellt die Template-Engine für Listen-, Detail- und Formularseiten bereit. |
| [python-multipart](https://github.com/Kludex/python-multipart) | Verarbeitet Formularübermittlungen und Datei-Uploads. |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | Signiert Cookies für CSRF-Tokens und Flash-Nachrichten. |

Anwendungen, die mit FastAPI erstellt wurden, benötigen keine zusätzliche Integration, da FastAPI auf Starlette aufbaut. Binden Sie die Admin-Oberfläche einfach in Ihre bestehende FastAPI-Anwendung ein.

## Optionale Abhängigkeiten

starlette-admin stellt die folgenden optionalen Abhängigkeiten bereit:

- `pdf`: Fügt Unterstützung für den PDF-Export hinzu ([reportlab](https://www.reportlab.com/)).
- `i18n`: Fügt Unterstützung für Internationalisierung hinzu ([Babel](https://babel.pocoo.org/)).
- `tinymce`: Fügt Unterstützung für Rich-Text-Editoren hinzu. Installiert [nh3](https://nh3.readthedocs.io/), das von `TinyMCEEditorField` übermitteltes HTML bereinigt.
- `s3`: Fügt Unterstützung für S3-kompatiblen Objektspeicher hinzu. Installiert [aiobotocore](https://aiobotocore.readthedocs.io/) für asynchrone Uploads zu AWS S3 und kompatiblen Objektspeicherdiensten wie MinIO.

Installieren Sie eine oder mehrere optionale Abhängigkeiten zusammen mit starlette-admin:

=== "pip"

    ```bash
    # Install the `pdf` extra.
    pip install "starlette-admin[pdf]"

    # Install multiple extras.
    pip install "starlette-admin[i18n,pdf,s3]"
    ```

=== "uv"

    ```bash
    # Install the `pdf` extra.
    uv add "starlette-admin[pdf]"

    # Install multiple extras.
    uv add "starlette-admin[i18n,pdf,s3]"
    ```

## Installation aus dem Quellcode

Um die neuesten noch unveröffentlichten Änderungen zu verwenden, installieren Sie das Paket direkt aus dem GitHub-Repository.

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## Nächste Schritte

- **[Quickstart](quickstart.md)**: Erstellen Sie Ihre erste Admin-Oberfläche mit echten Daten.
- **[Konzepte](concepts.md)**: Lernen Sie die zugrundeliegende Architektur und die Entwurfsprinzipien von starlette-admin kennen.
