---
title: Filtres
description: Ajoutez des capacités de filtrage AND/OR complexes et imbriquées à vos
  vues d'administration à l'aide de constructeurs de requêtes sensibles aux types.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
prompt_hash: 0bd45c6d5dcce61597a6a7d4092aab60033adf6d540437bd0d1499df82a2dbd5
machine_translated: true
translation_model: stealth/ox-alpha
translation_date: '2026-08-22'
---

??? info "Traduction automatique supervisée"

    Ce contenu est généré par traduction automatique, guidée par des
    glossaires et des guides de style validés par des humains. Comme le
    texte n'est pas relu ligne par ligne, des erreurs ou des formulations
    maladroites peuvent parfois apparaître.

    En cas de divergence, la [version originale en anglais](https://jowilf.github.io/starlette-admin/) fait foi.

# Filtres

Chaque champ d'une page de liste peut disposer de son propre ensemble d'opérateurs de filtrage, tels que `contains`, `between` et `is null`. Vos utilisateurs combinent ces opérateurs en un arbre imbriqué `AND`/`OR`, et vous n'avez jamais à écrire une requête complexe pour la base de données.

Le panneau d'administration déduit les filtres disponibles du type sous-jacent du champ. Vous pouvez restreindre, étendre ou remplacer entièrement cet ensemble pour n'importe quel champ.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Activer le filtrage et la recherche pour ces champs spécifiques
    searchable_fields = ["title", "content", "published", "created_at"]
```

Consultez [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) pour une application exécutable qui couvre les filtres par défaut, les remplacements par champ et une sous-classe personnalisée de `BaseFilter`.

Chaque champ que vous listez dans `searchable_fields` reçoit un menu déroulant **Filtres** dans la barre d'outils de la liste. À partir de là, les utilisateurs combinent autant de filtres que nécessaire pour trouver les lignes souhaitées.

## Fonctionnement du constructeur de filtres

La sélection du bouton **Filtres** ouvre un formulaire déroulant dans lequel les utilisateurs construisent leurs requêtes :

* **Ajouter un filtre** : ajoute une ligne de condition. L'utilisateur choisit un champ, sélectionne un opérateur parmi les filtres disponibles pour ce champ et fournit une valeur. Le champ de saisie s'adapte à l'opérateur : une zone de texte simple pour `contains`, deux zones pour `between`, et aucune saisie du tout pour `is null`.
* **Ajouter un groupe** : imbrique un sous-formulaire avec son propre sélecteur `AND`/`OR`. Utilisez-le pour construire des conditions telles que `A AND (B OR C)`.
* **Correspondre à tout ou partie des conditions suivantes** : détermine si le niveau actuel utilise la logique `AND` ou `OR`.
* **Appliquer les filtres** : soumet le formulaire sous forme de requête `GET`. Le panneau d'administration sérialise l'arbre complet de filtres en un seul paramètre de requête `filter`, décrit dans [Le format URL des filtres](#le-format-url-des-filtres).
* **Filtres actifs** : chaque filtre actif apparaît sous forme de pastille supprimable au-dessus du tableau. La sélection du symbole `×` soumet à nouveau la liste sans cette règle. Un groupe imbriqué se regroupe en une seule pastille que les utilisateurs suppriment dans son intégralité.

!!! tip
    Comme l'état complet des filtres est conservé dans l'URL, une liste filtrée peut être partagée. Vos utilisateurs peuvent ajouter la page à leurs favoris et envoyer le lien à un collègue.

## Remplacer les filtres d'un champ spécifique

Lorsque les filtres par défaut sont trop généraux, ou si vous avez besoin de quelque chose de plus spécifique, passez l'argument `filters=` à un champ pour remplacer son ensemble par défaut.

Vous pouvez réduire la liste aux opérateurs pertinents, l'étendre avec un filtre personnalisé, ou ajouter des opérateurs à un champ qui se limite par défaut aux vérifications de valeur nulle, tel que `TagsField` :

```python
from enum import Enum

from starlette_admin import (
    DateTimeField,
    DecimalField,
    EnumField,
    StringField,
    TagsField,
)
from starlette_admin.contrib.sqla import ModelView

# Importer les implémentations concrètes des filtres pour votre backend spécifique
from starlette_admin.contrib.sqla.filters import (
    BetweenFilter,
    DateInPastFilter,
    DateTimeBetweenFilter,
    GreaterThanFilter,
    NumericEqualFilter,
)


class ProductStatus(str, Enum):
    ACTIVE = "ACTIVE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class ProductView(ModelView):
    fields = [
        "id",
        StringField("name"),  # Utilise l'ensemble de filtres par défaut, aucun remplacement nécessaire
        EnumField("status", enum=ProductStatus),  # Utilise l'ensemble de filtres par défaut
        DecimalField(
            "price",
            # Réduit à seulement 3 des 9 filtres numériques par défaut
            filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter],
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

!!! important "Importer les filtres depuis votre backend"
    Les classes de filtres que vous passez à `filters=` doivent être les implémentations concrètes correspondant à votre backend de base de données : `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters` ou `.tortoise.filters`. Importez depuis le module `filters` de votre backend, pas depuis `starlette_admin.filters`.

## Le format URL des filtres

Le constructeur de filtres sérialise son état dans le paramètre de requête `filter` sous forme de chaîne compacte.

Le format est `field__operator` pour un filtre sans valeurs, `field__operator=value` pour une valeur unique, et `field__operator=value..value2` pour un filtre à deux valeurs tel que `between`. Les règles sont jointes par `AND` ou `OR`, et les parenthèses imbriquent un groupe :

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Placez une valeur entre guillemets lorsqu'elle contient un espace ou une parenthèse : `name__eq="quoted value"`. Une valeur de liste pour un filtre à sélection multiple tel que `is one of` est séparée par des virgules et ne nécessite pas de guillemets : `status__in=ACTIVE,OUT_OF_STOCK`.

Lorsque l'URL contient une chaîne `filter` invalide, telle qu'un champ inconnu, un opérateur indisponible ou une valeur impossible à analyser, l'application renvoie une erreur `HTTP 400` au lieu de supprimer silencieusement une partie de la condition.

!!! important
    Seuls les champs que vous listez dans `searchable_fields` reçoivent des filtres. Si vous laissez `searchable_fields` non défini, chaque champ en reçoit.


## Référence des filtres intégrés

Le tableau suivant répertorie chaque filtre disponible dès l'installation, l'identifiant d'URL que vous voyez dans un lien mis en favori et le type de valeur attendu par chacun. Les filtres marqués « deux valeurs » nécessitent à la fois un `value` et un `value2` dans l'URL, par exemple `between=2026-01-01..2026-01-31`.

| Filtre | Identifiant | Type de valeur | Deux valeurs ? |
| --- | --- | --- | --- |
| Contient | `contains` | texte |  |
| Ne contient pas | `not_contains` | texte |  |
| Commence par | `startswith` | texte |  |
| Se termine par | `endswith` | texte |  |
| Égal à | `eq` | texte, nombre, date, datetime ou heure |  |
| Différent de | `neq` | texte ou nombre |  |
| Est nul | `is_null` | *(aucune)* |  |
| N'est pas nul | `is_not_null` | *(aucune)* |  |
| Supérieur à | `gt` | nombre |  |
| Inférieur à | `lt` | nombre |  |
| Supérieur ou égal à | `gte` | nombre |  |
| Inférieur ou égal à | `lte` | nombre |  |
| Entre | `between` | nombre, date, datetime ou heure | ✓ |
| Est dans le passé | `in_past` | *(aucune)* |  |
| Est dans le futur | `in_future` | *(aucune)* |  |
| Est vrai | `is_true` | *(aucune)* |  |
| Est faux | `is_false` | *(aucune)* |  |
| Fait partie de | `in` | liste séparée par des virgules |  |
| Ne fait pas partie de | `not_in` | liste séparée par des virgules |  |

Si vous avez besoin d'un filtre pour un type de données non couvert par les filtres intégrés, tel qu'un champ JSON ou un point géographique, consultez [Filtres personnalisés](../advanced/custom-filters.md) pour écrire une sous-classe de `BaseFilter` et l'enregistrer globalement ou par instance de champ.

---

**Pour aller plus loin**

* **[Filtres personnalisés](../advanced/custom-filters.md) :** Écrire et enregistrer une sous-classe de `BaseFilter`.
* **[Actions](actions.md) :** Ajouter des actions groupées et des actions de ligne à vos pages de liste.
* **[Vues](views.md) :** En savoir plus sur `searchable_fields` et le reste de la configuration des pages de liste.
