---
title: Referencia de la API de Contrib para SQLAlchemy
description: Documentación de referencia de la API para la integración del backend
  de SQLAlchemy en starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy

Referencia completa de atributos y métodos del backend de SQLAlchemy (`starlette_admin.contrib.sqla`),
generada a partir de las cadenas de documentación. Para una guía orientada a tareas, consulte
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Validación con Pydantic

La extensión `ext.pydantic` valida los datos del formulario contra un modelo de Pydantic antes de
escribir el registro. Consulte [Validación con Pydantic](../../integrations/sqlalchemy.md#validacion-con-pydantic)
para obtener el procedimiento completo.

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Campos

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Convertidores

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Excepciones

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Las clases de filtro concretas (`EqualFilter`, `ContainsFilter`, `BetweenFilter`, etc.) no se
    enumeran aquí. Reflejan una a una los filtros independientes del backend documentados en
    [Filtros](../filters.md); el comportamiento específico de SQLAlchemy que conviene conocer se
    trata en [SQLAlchemy](../../integrations/sqlalchemy.md#registro-de-filtros).
