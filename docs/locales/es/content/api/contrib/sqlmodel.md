---
title: Referencia de la API de Contrib para SQLModel
description: Documentación de referencia de la API para la integración del backend
  SQLModel en starlette-admin.
source_hash: ee62d48b6085bc125ca853e8cb77e9de5b6818a9babd9bef12bfcae9dd82e8e5
prompt_hash: 4d252dd7142cde87a0a6edf7cc724709cd7913d618d80eb0687c4c9beddf15fb
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

<!-- translation-notice:start -->
??? warning "Traducción automática supervisada"

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
generada a partir de docstrings. SQLModel se basa en SQLAlchemy, por lo que `Admin` y `ModelView` son
subclases ligeras del [backend de SQLAlchemy](sqlalchemy.md) que validan los datos de los formularios a través de
la capa de Pydantic del modelo. Para un recorrido orientado a tareas, consulte
[Integración de SQLModel](../../integrations/sqlmodel.md).

::: starlette_admin.contrib.sqlmodel.admin.Admin

::: starlette_admin.contrib.sqlmodel.view.ModelView

::: starlette_admin.contrib.sqlmodel.view.InlineModelView
