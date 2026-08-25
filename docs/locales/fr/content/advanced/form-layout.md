---
title: Mises en page de formulaire
description: Concevez des mises en page de formulaires complexes et responsives à
  l'aide de TabsWidget, FieldsetWidget et des colonnes de grille dans starlette-admin.
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# Mises en page de formulaire

Par défaut, les formulaires de création et d'édition affichent tout ce qui se trouve dans `fields` sous la forme d'une simple liste à plat. L'attribut `form_layout` vous permet d'organiser ces champs avec les mêmes widgets composables que ceux utilisés pour les [tableaux de bord](../user-guide/custom-views.md) : rangées côte à côte, panneaux avec titre ou repliables, onglets, contenu statique et vos propres widgets personnalisés.

## Utilisation de base

La mise en page la plus simple ne nécessite aucun widget. Référencez un champ par son nom sous forme de chaîne de caractères pour le conserver sur sa propre ligne, et regroupez plusieurs noms dans un tuple pour les placer côte à côte sur une même ligne.

```python
from starlette_admin.contrib.sqla import ModelView


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        ("first_name", "last_name"),
        "email",
        ("salary", "notes"),
    ]
```

Dans la mise en page ci-dessus :

* `("first_name", "last_name")` crée une ligne répartie équitablement entre les deux champs.
* `"email"` s'affiche sur sa propre ligne, juste en dessous.
* `("salary", "notes")` crée une seconde ligne multi-colonnes.

Vous pouvez placer autant de champs que vous le souhaitez dans une ligne et mélanger librement des lignes à une colonne et des lignes multi-colonnes.

Les widgets conteneurs développent eux-mêmes cette syntaxe abrégée : `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget` et `Col` convertissent tous les tuples en lignes et les listes en colonnes empilées lors de leur construction. La syntaxe abrégée fonctionne donc également dans les attributs `children` imbriqués et dans un tableau de bord [`CustomView.widget`](../user-guide/custom-views.md).

## Regroupement des champs

### Panneaux avec titre

Pour donner un titre à un groupe de champs, ou pour le rendre repliable, enveloppez-le dans un `PanelWidget`. Ce widget accepte la même syntaxe abrégée (chaînes et tuples) que le niveau supérieur.

```python
from starlette_admin import PanelWidget


class EmployeeView(ModelView):
    fields = ["id", "first_name", "last_name", "email", "salary", "notes"]
    form_layout = [
        PanelWidget(
            title="Identity",
            children=[("first_name", "last_name"), "email"],
        ),
        PanelWidget(
            title="Compensation",
            children=["salary", "notes"],
            collapsible=True,
            collapsed=True,
        ),
    ]
```

`PanelWidget` accepte les attributs suivants :

| Attribut | Description |
| --- | --- |
| `title` | Le titre affiché dans l'en-tête de carte du panneau. |
| `children` | Les widgets affichés à l'intérieur du panneau, dans l'ordre. Accepte la syntaxe abrégée décrite ci-dessus ou des widgets imbriqués. Ajoutez un enfant `TextWidget(card=False)` pour insérer un texte explicatif sous le titre. |
| `collapsible` | Permet aux utilisateurs de déplier et de replier le panneau. |
| `collapsed` | Affiche le panneau initialement replié. Ne s'applique que lorsque `collapsible=True`. |

Pour un groupe qui n'a pas besoin de titre, utilisez plutôt `ColumnWidget`. Il empile ses enfants verticalement sans les envelopper dans une carte stylisée.

### Fieldsets

`FieldsetWidget` regroupe les champs de manière similaire à `PanelWidget`, mais affiche un élément HTML natif `<fieldset>` et `<legend>` au lieu d'une carte stylisée. Utilisez-le lorsque vous souhaitez un regroupement plus simple, avec bordures.

```python
from starlette_admin import FieldsetWidget

form_layout = [
    FieldsetWidget(
        legend="Identity",
        children=[("first_name", "last_name"), "email"],
    ),
    FieldsetWidget(
        legend="Compensation",
        children=["salary", "notes"],
        disabled=True,
    ),
]
```

L'attribut `legend` définit la légende de l'élément `<legend>`. `disabled=True` ajoute l'attribut HTML `disabled` au conteneur, ce qui désactive tous les contrôles de formulaire imbriqués. `FieldsetWidget` prend en charge la même syntaxe abrégée pour `children` que `PanelWidget`, mais pas les options spécifiques aux panneaux telles que `collapsible` et `icon`.

## Largeurs de colonnes explicites

La syntaxe abrégée par tuple répartit toujours une ligne de manière égale. Pour un contrôle plus fin des largeurs de colonnes, construisez explicitement la ligne avec `RowWidget`, `Col` et `FieldRef` :

```python
from starlette_admin import Breakpoints, Col, FieldRef, RowWidget

form_layout = [
    RowWidget(
        children=[
            Col(FieldRef("first_name"), Breakpoints(default=12, md=4)),
            Col(FieldRef("last_name"), Breakpoints(default=12, md=8)),
        ]
    ),
]
```

