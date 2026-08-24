---
title: Champs personnalisés
description: Apprenez à créer des types de champs personnalisés dans starlette-admin
  pour gérer des types de données spécialisés et des widgets UI sur mesure.
source_hash: 5daa493733490d2421b0bacf11a0669eaad36b82cccc3dd0be3f7709e5681eb2
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/custom-fields/)
<!-- translation-notice:end -->

# Champs personnalisés

Les champs intégrés couvrent la plupart des colonnes que vous rencontrerez, mais lorsqu'aucun d'entre eux ne convient, vous pouvez créer le vôtre en dérivant de [`BaseField`](../api/fields.md#starlette_admin.fields.BaseField). Un champ se compose de trois méthodes qui font circuler les données entre votre modèle et le navigateur, plus un ensemble de chemins de templates qui le rendent. Dérivez directement de `BaseField`, ou étendez le champ intégré le plus proche de vos besoins (par exemple `StringField` ou `EnumField`) et ne remplacez que les parties qui diffèrent.

## Exemple minimal

```python
from dataclasses import dataclass
from dataclasses import field as dc_field

from starlette_admin.fields import EnumField


@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    badge_class_by_value: dict[str, str] = dc_field(
        default_factory=lambda: {
            "Online": "badge bg-success-lt",
            "Busy": "badge bg-danger-lt",
            "Offline": "badge",
        }
    )
```

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

Pointez votre instance d'`Admin` vers le répertoire des templates, puis utilisez ce champ dans votre vue :

```python
from starlette_admin.contrib.sqla import Admin, ModelView

admin = Admin(engine, title="My Admin", templates_dir="templates/")
```

```python
class EmployeeView(ModelView):
    fields = [
        "id",
        "name",
        StatusBadgeField("status", choices=["Online", "Busy", "Offline"]),
    ]
```

Comme `StatusBadgeField` dérive de `EnumField` plutôt que de `BaseField`, elle hérite de `choices`, de la validation du formulaire contre ces choix et du template par défaut `fields/form/enum.html` pour les formulaires de création et d'édition. Rien de tout cela n'a besoin de changer : la classe ne remplace donc que les attributs de rendu pour la liste et le détail.

Le reste de cette page décrit quoi remplacer lorsqu'un champ a besoin de plus qu'un simple changement de template. Pour le code complet fonctionnel, ainsi qu'un second champ (`AvatarNameField`) qui remplace effectivement les méthodes de données, consultez [`examples/advanced/05-custom-fields`](https://github.com/jowilf/starlette-admin/tree/main/examples/advanced/05-custom-fields).

## Les trois méthodes de données

| Méthode | Appelée lorsque | Signature |
| --- | --- | --- |
| `parse_form_data` | Un formulaire de création/édition est soumis | `async def parse_form_data(self, request: Request, form_data: FormData) -> Any` |
| `parse_obj` | Lecture d'une valeur depuis une instance de modèle pour affichage | `async def parse_obj(self, request: Request, obj: Any) -> Any` |
| `serialize_value` | Formatage d'une valeur pour le frontend (liste, détail, API, export) | `async def serialize_value(self, request: Request, value: Any) -> Any` |

`StatusBadgeField` ne remplace aucune d'entre elles, car `EnumField` analyse déjà la valeur soumise par rapport à `choices` et lit la chaîne brute depuis `obj.status`. Le badge n'est qu'une présentation posée par-dessus cette chaîne. Remplacez ces trois méthodes lorsque la valeur elle-même doit être calculée ou restructurée plutôt que simplement re-rendue.

!!! tip "Hooks ou héritage"
    Pour une modification ponctuelle d'un seul champ, une sous-classe est rarement nécessaire. Passez plutôt les [hooks `getter`, `formatter` et `parser`](../user-guide/fields.md#computing-formatting-and-parsing-values) comme arguments du constructeur, afin de gérer respectivement la lecture, le formatage d'affichage et l'analyse de l'entrée.
    **Quand dériver :** uniquement lorsque vous avez besoin de la même logique dans plusieurs vues, ou lorsque vous devez modifier les templates.

`parse_form_data` reçoit le `FormData` brut (issu de `starlette.datastructures`) de la requête et renvoie la donnée que `view.create()` ou `view.edit()` doit recevoir pour ce champ. L'implémentation par défaut lit `form_data.get(self.id)` et la renvoie inchangée. La plupart des champs ont seulement besoin d'ajouter une conversion de type :

```python
async def parse_form_data(self, request: Request, form_data: FormData) -> bool:
    raw = form_data.get(self.id)
    return raw in ("on", "true", "yes")
```

`parse_obj` reçoit l'instance de modèle et renvoie la valeur à afficher. L'implémentation par défaut renvoie `getattr(obj, self.name, None)`. Remplacez-la pour les champs qui ne correspondent pas à un unique attribut du modèle, comme un champ combinant deux colonnes. `AvatarNameField`, par exemple, combine une chaîne `name` avec l'avatar téléversé de la ligne :

```python
async def parse_obj(self, request: Request, obj: Any) -> Any:
    name = await super().parse_obj(request, obj)
    avatar_key = obj.avatar.get("key") if obj.avatar is not None else None
    return {"name": name, "avatar_key": avatar_key, "initials": self._initials(name)}
```

`serialize_value` reçoit ce que `parse_obj` (ou la couche ORM) a produit et le formate pour la requête courante. Elle est appelée séparément pour la page de liste, la page de détail, l'API JSON et les exports de données ; branchez donc sur `request.state.action` lorsque la forme doit différer selon le contexte. `AvatarNameField` n'a besoin de l'image d'avatar que sur la page de liste et retombe sur du texte simple partout ailleurs :

```python
async def serialize_value(self, request: Request, value: Any) -> Any:
    name, avatar_key = value.get("name"), value.get("avatar_key")
    if request.state.action != RequestAction.LIST:
        return name
    if avatar_key is not None:
        value["avatar_url"] = await self.avatars_storage.url(request, avatar_key)
    return value
```

!!! warning
    Ce que `serialize_value` renvoie pour `RequestAction.LIST` et `RequestAction.RELATION_LOOKUP` va directement dans une réponse JSON ; il doit donc être sérialisable en JSON.

## Chemins des templates

Chaque champ porte les attributs de template ci-dessous. Chacun est un chemin que le loader Jinja2 de l'admin résout : il vérifie d'abord votre `templates_dir`, si vous en avez défini un, puis retombe sur le répertoire intégré `starlette_admin/templates/`. Consultez [Templates](templates.md) pour les détails.

| Attribut | Défaut | Rendu pour |
| --- | --- | --- |
| `list_template` | `"fields/list/text.html"` | La valeur de colonne de chaque ligne sur la page de liste |
| `detail_template` | `"fields/detail/text.html"` | La page de détail en lecture seule |
| `form_template` | `"fields/form/input.html"` | Le champ de saisie du formulaire de création/édition |
| `null_template` | `"fields/detail/_null.html"` | Les pages de liste et de détail lorsque la valeur est `None` |
| `empty_template` | `"fields/detail/_empty.html"` | Les pages de liste et de détail lorsque la valeur est une liste ou un tuple vide |

Les cinq templates reçoivent l'instance `field` et la valeur `data` courante. Pour `list_template` et `detail_template`, `data` n'est jamais `None` ni vide, car ces cas sont redirigés vers `null_template` ou `empty_template` avant l'inclusion du template spécifique au type. Le `form_template` reçoit également `error` (le message d'une `FormValidationError`, si une erreur s'est produite) et `action` (`RequestAction.CREATE`, `RequestAction.EDIT` ou `RequestAction.INLINE_EDIT` lorsqu'il est rendu dans la fenêtre contextuelle d'[édition en ligne](../user-guide/inline-edit.md) de la page de liste). Ces trois valeurs sont des actions de formulaire, si bien que `action.is_form()` renvoie `True`. Le code d'un champ qui a besoin de la représentation sous forme de formulaire devrait se baser sur cela plutôt que sur `action == RequestAction.EDIT`.

Remplacez `null_template` et `empty_template` lorsqu'une valeur manquante doit avoir une apparence différente des étiquettes par défaut atténuées `-null-` et `-empty-`, par exemple une icône d'état vide ou un badge « Non renseigné » assorti au style propre au champ :

```python
@dataclass
class StatusBadgeField(EnumField):
    list_template: str = "employee/status_badge.html"
    detail_template: str = "employee/status_badge.html"
    null_template: str = "employee/status_badge_null.html"
    empty_template: str = "employee/status_badge_null.html"
```

```html title="templates/employee/status_badge_null.html"
<span class="badge">Unknown</span>
```

Comme `null_template` et `empty_template` sont de simples attributs de champ au même titre que `list_template`, ils sont partagés entre la liste, le détail et toute autre vue qui rend ce champ, comme le tableau en ligne d'une vue liée.

`StatusBadgeField` assigne le même template à `list_template` et à `detail_template`, car le même badge fonctionne dans les deux contextes :

```html title="templates/employee/status_badge.html"
<span class="{{ field.badge_class_by_value.get(data, 'badge') }}">{{ data }}</span>

```

`AvatarNameField` ne remplace que `list_template`. Dans ce template, la variable `data` est le dictionnaire construit par `parse_obj` puis remodelé par `serialize_value`, et non une simple chaîne :

```html title="templates/employee/avatar_name.html"
<span class="avatar avatar-xs me-2"
      {% if data.avatar_url %}style="background-image: url({{ data.avatar_url }})"{% endif %}>
    {% if not data.avatar_url %}{{ data.initials }}{% endif %}
</span>
<span class="inline-edit-value">{{ data.name }}</span>

```

La classe `inline-edit-value` est le marqueur opt-in pour le soulignement de l'[édition en ligne](../user-guide/inline-edit.md). Elle est inerte tant que le champ n'est pas éditable en ligne ; l'appliquer ici au nom et pas à l'avatar n'a donc aucun coût, tout en gardant cette affordance correctement délimitée si le champ devient éditable un jour.

Remplacer `list_template` et `detail_template` tout en conservant le `form_template` par défaut est exactement ce que fait `StatusBadgeField` en étendant `EnumField`. Le `fields/form/enum.html` par défaut rend un menu déroulant `<select>` alimenté par `field.choices`, si bien que l'édition d'un statut fonctionne sans modification supplémentaire.

## Enregistrement auprès du registre de conversion

La liste `fields = [...]` d'une vue accepte aussi bien des noms d'attributs simples que des objets champ. Tout élément qui n'est pas déjà un `BaseField` passe par un **registre de conversion** qui associe le type de colonne à une classe de champ. Chaque backend ORM fournit son propre registre (`starlette_admin.contrib.sqla.converters.ModelConverter` et leurs équivalents pour `beanie`, `mongoengine` et `tortoise`), tous construits sur la même base :

```python
from starlette_admin.converters import BaseModelConverter, converts
```

Le décorateur `@converts(*types)` marque une méthode comme convertisseur pour une ou plusieurs clés de type. `BaseModelConverter.__init__` parcourt l'instance à la recherche de ces méthodes décorées et construit son dictionnaire `converters` à partir d'elles. Pour le backend SQLAlchemy, les clés de type sont les **noms** des types de colonnes (`"String"`, `"Integer"`, `"Enum"`, etc.), car SQLAlchemy n'a pas de classe de base commune à tous les dialectes.

Dérivez du convertisseur du backend pour ajouter vos propres correspondances. Cet exemple route chaque colonne `Enum` vers `StatusBadgeField` au lieu du `EnumField` par défaut :

```python
from typing import Any

from starlette_admin.contrib.sqla.converters import ModelConverter
from starlette_admin.converters import converts
from starlette_admin.fields import BaseField


class MyModelConverter(ModelConverter):
    @converts("Enum")
    def conv_enum(self, *args: Any, **kwargs: Any) -> BaseField:
        _type = kwargs["type"]
        return StatusBadgeField(
            **self._field_common(*args, **kwargs), enum=_type.enum_class
        )
```

Passez la sous-classe à `ModelView(converter=...)` afin que les noms de champs textuels dans `fields = [...]` soient résolus via votre convertisseur plutôt que via celui par défaut :

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "name", "status"]


admin.add_view(EmployeeView(Employee, converter=MyModelConverter()))
```

Si vous construisez toujours explicitement vos champs, comme dans l'exemple minimal ci-dessus, vous pouvez vous passer du registre de conversion. Vous ne le nécessitez que lorsque vous voulez qu'une entrée telle que `fields = ["status"]` produise un `StatusBadgeField` à partir du type de colonne sous-jacent.

---

## Et ensuite ?

* **[Fields](../user-guide/fields.md) :** La référence complète des champs intégrés et le tableau des attributs de `BaseField`.
* **[Templates](templates.md) :** Comment le loader de templates résout `list_template`, `detail_template`, `form_template`, `null_template` et `empty_template`.
* **[Extension Points](extension-points.md) :** Toutes les autres surfaces enfichables de `starlette-admin`.
