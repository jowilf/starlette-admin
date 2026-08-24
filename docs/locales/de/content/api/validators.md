---
title: Validators-API-Referenz
description: API-Referenzdokumentation für Formularfeld-Validatoren in starlette-admin.
source_hash: 42e3fab8cab328d3c9f6ee206f8e80a246ccb8d84625a9da35ee0afd4f8bd644
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/validators/)
<!-- translation-notice:end -->

# Validators

Integrierte Feldvalidatoren, die über `BaseField(validators=[...])` an jedes Feld angehängt und von `BaseField.validate` ausgeführt werden. Einen Überblick über den Validierungsablauf finden Sie unter [Fields](../user-guide/fields.md).

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

## Datei-Validatoren

::: starlette_admin.validators.file_size

::: starlette_admin.validators.file_type

::: starlette_admin.validators.valid_image

::: starlette_admin.validators.image_size
