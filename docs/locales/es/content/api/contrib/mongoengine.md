---
title: Referencia de la API de Contrib para MongoEngine
description: Documentación de referencia de la API para la integración del backend
  MongoEngine en starlette-admin.
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib: MongoEngine

Referencia completa de atributos y métodos para el backend de MongoEngine
(`starlette_admin.contrib.mongoengine`), generada a partir de las docstrings. Para una guía
orientada a tareas, consulte [MongoEngine](../../integrations/mongoengine.md).

::: starlette_admin.contrib.mongoengine.admin.Admin

::: starlette_admin.contrib.mongoengine.view.ModelView

::: starlette_admin.contrib.mongoengine.view.InlineModelView

## Fields

::: starlette_admin.contrib.mongoengine.fields.ObjectIdField

::: starlette_admin.contrib.mongoengine.fields.FileField

::: starlette_admin.contrib.mongoengine.fields.ImageField

## Converters

::: starlette_admin.contrib.mongoengine.converters.BaseMongoEngineModelConverter

::: starlette_admin.contrib.mongoengine.converters.ModelConverter

## Exceptions

::: starlette_admin.contrib.mongoengine.exceptions.NotSupportedField

!!! note
    Las clases de filtros concretas (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, etc.) no se
    enumeran aquí. Reflejan los filtros independientes del backend documentados en
    [Filters](../filters.md); el comportamiento específico de MongoEngine se describe en
    [MongoEngine](../../integrations/mongoengine.md#filter-registry).
