---
title: Installation
description: Découvrez comment installer starlette-admin et ses dépendances optionnelles
  pour créer une interface d'administration pour votre application FastAPI ou Starlette.
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# Installation

Installez **starlette-admin** à l'aide du gestionnaire de paquets de votre choix.

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin nécessite **Python 3.11 ou une version ultérieure**.

Le paquet principal est indépendant du backend. Pour créer une interface d'administration pour votre application, installez l'intégration appropriée à votre couche de données (telle que SQLAlchemy, Beanie, MongoEngine ou Tortoise ORM) en complément du paquet de base.

## Dépendances incluses

L'installation de base inclut tout ce qui est nécessaire au fonctionnement de l'interface d'administration. Aucune dépendance optionnelle n'est installée par défaut.

| Dépendance | Rôle |
| --- | --- |
| [Starlette](https://www.starlette.io/) | Héberge l'application d'administration. |
| [Jinja2](https://jinja.palletsprojects.com/) | Fournit le moteur de templates pour les pages de liste, de détail et les formulaires. |
| [python-multipart](https://github.com/Kludex/python-multipart) | Analyse les soumissions de formulaires et les téléversements de fichiers. |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | Signe les cookies pour les jetons CSRF et les messages flash. |

Les applications construites avec FastAPI ne nécessitent aucune intégration supplémentaire, car FastAPI repose sur Starlette. Montez simplement l'interface d'administration dans votre application FastAPI existante.

## Dépendances optionnelles

starlette-admin fournit les dépendances optionnelles suivantes :

- `pdf` : ajoute la prise en charge de l'export PDF ([reportlab](https://www.reportlab.com/)).
- `i18n` : ajoute la prise en charge de l'internationalisation ([Babel](https://babel.pocoo.org/)).
- `tinymce` : ajoute la prise en charge des éditeurs de texte enrichi. Installe [nh3](https://nh3.readthedocs.io/), qui assainit le HTML soumis par `TinyMCEEditorField`.
- `s3` : ajoute la prise en charge du stockage objet compatible S3. Installe [aiobotocore](https://aiobotocore.readthedocs.io/) pour les téléversements asynchrones vers AWS S3 et les services de stockage objet compatibles, tels que MinIO.

Installez une ou plusieurs dépendances optionnelles en même temps que starlette-admin :

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

## Installation depuis les sources

Pour utiliser les dernières modifications non encore publiées, installez le paquet directement depuis le dépôt GitHub.

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## Prochaines étapes

- **[Quickstart](quickstart.md)** : créez votre première interface d'administration avec des données réelles.
- **[Concepts](concepts.md)** : découvrez l'architecture fondamentale et les principes de conception derrière starlette-admin.
