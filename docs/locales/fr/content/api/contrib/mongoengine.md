---
title: Référence de l'API MongoEngine Contrib
description: Documentation de référence de l'API pour l'intégration du backend MongoEngine
  dans starlette-admin.
source_hash: 453c422f60aa5c89d4a1eb9a4310165bb2773263a8b6d21a791a3141f009bb8e
prompt_hash: 8069042d0b0fb6ced5d0faa52da31ad04aa7f9a9dffdc142711ed8fbdffe7e42
machine_translated: true
---

<!-- translation-notice:start -->
??? info "Traduction automatique supervisée"

    Ce contenu est traduit à l'aide d'une génération automatique guidée par
    des glossaires et des guides de style élaborés par des humains. Le texte
    n'étant pas relu manuellement ligne par ligne, des erreurs ou des
    tournures maladroites peuvent occasionnellement apparaître.

    En cas de divergence, la version anglaise constitue la source de
    référence.

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/contrib/mongoengine/)
<!-- translation-notice:end -->

# Contrib : MongoEngine

Référence complète des attributs et méthodes pour le backend MongoEngine
(`starlette_admin.contrib.mongoengine`), générée à partir des docstrings. Pour un guide
orienté tâches, consultez [MongoEngine](../../integrations/mongoengine.md).

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
    Les classes de filtres concrètes (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, etc.) ne
    sont pas énumérées ici. Elles reprennent les filtres indépendants du backend documentés dans
    [Filters](../filters.md) ; les comportements spécifiques à MongoEngine sont décrits dans
    [MongoEngine](../../integrations/mongoengine.md#filter-registry).
