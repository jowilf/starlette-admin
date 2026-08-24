---
title: Referencia de la API de validadores
description: Documentación de referencia de la API para los validadores de campos
  de formulario en starlette-admin.
source_hash: 42e3fab8cab328d3c9f6ee206f8e80a246ccb8d84625a9da35ee0afd4f8bd644
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

    [Leer la versión original en inglés](https://jowilf.github.io/starlette-admin/api/validators/)
<!-- translation-notice:end -->

# Validadores

Validadores de campos integrados, que se adjuntan a cualquier campo mediante `BaseField(validators=[...])`
y se ejecutan a través de `BaseField.validate`. Para obtener una descripción general del flujo de
validación, consulte [Campos](../user-guide/fields.md).

::: starlette_admin.validators.length

::: starlette_admin.validators.number_range

::: starlette_admin.validators.number_gt

::: starlette_admin.validators.number_lt

::: starlette_admin.validators.date_range

::: starlette_admin.validators.regexp

::: starlette_admin.validators.disallow

::: starlette_admin.validators.mac_address

::: starlette_admin.validators.slug

::: starlette_admin.validators.color

::: starlette_admin.validators.email

::: starlette_admin.validators.url

::: starlette_admin.validators.uuid

::: starlette_admin.validators.ip_address

::: starlette_admin.validators.any_of

::: starlette_admin.validators.none_of

::: starlette_admin.validators.items

## Validadores de archivos

::: starlette_admin.validators.file_size

::: starlette_admin.validators.file_type

::: starlette_admin.validators.valid_image

::: starlette_admin.validators.image_size
