---
title: Instalación
description: Aprenda a instalar starlette-admin y sus dependencias opcionales para
  crear una interfaz de administración para su aplicación FastAPI o Starlette.
source_hash: f19997ae1ec3c0e2b85ec0ebebd1c49e85a2dcd43be9ed4d945de9f336b4caf1
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/getting-started/installation/)
<!-- translation-notice:end -->

# Instalación

Instale **starlette-admin** con el gestor de paquetes de su preferencia.

=== "pip"

    ```bash
    pip install starlette-admin
    ```

=== "uv"

    ```bash
    uv add starlette-admin
    ```

starlette-admin requiere **Python 3.11 o posterior**.

El paquete principal es independiente del backend. Para crear una interfaz de administración para su aplicación, instale la integración adecuada para su capa de datos (como SQLAlchemy, Beanie, MongoEngine o Tortoise ORM) junto con el paquete base.

## Dependencias incluidas

La instalación base incluye todo lo necesario para ejecutar la interfaz de administración. No se instala ninguna dependencia opcional de forma predeterminada.

| Dependencia | Propósito |
| --- | --- |
| [Starlette](https://www.starlette.io/) | Aloja la aplicación de administración. |
| [Jinja2](https://jinja.palletsprojects.com/) | Proporciona el motor de plantillas para las páginas de lista, detalle y formulario. |
| [python-multipart](https://github.com/Kludex/python-multipart) | Analiza los envíos de formularios y las cargas de archivos. |
| [itsdangerous](https://itsdangerous.palletsprojects.com/) | Firma cookies para tokens CSRF y mensajes flash. |

Las aplicaciones creadas con FastAPI no requieren ninguna integración adicional, ya que FastAPI está construido sobre Starlette. Monte la interfaz de administración en su aplicación FastAPI existente.

## Dependencias opcionales

starlette-admin proporciona las siguientes dependencias opcionales:

- `pdf`: Añade soporte de exportación a PDF ([reportlab](https://www.reportlab.com/)).
- `i18n`: Añade soporte de internacionalización ([Babel](https://babel.pocoo.org/)).
- `tinymce`: Añade soporte de editor de texto enriquecido. Instala [nh3](https://nh3.readthedocs.io/), que depura el HTML enviado por `TinyMCEEditorField`.
- `s3`: Añade soporte de almacenamiento de objetos compatible con S3. Instala [aiobotocore](https://aiobotocore.readthedocs.io/) para cargas asíncronas a AWS S3 y servicios de almacenamiento de objetos compatibles, como MinIO.

Instale una o más dependencias opcionales junto con starlette-admin:

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

## Instalar desde el código fuente

Para usar los cambios más recientes que aún no se han publicado, instale el paquete directamente desde el repositorio de GitHub.

=== "pip"

    ```bash
    pip install "git+https://github.com/jowilf/starlette-admin.git"
    ```

=== "uv"

    ```bash
    uv add "git+https://github.com/jowilf/starlette-admin.git"
    ```

---

## Próximos pasos

- **[Inicio rápido](quickstart.md)**: Cree su primera interfaz de administración con datos reales.
- **[Conceptos](concepts.md)**: Conozca la arquitectura central y los principios de diseño detrás de starlette-admin.
