---
title: Édition en ligne
description: Permettez aux utilisateurs de modifier directement les valeurs des champs
  dans le tableau de la page de liste pour une saisie de données plus rapide.
source_hash: eaec1e767aabf070c53dc837993958784bc8326597e2c008e52bf592dc1f1ae2
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/user-guide/inline-edit/)
<!-- translation-notice:end -->

# Édition en ligne

L'édition en ligne permet aux utilisateurs de modifier un seul champ directement depuis la page de liste. La sélection d'une cellule ouvre une petite fenêtre contextuelle, ce qui évite d'avoir à ouvrir le formulaire d'édition complet. Utilisez-la pour des mises à jour rapides portant sur un seul champ : corriger un titre, basculer un statut ou ajuster une date. L'interaction suit le modèle familier de [x-editable](https://vitalets.github.io/x-editable/).

Cette fonctionnalité est optionnelle et désactivée par défaut. Son activation ne modifie pas la page d'édition standard, qui reste l'interface principale pour les éditions complexes portant sur plusieurs champs.

> Pour un exemple exécutable avec l'édition en ligne, consultez [examples/01-quickstart](https://github.com/jowilf/starlette-admin/tree/main/examples/01-quickstart).

## Utilisation de base

Déclarez les noms des champs modifiables dans la liste `inline_editable_fields` :

```python
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    fields = ["id", "title", "content", "status", "views", "published_at"]
    inline_editable_fields = ["title", "status", "views", "published_at"]
```

Les cellules modifiables affichent alors un soulignement en pointillés sur la page de liste. La sélection d'une cellule ouvre une fenêtre contextuelle avec le contrôle de formulaire standard du champ, prérempli avec la valeur actuelle.

Le soulignement n'est pas appliqué à toute la cellule. Chaque template de liste place la classe CSS `inline-edit-value` sur l'élément exact à souligner, et le style s'applique uniquement à l'intérieur d'une cellule modifiable. Tous les templates de liste intégrés comportent déjà cette classe. Si vous écrivez un `list_template` personnalisé et souhaitez la même indication visuelle, ajoutez vous-même la classe :

```html
<span class="avatar avatar-xs me-2">...</span>
<span class="inline-edit-value">{{ data.name }}</span>
```

Sans la classe, la cellule ouvre toujours la fenêtre contextuelle, mais elle n'affiche aucun soulignement.

- **Enregistrer :** sélectionnez le bouton de validation ou appuyez sur <kbd>Entrée</kbd> dans un champ de saisie sur une seule ligne. Le panneau d'administration valide le champ, enregistre la modification et actualise la ligne sans recharger la page.
- **Annuler :** sélectionnez le bouton <kbd>x</kbd> ou appuyez sur <kbd>Échap</kbd> pour abandonner la modification.

## Règles de configuration

L'application valide `inline_editable_fields` au démarrage afin que les erreurs de configuration soient détectées rapidement. Un nom listé lève une exception `ValueError` s'il répond à l'une des conditions suivantes :

- Il n'est pas déclaré dans `fields`.
- C'est le champ de clé primaire.
- Il est exclu de la page de liste (`exclude_from_list`) ou du formulaire d'édition (`exclude_from_edit`).
- C'est un champ conteneur ou en lecture seule : `CollectionField`, `ListField`, `ComputedField`, `FileField` ou `ImageField`.

## Champs pris en charge

Chaque champ modifiable affiche le même widget de formulaire qu'il utilise sur la page d'édition. Les ressources JavaScript et CSS d'un champ, telles que select2, flatpickr, JSONEditor ou TinyMCE, sont chargées sur la page de liste uniquement lorsque ce champ est modifiable en ligne. Les vues sans édition en ligne conservent leur empreinte de page légère actuelle.