## Masquage des libellés des champs

La construction explicite d'un `FieldRef` vous donne accès au paramètre `show_label`, qui supprime l'élément `<label>` lorsque la mise en page environnante rend déjà évidente la finalité du champ.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` vaut `True` par défaut. Les syntaxes abrégées par chaîne et par tuple affichent toujours les libellés, car elles n'acceptent pas d'arguments nommés.

## Groupes de saisie

Les paramètres `prepend` et `append` attachent un addon de [groupe de saisie](https://docs.tabler.io/ui/forms/form-elements#input-group) à gauche ou à droite d'un champ. Chacun accepte du texte brut ou du HTML brut, tel qu'une icône Font Awesome.

```python
from starlette_admin import FieldRef

form_layout = [
    FieldRef("email", prepend="@"),
    FieldRef("phone", append='<i class="fa fa-phone"></i>'),
    FieldRef("salary", prepend="$", append="USD"),
]
```

Les addons fonctionnent sur les champs dont le template de formulaire affiche un élément `<input>` natif : `StringField`, `EmailField`, `URLField`, `PhoneField`, `PasswordField`, `ColorField`, `SlugField`, les champs numériques (`IntegerField`, `DecimalField`, `FloatField`) ainsi que les champs de date et d'heure. Les autres types, tels que `EnumField`, `TextAreaField` et `BooleanField`, les ignorent silencieusement.

!!! warning
    Les valeurs des addons sont affichées sans échappement afin que du HTML tel que le balisage d'icônes fonctionne correctement. Ne transmettez que du contenu fiable que vous avez rédigé vous-même, jamais des saisies utilisateur.

## Onglets

Pour diviser les sections en une interface à onglets, utilisez `TabsWidget`. Il prend une liste de paires `(label, widgets)`.

```python
from starlette_admin import TabsWidget

form_layout = [
    TabsWidget(
        tabs=[
            ("Identity", [("first_name", "last_name"), "email"]),
            ("Compensation", ["salary", "notes"]),
        ]
    ),
]
```

## Contenu statique

Utilisez `HtmlWidget` et `TextWidget` pour afficher du contenu arbitraire n'importe où dans la mise en page : instructions, avertissements ou séparateurs.

```python
from starlette_admin import HtmlWidget, PanelWidget

form_layout = [
    HtmlWidget(html="<p class='text-warning'>Changes here are audited.</p>"),
    PanelWidget(title="Compensation", children=["salary", "notes"]),
]
```

## Widgets personnalisés

Comme `form_layout` partage la hiérarchie `BaseWidget` avec les tableaux de bord, vous pouvez hériter de `BaseWidget` pour créer vos propres éléments. C'est la solution de secours pour tout ce que les widgets intégrés ne couvrent pas, comme des aperçus en lecture seule, des graphiques embarqués ou des macros personnalisées.

Consultez [Custom Views & Widgets](../user-guide/custom-views.md) pour le schéma général, ainsi que la [référence de l'API Widgets](../api/widgets.md) pour connaître les méthodes qu'une classe fille peut redéfinir. Les widgets personnalisés présents dans `form_layout` sont toujours affichés, quelles que soient les règles de visibilité des champs.

## Contrôle d'accès et visibilité

`form_layout` respecte vos règles d'accès au niveau des champs. Chaque `FieldRef` passe par le contrôle habituel `can_access_field`, et les permissions `exclude_from_create`, `exclude_from_edit` ainsi que celles basées sur les rôles restent toutes en vigueur.

* **Expansion des lignes :** lorsqu'un champ d'une ligne multi-colonnes est masqué pour une requête, les champs visibles restants s'étendent pour occuper l'espace disponible.
* **Conteneurs vides :** lorsque tous les champs d'un conteneur (ligne, panneau, fieldset, colonne, grille ou onglet) sont masqués, le conteneur est omis, de sorte que vous n'obtenez jamais une coquille vide.
* **Rendu statique :** les composants statiques tels que `HtmlWidget`, `TextWidget` et les classes filles personnalisées de `BaseWidget` sont toujours affichés, car ils ne dépendent pas des champs du formulaire.

## Gestion des champs omis

Un champ déclaré dans `fields` mais absent de `form_layout` est ajouté en bas du formulaire, dans l'ordre de déclaration, afin qu'aucun champ ne soit jamais perdu silencieusement.

Le fait de référencer deux fois le même champ, ou de référencer un nom absent de `fields`, déclenche une `ValueError` lors de la construction de la vue.

---

## Et ensuite ?

* **[Custom Views & Widgets](../user-guide/custom-views.md) :** la hiérarchie de widgets sur laquelle repose `form_layout`, et comment écrire votre propre widget.
* **[Templates](templates.md) :** remplacez `_form_group.html` pour modifier le balisage généré par un groupe de mise en page.
* **[Fields](../user-guide/fields.md) :** les types de champs et les règles de visibilité qu'une mise en page organise.
