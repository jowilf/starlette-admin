---
title: Référence de l'API Contrib SQLAlchemy
description: Documentation de référence de l'API pour l'intégration du backend SQLAlchemy
  dans starlette-admin.
source_hash: c966b22ba523b8451e3c0168394e068bf412475140a3d5427bc0c70d2c6d971d
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
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

Référence complète des attributs et des méthodes du backend SQLAlchemy (`starlette_admin.contrib.sqla`),
générée à partir des docstrings. Pour un guide orienté tâches, consultez
[SQLAlchemy](../../integrations/sqlalchemy.md).

::: starlette_admin.contrib.sqla.admin.Admin

::: starlette_admin.contrib.sqla.view.ModelView

::: starlette_admin.contrib.sqla.view.InlineModelView

## Validation Pydantic

L'extension `ext.pydantic` valide les données du formulaire par rapport à un modèle Pydantic avant
d'écrire l'enregistrement. Consultez [Validation Pydantic](../../integrations/sqlalchemy.md#validation-pydantic) pour
le guide complet.

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
    Les classes concrètes de filtres (`EqualFilter`, `ContainsFilter`, `BetweenFilter`, etc.) ne sont pas
    énumérées ici. Elles correspondent un à un aux filtres indépendants du backend documentés dans
    [Filtres](../filters.md) ; les comportements spécifiques à SQLAlchemy qu'il est utile de connaître sont
    traités dans [SQLAlchemy](../../integrations/sqlalchemy.md#registre-de-filtres).
