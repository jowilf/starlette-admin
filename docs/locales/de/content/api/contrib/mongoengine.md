---
title: MongoEngine Contrib API-Referenz
description: API-Referenzdokumentation für die MongoEngine-Backend-Integration in
  starlette-admin.
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
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

    [Lesen Sie die ursprüngliche englische Version](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib: MongoEngine

Vollständige Referenz aller Attribute und Methoden des MongoEngine-Backends
(`starlette_admin.contrib.mongoengine`), generiert aus Docstrings. Eine aufgabenorientierte
Einführung finden Sie unter [MongoEngine](../../integrations/mongoengine.md).

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
    Konkrete Filterklassen (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter` usw.) werden
    hier nicht aufgeführt. Sie entsprechen den backend-unabhängigen Filtern, die unter
    [Filters](../filters.md) dokumentiert sind; das MongoEngine-spezifische Verhalten wird in
    [MongoEngine](../../integrations/mongoengine.md#filter-registry) behandelt.
