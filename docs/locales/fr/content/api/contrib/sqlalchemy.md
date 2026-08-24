---
title: Référence de l'API Contrib SQLAlchemy
description: Documentation de référence de l'API pour l'intégration backend SQLAlchemy
  de starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/contrib/sqlalchemy/)
<!-- translation-notice:end -->

# Contrib : SQLAlchemy

Référence complète des attributs et méthodes du backend SQLAlchemy (`starlette_admin.contrib.sqla`),
générée à partir des docstrings. Pour un guide orienté vers les tâches, consultez la page
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Validation Pydantic

L'extension `ext.pydantic` valide les données du formulaire à l'aide d'un modèle Pydantic avant
l'enregistrement. Consultez [Validation Pydantic](../../integrations/sqlalchemy.md#pydantic-validation)
pour le guide complet.

::: starlette_admin.contrib.sqla.ext.pydantic.ModelView

## Champs

::: starlette_admin.contrib.sqla.fields.MultiplePKField

::: starlette_admin.contrib.sqla.fields.FileField

::: starlette_admin.contrib.sqla.fields.ImageField

## Convertisseurs

::: starlette_admin.contrib.sqla.converters.BaseSQLAModelConverter

::: starlette_admin.contrib.sqla.converters.ModelConverter

## Exceptions

::: starlette_admin.contrib.sqla.exceptions.InvalidModelError

::: starlette_admin.contrib.sqla.exceptions.InvalidQuery

::: starlette_admin.contrib.sqla.exceptions.NotSupportedColumn

::: starlette_admin.contrib.sqla.exceptions.NotSupportedValue

!!! note
    Les classes de filtres concrètes (`EqualFilter`, `ContainsFilter`, `BetweenFilter`, etc.) ne sont
    pas énumérées ici. Elles reprennent à l'identique les filtres indépendants du backend documentés dans
    [Filtres](../filters.md) ; le comportement spécifique à SQLAlchemy qu'il est utile de connaître est
    couvert dans [SQLAlchemy](../../integrations/sqlalchemy.md#filter-registry).
