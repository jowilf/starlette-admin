---
title: Referencia de la API de Contrib para SQLModel
description: Documentación de referencia de la API para la integración del backend
  SQLModel en starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traducción automática supervisada"

    Este contenido se traduce mediante generación automática guiada por
    glosarios y guías de estilo revisados por personas. Dado que el texto no
    se revisa manualmente línea por línea, pueden producirse errores
    ocasionales o expresiones poco naturales.

    En caso de cualquier discrepancia, la versión en inglés constituye la
    autoridad y la fuente de referencia.

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/sqlmodel/)
<!-- translation-notice:end -->

# Contrib: SQLModel

Referencia completa de atributos y métodos para el backend de SQLModel (`starlette_admin.contrib.sqlmodel`),
generada a partir de los docstrings. SQLModel se basa en SQLAlchemy por debajo, por lo que `Admin` y `ModelView` son
subclases ligeras del [backend de SQLAlchemy](sqlalchemy.md) que validan los datos de los formularios a través de la
capa Pydantic del modelo. Para una guía orientada a tareas, consulte
[Integración con SQLModel](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
