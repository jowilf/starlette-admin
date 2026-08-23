---
title: Mises en page de formulaire
description: Concevez des mises en page de formulaire complexes et responsives à l'aide
  de TabsWidget, FieldsetWidget et des colonnes de grille dans starlette-admin.
source_hash: ab3f17593165b8c7e689af55be35a5b79b082aca4f984f7eb610c0b292763ea5
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/advanced/form-layout/)
<!-- translation-notice:end -->

# Mises en page de formulaire

Par défaut, les formulaires de création et d'édition affichent tout ce qui se trouve dans `fields` sous la forme d'une simple liste à plat. L'attribut `form_layout` vous permet d'organiser ces champs avec les mêmes widgets composables que ceux utilisés pour les [tableaux de bord](../user-guide/custom-views.md) : lignes côte à côte, panneaux titrés ou repliables, onglets, contenu statique et vos propres widgets personnalisés.

## Utilisation de base

La mise en page la plus simple ne nécessite aucun widget. Référencez un champ par son nom sous forme de chaîne pour le conserver sur sa propre ligne, et regroupez plusieurs noms dans un tuple pour les placer côte à côte sur une même ligne.

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

Vous pouvez placer autant de champs que vous le souhaitez dans une ligne et mélanger librement les lignes à une colonne et celles à plusieurs colonnes.

Les widgets conteneurs développent eux-mêmes cette notation abrégée : `RowWidget`, `ColumnWidget`, `GridWidget`, `PanelWidget`, `FieldsetWidget`, `TabsWidget` et `Col` transforment tous les tuples en lignes et les listes en colonnes empilées lors de leur construction. La notation abrégée fonctionne donc également dans les attributs `children` imbriqués et dans un tableau de bord [`CustomView.widget`](../user-guide/custom-views.md).

## Regroupement des champs

### Panneaux titrés

Pour donner un titre à un groupe de champs, ou pour le rendre repliable, enveloppez-le dans un `PanelWidget`. Ce widget accepte la même notation abrégée par chaînes et tuples qu'au niveau supérieur.

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
| `title` | Le titre affiché dans l'en-tête de la carte du panneau. |
| `children` | Les widgets affichés à l'intérieur du panneau, dans l'ordre. Accepte la notation abrégée ci-dessus ou des widgets imbriqués. Ajoutez un enfant `TextWidget(card=False)` pour placer un texte explicatif sous le titre. |
| `collapsible` | Permet aux utilisateurs de déplier et de replier le panneau. |
| `collapsed` | Affiche le panneau replié au départ. Ne s'applique que lorsque `collapsible=True`. |

Pour un groupe qui n'a pas besoin de titre, utilisez plutôt `ColumnWidget`. Il empile ses enfants verticalement sans les envelopper dans une carte stylisée.

### Fieldsets

`FieldsetWidget` regroupe les champs de manière très similaire à `PanelWidget`, mais affiche un `<fieldset>` et une `<legend>` HTML natifs plutôt qu'une carte stylisée. Utilisez-le lorsque vous souhaitez un regroupement plus simple, avec bordures.

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

L'attribut `legend` définit la légende dans l'élément `<legend>`. `disabled=True` ajoute l'attribut HTML `disabled` au conteneur, ce qui désactive chaque contrôle de formulaire imbriqué. `FieldsetWidget` prend en charge la même notation abrégée pour `children` que `PanelWidget`, mais pas les options spécifiques aux panneaux telles que `collapsible` et `icon`.

## Largeurs de colonnes explicites

La notation abrégée par tuples divise toujours une ligne en parts égales. Pour un contrôle plus fin des largeurs de colonnes, construisez la ligne explicitement avec `RowWidget`, `Col` et `FieldRef` :

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

Construire un `FieldRef` explicitement vous donne accès au paramètre `show_label`, qui supprime l'élément `<label>` lorsque la mise en page environnante rend déjà évident le rôle du champ.

```python
from starlette_admin import FieldsetWidget, FieldRef

form_layout = [
    FieldsetWidget(legend="Email", children=[FieldRef("email", show_label=False)]),
]
```

`show_label` vaut `True` par défaut. Les notations abrégées par chaînes et tuples affichent toujours les libellés, car elles n'acceptent aucun argument nommé.

## Groupes de saisie

Les paramètres `prepend` et `append` attachent un addon de [groupe de saisie](https://docs.tabler.io/ui/forms/form-elements#input-group) de part et d'autre d'un champ de saisie. Chacun accepte du texte brut ou du HTML brut, comme une icône Font Awesome.

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
    Les valeurs des addons sont affichées sans échappement afin que du HTML tel que le balisage d'icônes fonctionne. Ne transmettez que du contenu fiable que vous avez écrit vous-même, jamais une saisie utilisateur.

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

Comme `form_layout` partage la hiérarchie `BaseWidget` avec les tableaux de bord, vous pouvez hériter de `BaseWidget` pour créer vos propres éléments. C'est la solution de secours pour tout ce que les champs intégrés ne couvrent pas, comme des aperçus en lecture seule, des graphiques intégrés ou des macros personnalisées.

Consultez [Vues personnalisées & Widgets](../user-guide/custom-views.md) pour le schéma général, et la [référence de l'API Widgets](../api/widgets.md) pour les méthodes qu'une classe fille peut redéfinir. Les widgets personnalisés dans `form_layout` sont toujours affichés, quelles que soient les règles de visibilité des champs.

## Contrôle d'accès et visibilité

`form_layout` respecte vos règles d'accès au niveau des champs. Chaque `FieldRef` passe par la vérification habituelle `can_access_field`, et `exclude_from_create`, `exclude_from_edit` ainsi que les permissions basées sur les rôles restent toutes en vigueur.

* **Expansion des lignes :** lorsqu'un champ d'une ligne multi-colonnes est masqué pour une requête, les champs visibles restants s'étendent pour remplir l'espace.
* **Conteneurs vides :** lorsque tous les champs d'un conteneur (ligne, panneau, fieldset, colonne, grille ou onglet) sont masqués, le conteneur est omis, de sorte que vous n'obtenez jamais une coquille vide.
* **Affichage statique :** les composants statiques tels que `HtmlWidget`, `TextWidget` et les classes filles personnalisées de `BaseWidget` sont toujours affichés, car ils ne dépendent pas des champs du formulaire.

## Gestion des champs omis

Un champ déclaré dans `fields` mais absent de `form_layout` est ajouté en bas du formulaire, dans l'ordre de déclaration, afin qu'aucun champ ne soit jamais perdu silencieusement.

Référencer deux fois le même champ, ou référencer un nom qui ne figure pas dans `fields`, lève une exception `ValueError` lors de la construction de la vue.

---

## Et ensuite ?

* **[Vues personnalisées & Widgets](../user-guide/custom-views.md) :** la hiérarchie de widgets sur laquelle repose `form_layout`, et comment écrire votre propre widget.
* **[Templates](templates.md) :** redéfinissez `_form_group.html` pour modifier le balisage qu'affiche un groupe de mise en page.
* **[Champs](../user-guide/fields.md) :** les types de champs et les règles de visibilité qu'une mise en page organise.
