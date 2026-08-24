---
title: Filtres
description: Ajoutez des capacités de filtrage AND/OR complexes et imbriquées à vos
  vues d'administration grâce à des constructeurs de requêtes sensibles aux types.
source_hash: e42a5eccf8e516fe88adb3dcbc989e7c7707b29918b89c8c662d7062b0c6a241
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/filters/)
<!-- translation-notice:end -->

# Filtres

Chaque champ d'une page de liste peut disposer de son propre ensemble d'opérateurs de filtrage, tels que `contains`, `between` ou `is null`. Vos utilisateurs combinent ces opérateurs en un arbre `AND`/`OR` imbriqué, et vous n'avez jamais à écrire une requête complexe en base de données.

L'admin déduit les filtres disponibles du type sous-jacent du champ. Vous pouvez restreindre, étendre ou remplacer entièrement cet ensemble pour n'importe quel champ.


```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "published", "created_at"]
    # Activer le filtrage et la recherche pour ces champs spécifiques
    searchable_fields = ["title", "content", "published", "created_at"]
```

Consultez [examples/02-filters](https://github.com/jowilf/starlette-admin/tree/main/examples/02-filters) pour une application exécutable couvrant les filtres par défaut, les remplacements par champ et une sous-classe personnalisée de `BaseFilter`.

Chaque champ listé dans `searchable_fields` reçoit un menu déroulant **Filtres** dans la barre d'outils de la liste. À partir de là, les utilisateurs combinent autant de filtres que nécessaire pour trouver les lignes recherchées.

## Fonctionnement du constructeur de filtres

La sélection du bouton **Filtres** ouvre un formulaire déroulant dans lequel les utilisateurs construisent leurs requêtes :

* **Ajouter un filtre** : ajoute une ligne de condition. L'utilisateur choisit un champ, sélectionne un opérateur parmi les filtres disponibles pour ce champ et fournit une valeur. Le champ de saisie s'adapte à l'opérateur : une simple zone de texte pour `contains`, deux zones pour `between`, et aucune saisie pour `is null`.
* **Ajouter un groupe** : imbrique un sous-formulaire doté de son propre sélecteur `AND`/`OR`. Utilisez-le pour construire des conditions du type `A AND (B OR C)`.
* **Correspondre à tous/aucun des éléments suivants** : détermine si le niveau courant utilise la logique `AND` ou `OR`.
* **Appliquer les filtres** : soumet le formulaire sous forme de requête `GET`. L'admin sérialise l'intégralité de l'arbre de filtres dans un seul paramètre de requête `filter`, décrit dans [Le format URL des filtres](#the-filter-url-format).
* **Filtres actifs** : chaque filtre actif apparaît sous forme d'une pastille supprimable au-dessus du tableau. La sélection du `×` recharge la liste sans cette règle. Un groupe imbriqué est réduit en une seule pastille que les utilisateurs suppriment dans son intégralité.

!!! tip
    Comme tout l'état des filtres est contenu dans l'URL, une liste filtrée est partageable. Vos utilisateurs peuvent mettre la page en favori et envoyer le lien à un collègue.

## Remplacer les filtres d'un champ spécifique {#overriding-filters-for-a-specific-field}

Lorsque les filtres par défaut sont trop larges, ou si vous avez besoin de quelque chose de plus spécifique, passez l'argument `filters=` à un champ pour remplacer son ensemble par défaut.

Vous pouvez restreindre la liste aux opérateurs qui vous importent, l'étendre avec un filtre personnalisé, ou ajouter des opérateurs à un champ qui ne dispose par défaut que des vérifications basiques de nullité, comme `TagsField` :

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
            # Restreint à seulement 3 des 9 filtres numériques par défaut
            filters=[GreaterThanFilter, BetweenFilter, NumericEqualFilter],
        ),
        DateTimeField("created_at", filters=[DateTimeBetweenFilter, DateInPastFilter]),
    ]
