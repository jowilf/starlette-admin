---
title: Installation
description: Erfahren Sie, wie Sie starlette-admin und seine optionalen Abhängigkeiten
  installieren, um ein Admin-Interface für Ihre FastAPI- oder Starlette-Anwendung
  zu erstellen.
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# Installation

Installieren Sie **starlette-admin** mit Ihrem bevorzugten Paketmanager.

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin erfordert **Python 3.11 oder höher**.

Das Kernpaket ist backend-agnostisch. Um ein Admin-Interface für Ihre Anwendung zu erstellen, installieren Sie die passende Integration für Ihre Datenschicht (z. B. SQLAlchemy, Beanie, MongoEngine oder Tortoise ORM) zusammen mit dem Basispaket.

## Enthaltene Abhängigkeiten

Die Basisinstallation enthält alles, was zum Ausführen des Admin-Interfaces erforderlich ist. Optionale Abhängigkeiten werden standardmäßig nicht installiert.

| Abhängigkeit | Zweck |
| --- | --- |
| [Starlette](https://www.starlette.io/) | Hostet die Admin-Anwendung. |
| [Jinja2](https://jinja.palletsprojects.com/) | Stellt die Template-Engine für Listen-, Detail- und Formularseiten bereit. |
| [python-multipart](https://github.com/Kludex/python-multipart) | Parst Formularübermittlungen und Uploads. |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | Signiert Cookies für CSRF-Tokens und Flash-Nachrichten. |

Anwendungen, die mit FastAPI erstellt wurden, benötigen keine zusätzliche Integration, da FastAPI auf Starlette aufbaut. Mounten Sie das Admin-Interface in Ihre bestehende FastAPI-Anwendung.

## Optionale Abhängigkeiten

starlette-admin bietet die folgenden optionalen Abhängigkeiten:

- `pdf`: Fügt Unterstützung für den PDF-Export hinzu ([reportlab](https://www.reportlab.com/)).
- `i18n`: Fügt Unterstützung für Internationalisierung hinzu ([Babel](https://babel.pocoo.org/)).
- `tinymce`: Fügt Unterstützung für Rich-Text-Editoren hinzu. Installiert [nh3](https://nh3.readthedocs.io/), das von `TinyMCEEditorField` übermitteltes HTML bereinigt.
- `s3`: Fügt Unterstützung für S3-kompatiblen Objektspeicher hinzu. Installiert [aiobotocore](https://aiobotocore.readthedocs.io/) für asynchrone Uploads zu AWS S3 und kompatiblen Objektspeicherdiensten, z. B. MinIO.

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

## Aus dem Quellcode installieren

Um die neuesten unveröffentlichten Änderungen zu verwenden, installieren Sie das Paket direkt aus dem GitHub-Repository.

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

- **[Quickstart](quickstart.md)**: Erstellen Sie Ihr erstes Admin-Interface mit echten Daten.
- **[Konzepte](concepts.md)**: Lernen Sie die Kernarchitektur und die Designprinzipien hinter starlette-admin kennen.
