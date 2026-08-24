---
title: Referencia de la API de Contrib para MongoEngine
description: Documentación de referencia de la API para la integración del backend
  MongoEngine en starlette-admin.
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib: MongoEngine

Referencia completa de atributos y métodos para el backend de MongoEngine
(`starlette_admin.contrib.mongoengine`), generada a partir de las docstrings. Para una guía orientada a tareas,
consulte [MongoEngine](../../integrations/mongoengine.md).

::: starlette_admin.contrib.mongoengine.admin.Admin

::: starlette_admin.contrib.mongoengine.view.ModelView

::: starlette_admin.contrib.mongoengine.view.InlineModelView

## Campos

::: starlette_admin.contrib.mongoengine.fields.ObjectIdField

::: starlette_admin.contrib.mongoengine.fields.FileField

::: starlette_admin.contrib.mongoengine.fields.ImageField

## Convertidores

::: starlette_admin.contrib.mongoengine.converters.BaseMongoEngineModelConverter

::: starlette_admin.contrib.mongoengine.converters.ModelConverter

## Excepciones

::: starlette_admin.contrib.mongoengine.exceptions.NotSupportedField

!!! note
    Las clases de filtro concretas (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, etc.) no se
    enumeran aquí. Reflejan los filtros independientes del backend documentados en
    [Filtros](../filters.md); el comportamiento específico de MongoEngine se describe en
    [MongoEngine](../../integrations/mongoengine.md#registro-de-filtros).