```

!!! important "Importer les filtres depuis votre backend"
    Les classes de filtres que vous passez à `filters=` doivent être les implémentations concrètes correspondant à votre backend de base de données : `starlette_admin.contrib.sqla.filters`, `.beanie.filters`, `.mongoengine.filters`, ou `.tortoise.filters`. Importez depuis le module `filters` de votre backend, et non depuis `starlette_admin.filters`.

## Le format URL des filtres {#the-filter-url-format}

Le constructeur de filtres sérialise son état dans le paramètre de requête `filter` sous forme d'une chaîne compacte.

Le format est `field__operator` pour un filtre sans valeur, `field__operator=value` pour une valeur unique, et `field__operator=value..value2` pour un filtre à deux valeurs tel que `between`. Les règles sont jointes par `AND` ou `OR`, et les parenthèses imbriquent un groupe :

```text
/admin/product/list?filter=price__gt=50+AND+status__eq=ACTIVE

```

```text
/admin/product/list?filter=created_at__between=2026-01-01..2026-01-31+AND+(price__gt=12+OR+price__eq=8)

```

Placez une valeur entre guillemets lorsqu'elle contient un espace ou une parenthèse : `name__eq="quoted value"`. Une valeur de liste pour un filtre à sélection multiple tel que `is one of` est séparée par des virgules et ne nécessite pas de guillemets : `status__in=ACTIVE,OUT_OF_STOCK`.

Lorsque l'URL contient une chaîne `filter` invalide, comme un champ inconnu, un opérateur indisponible ou une valeur non analysable, l'application renvoie une erreur `HTTP 400` plutôt que de rejeter silencieusement une partie de la condition.

!!! important
    Seuls les champs listés dans `searchable_fields` reçoivent des filtres. Si vous laissez `searchable_fields` non défini, tous les champs les reçoivent.


## Référence des filtres intégrés

Le tableau suivant recense chaque filtre disponible nativement, le slug URL visible dans un lien mis en favori, ainsi que le type de valeur attendu par chacun. Les filtres marqués « deux valeurs » nécessitent à la fois une `value` et une `value2` dans l'URL, par exemple `between=2026-01-01..2026-01-31`.

| Filtre | Slug | Type de valeur | Deux valeurs ? |
| --- | --- | --- | --- |
| Contient | `contains` | texte |  |
| Ne contient pas | `not_contains` | texte |  |
| Commence par | `startswith` | texte |  |
| Finit par | `endswith` | texte |  |
| Égal | `eq` | texte, nombre, date, datetime ou heure |  |
| Différent | `neq` | texte ou nombre |  |
| Est null | `is_null` | *(aucune)* |  |
| N'est pas null | `is_not_null` | *(aucune)* |  |
| Supérieur à | `gt` | nombre |  |
| Inférieur à | `lt` | nombre |  |
| Supérieur ou égal | `gte` | nombre |  |
| Inférieur ou égal | `lte` | nombre |  |
| Entre | `between` | nombre, date, datetime ou heure | ✓ |
| Est dans le passé | `in_past` | *(aucune)* |  |
| Est dans le futur | `in_future` | *(aucune)* |  |
| Est vrai | `is_true` | *(aucune)* |  |
| Est faux | `is_false` | *(aucune)* |  |
| Fait partie de | `in` | liste séparée par des virgules |  |
| Ne fait pas partie de | `not_in` | liste séparée par des virgules |  |

Si vous avez besoin d'un filtre pour un type de données non couvert par les filtres intégrés, comme un champ JSON ou un point géographique, consultez [Filtres personnalisés](../advanced/custom-filters.md) pour écrire une sous-classe de `BaseFilter` et l'enregistrer globalement ou pour une instance de champ donnée.

---

**Et ensuite**

* **[Filtres personnalisés](../advanced/custom-filters.md) :** écrire et enregistrer une sous-classe de `BaseFilter`.
* **[Actions](actions.md) :** ajouter des actions groupées et des actions sur les lignes à vos pages de listes.
* **[Vues](views.md) :** en savoir plus sur `searchable_fields` et le reste de la configuration de la page de liste.
