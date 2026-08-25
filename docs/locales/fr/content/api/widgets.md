---
title: Référence de l'API des widgets
description: Référence complète de l'API des widgets de tableau de bord et de mise
  en page de formulaires dans starlette-admin.
source_hash: da6469e2d30b13afb7827dac861073c091225333cce9307a41dc3c1ff24913e5
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

    [Lire la version originale en anglais](https://jowilf.github.io/starlette-admin/api/widgets/)
<!-- translation-notice:end -->

# Widgets

Référence complète des attributs et méthodes du système de widgets, générée à partir des docstrings. Pour une présentation orientée tâches, consultez [Custom Views & Widgets](../user-guide/custom-views.md) et
[Form Layouts](../advanced/form-layout.md).

Les widgets sont des blocs de construction composables et affichables, utilisés pour construire dynamiquement des éléments d'interface. Chaque classe de widget répertoriée ci-dessous peut être importée directement depuis `starlette_admin`.

Le système de widgets remplit deux rôles principaux selon le contexte :

* **Tableaux de bord & pages personnalisées :** utilisé comme attribut `widget` de [`CustomView`](views.md#starlette_admin.views.CustomView) pour créer des interfaces autonomes et des tableaux de métriques.
* **Mises en page de formulaires :** utilisé comme attribut `form_layout` de [`BaseModelView`](views.md#starlette_admin.views.BaseModelView) pour organiser et regrouper les champs sur les formulaires de création/édition.

---

## Classe de base

Tous les widgets héritent d'une classe de base commune qui définit l'interface standard d'affichage et de collecte d'assets.

::: starlette_admin.widgets.BaseWidget

---

## Widgets de contenu

Les widgets de contenu constituent les nœuds terminaux de votre arborescence d'interface. Au lieu de contenir d'autres widgets, ils affichent des données en direct. Chaque widget de contenu accepte un callback asynchrone invoqué une fois par requête, garantissant que les valeurs affichées sont toujours à jour.

::: starlette_admin.widgets.StatWidget
::: starlette_admin.widgets.ChartWidget
::: starlette_admin.widgets.TableWidget
::: starlette_admin.widgets.TextWidget
::: starlette_admin.widgets.HtmlWidget
::: starlette_admin.widgets.DividerWidget

---

## Widgets de mise en page

Les widgets de mise en page sont des conteneurs servant à agencer leurs `children` (qui peuvent être des widgets de contenu, des champs de formulaire ou d'autres widgets de mise en page).

**Gestion automatique des assets :** les widgets de mise en page parcourent récursivement leur arborescence afin de collecter les `additional_css_links` et `additional_js_links` de leurs enfants. Cela garantit que les composants profondément imbriqués chargent automatiquement les assets CSS/JS dont ils ont besoin, sans aucun câblage manuel.

::: starlette_admin.widgets.RowWidget
::: starlette_admin.widgets.CardRowWidget
::: starlette_admin.widgets.ColumnWidget
::: starlette_admin.widgets.GridWidget
::: starlette_admin.widgets.PanelWidget
::: starlette_admin.widgets.FieldsetWidget
::: starlette_admin.widgets.TabsWidget

---

## Dimensionnement adaptatif

Classes utilitaires dédiées à la gestion des comportements de grille adaptative, de la largeur des colonnes et des points de rupture selon les différentes tailles d'écran.

::: starlette_admin.widgets.Breakpoints
::: starlette_admin.widgets.Col

---

## Références aux champs de formulaire

Widgets spécialisés, utilisés exclusivement dans le contexte des formulaires de modèle, pour référencer des champs spécifiques de la base de données.

::: starlette_admin.widgets.FieldRef

---

## Raccourcis & normalisation

Afin de garder votre code de mise en page propre et très lisible, les widgets conteneurs acceptent des types Python simples à la place d'instanciations explicites de classes de widgets. Lors de l'initialisation (`__post_init__`), les conteneurs résolvent automatiquement ces valeurs raccourcies en leur équivalent sous forme de widget approprié.

**Raccourcis pris en charge :**

* `str` : résolu en une référence de champ (`FieldRef`).
* `tuple` : résolu en une ligne côte à côte (`RowWidget`).
* `list` : résolu en une pile verticale (`ColumnWidget`).

::: starlette_admin.widgets.WidgetShorthand
::: starlette_admin.widgets.normalize_widget

---

## Fonctions auxiliaires

Fonctions utilitaires permettant d'afficher des widgets dans des templates Jinja2 ou dans des contextes personnalisés.

::: starlette_admin.widgets.render_widget