| Type de champ                                                                        | Pris en charge | Widget contextuel                     |
| ------------------------------------------------------------------------------------ | -------------- | ------------------------------------- |
| `StringField`, `EmailField`, `URLField`, `PhoneField`, `ColorField`, `PasswordField` | Oui            | Champ de saisie simple                |
| `SlugField`                                                                          | Oui            | Champ de saisie simple (champ source exclu) |
| `TextAreaField`                                                                      | Oui            | Zone de texte                         |
| `IntegerField`, `DecimalField`, `FloatField`                                         | Oui            | Champ de saisie numérique             |
| `BooleanField`                                                                       | Oui            | Bascule                               |
| `DateField`, `DateTimeField`, `TimeField`, `ArrowField`                              | Oui            | flatpickr                             |
| `EnumField`, `TimeZoneField`, `CountryField`, `CurrencyField`                        | Oui            | select2 ou select natif               |
| `TagsField`                                                                          | Oui            | select2 avec balises                  |
| `JSONField`                                                                          | Oui            | JSONEditor                            |
| `TinyMCEEditorField`                                                                 | Oui            | TinyMCE                               |
| `HasOne`, `HasMany`                                                                  | Oui            | select2 avec recherche asynchrone     |
| `FileField`, `ImageField`                                                            | Non            | Aucun (nécessite la page d'édition)   |
| `CollectionField`, `ListField`, `ComputedField`                                      | Non            | Aucun (conteneurs en lecture seule)   |

---

## Permissions

L'édition en ligne réutilise le modèle de permissions existant. La fenêtre contextuelle apparaît et le panneau d'administration accepte la requête uniquement lorsque `is_accessible(request)` et `can_edit(request)` renvoient tous deux `True`. La substitution de `can_edit` sécurise donc également les modifications en ligne :

```python
class PostView(ModelView):
    inline_editable_fields = ["title", "status"]

    def can_edit(self, request: Request) -> bool:
        # Also disables inline edit when False
        return "edit:post" in request.state.admin_user.roles
```

---

## Validation

Un enregistrement en ligne valide et écrit uniquement le champ modifié.

- La vérification `required` du champ et la chaîne de `validators` s'exécutent exactement comme sur la page d'édition.
- Les autres champs sont ignorés. Un enregistrement depuis la page de liste ne peut pas écraser une modification concurrente portant sur un autre champ, et des données invalides dans un autre champ ne bloquent pas l'enregistrement.

Le hook `validate` multi-champs de la vue s'exécute toujours, mais le dictionnaire `data` ne contient que le champ modifié. Un hook qui s'attend à une soumission de formulaire complète lève une exception `KeyError` s'il indexe directement des clés manquantes ; vérifiez donc d'abord qu'une clé est présente :

```python
from typing import Any
from starlette.requests import Request
from starlette_admin.exceptions import FormValidationError
from starlette_admin.contrib.sqla import ModelView


class PostView(ModelView):
    inline_editable_fields = ["title", "status", "published_at"]

    async def validate(self, request: Request, data: dict[str, Any]) -> None:
        errors: dict[str, str] = {}

        if "title" in data and (not data["title"] or len(data["title"]) < 3):
            errors["title"] = "Ensure this value has at least 3 characters"

        if (
            "published_at" in data
            and data.get("status") == "published"
            and data["published_at"] is None
        ):
            errors["published_at"] = "Required when status is published"

        if errors:
            raise FormValidationError(errors)

        await super().validate(request, data)
```

En cas d'échec de la validation, la fenêtre contextuelle reste ouverte avec la valeur soumise intacte. Le message du champ modifié s'affiche sous le contrôle, exactement comme sur la page d'édition. Un message associé à un autre champ est préfixé par le libellé de ce champ.

Pour détecter un enregistrement en ligne à l'intérieur d'un hook, vérifiez `request.state.action == RequestAction.INLINE_EDIT`. Utilisez-le pour ignorer les messages flash destinés aux rendus de pages complètes.

!!! warning
    Une règle de validation associée à un champ que l'utilisateur n'a pas modifié ne s'exécute pas lors d'un enregistrement en ligne. Si les invariants d'un champ dépendent de valeurs que l'utilisateur ne peut ni voir ni modifier depuis la page de liste, excluez ce champ de `inline_editable_fields`.

---

## Hooks de cycle de vie et événements

Les enregistrements en ligne passent par le chemin `edit()` standard de la vue. Les hooks `before_edit`, `after_edit` et `after_edit_committed` se déclenchent comme d'habitude, et les [événements](../advanced/events.md) correspondants utilisent les types de contexte standard. Les charges utiles `data` et `old_data` ne contiennent que le champ modifié ; elles reflètent donc exactement ce que l'enregistrement a touché.

Pour distinguer un enregistrement en ligne à l'intérieur d'un écouteur d'événements, vérifiez `ctx.extra["inline"]`, qui vaut `True` pour les modifications en ligne :

```python
from starlette_admin import AdminEvent
from starlette_admin.events import AfterEditContext


@admin.events.on(AdminEvent.AFTER_EDIT)
async def audit(ctx: AfterEditContext) -> None:
    source = "list page" if ctx.extra.get("inline") else "edit page"
    logger.info("updated %s pk=%s from the %s", ctx.view_key, ctx.pk, source)
```

---

## Champs personnalisés

Les champs personnalisés prennent en charge automatiquement l'édition en ligne lorsqu'ils respectent le contrat standard de `BaseField`. Comme `RequestAction.INLINE_EDIT` est une action de formulaire, `action.is_form()` renvoie `True`. Si votre champ personnalisé vérifie `action == RequestAction.EDIT` pour construire une représentation de valeur de formulaire, remplacez cette vérification par `action.is_form()` afin que la fenêtre contextuelle reçoive la bonne représentation. Pour connaître le contrat complet des champs, consultez [Champs personnalisés](../advanced/custom-fields.md).
