---
title: SQLAlchemy Contrib API-Referenz
description: API-Referenzdokumentation für die SQLAlchemy-Backend-Integration in starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Überwachte maschinelle Übersetzung"

    Dieser Inhalt wurde maschinell übersetzt und basiert auf von Menschen
    kuratierten Glossaren und Styleguides. Da der Text nicht zeilenweise
    manuell überprüft wird, können gelegentlich Fehler oder unklare
    Formulierungen auftreten.

    Bei etwaigen Abweichungen ist die ursprüngliche englische Version die
    maßgebliche Quelle.

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib: SQLAlchemy

Vollständige Referenz aller Attribute und Methoden des SQLAlchemy-Backends (`starlette_admin.contrib.sqla`),
generiert aus den Docstrings. Eine aufgabenorientierte Einführung finden Sie unter
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Pydantic-Validierung

Die `ext.pydantic`-Erweiterung validiert Formulardaten gegen ein Pydantic-Modell, bevor der
Datensatz geschrieben wird. Die vollständige Anleitung finden Sie unter
[Pydantic-Validierung](../../integrations/sqlalchemy.md#pydantic-validation).

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Fields

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Converter

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Exceptions

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Konkrete Filterklassen (`EqualFilter`, `ContainsFilter`, `BetweenFilter` usw.) werden hier
    nicht aufgeführt. Sie entsprechen eins zu eins den backend-unabhängigen Filtern, die in
    [Filters](../filters.md) dokumentiert sind; das SQLAlchemy-spezifische Verhalten, das es zu
    kennen lohnt, wird unter [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry) behandelt.
