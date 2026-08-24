---
title: Referencia de la API de contrib de Tortoise ORM
description: Documentación de referencia de la API para la integración del backend
  de Tortoise ORM en starlette-admin.
source_hash: 64e4327c8b219a5ce961ab0f5a300132bb286dd74a34ad5ec50a110445af46bd
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/tortoise/)
<!-- translation-notice:end -->

# Contrib: Tortoise ORM

Referencia completa de atributos y métodos para el backend de Tortoise ORM
(`starlette_admin.contrib.tortoise`), generada a partir de las cadenas de
documentación (docstrings). Para una guía orientada a tareas, consulte
[Tortoise ORM](../../integrations/tortoise.md).

::: starlette_admin.contrib.tortoise.admin.Admin

::: starlette_admin.contrib.tortoise.view.ModelView

::: starlette_admin.contrib.tortoise.view.InlineModelView

## Campos

::: starlette_admin.contrib.tortoise.fields.BackwardHasOne

## Convertidores

::: starlette_admin.contrib.tortoise.converters.BaseTortoiseModelConverter

::: starlette_admin.contrib.tortoise.converters.ModelConverter

!!! note
    Las clases de filtro concretas (`ContainsFilter`, `EnumInFilter`, `RelationIsNullFilter`, etc.)
    no se enumeran aquí. Son un reflejo de los filtros independientes del backend documentados en
    [Filtros](../filters.md); el comportamiento específico de Tortoise (búsquedas sin distinción
    entre mayúsculas y minúsculas, coerción de enumeraciones y comprobaciones de nulos en columnas
    de clave sin procesar) se cubre en
    [Tortoise ORM](../../integrations/tortoise.md#registro-de-filtros).
