---
title: Référence de l'API Contrib Beanie
description: Documentation de référence de l'API pour l'intégration du backend Beanie
  dans starlette-admin.
source_hash: 6a89593e9010ec12dd664910d2bbb407467441efa960bc4a6fefd818a7d71b36
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/contrib/beanie/)
<!-- translation-notice:end -->

# Contrib : Beanie

Référence complète des attributs et des méthodes du backend Beanie (`starlette_admin.contrib.beanie`),
générée à partir des docstrings. Pour une présentation orientée tâches, consultez la page
[Beanie](../../integrations/beanie.md).

::: starlette_admin.contrib.beanie.admin.Admin

::: starlette_admin.contrib.beanie.view.ModelView

::: starlette_admin.contrib.beanie.view.InlineModelView

## Fields

::: starlette_admin.contrib.beanie.fields.BeanieObjectIdField

## Converters

::: starlette_admin.contrib.beanie.converters.BeanieModelConverter

!!! note
    Les classes de filtres concrètes (`EqualFilter`, `ArrayInFilter`, `ObjectIdEqualFilter`, etc.) ne sont pas
    énumérées ici. Elles reprennent les filtres indépendants du backend documentés dans
    [Filters](../filters.md) ; les comportements spécifiques à Beanie (correspondance de chaînes par regex ancrée,
    recherche plein texte) sont décrits dans [Beanie](../../integrations/beanie.md#filter-registry).
